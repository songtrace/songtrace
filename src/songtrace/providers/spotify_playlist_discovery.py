"""Private-safe Spotify playlist discovery by search query."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from songtrace.providers.spotify_api_access import request_spotify_client_credentials_access_token
from songtrace.providers.spotify_environment import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    validate_spotify_environment,
)
from songtrace.providers.spotify_playlist_membership import (
    SpotifyPlaylistTrackMembership,
    request_spotify_playlist_track_pages,
)

SPOTIFY_SEARCH_URL_BASE = "https://api.spotify.com/v1/search"

TokenProvider = Callable[[str, str], str]
PlaylistSearchRequester = Callable[[str, str, int], Mapping[str, object]]
PlaylistTrackPagesRequester = Callable[[str, str], tuple[Mapping[str, object], ...]]


@dataclass(frozen=True, slots=True)
class SpotifyPlaylistSearchCandidate:
    """Safe Spotify playlist candidate returned by playlist search."""

    spotify_playlist_id: str
    playlist_name: str | None = None

    def __post_init__(self) -> None:
        if not self.spotify_playlist_id.strip():
            msg = "spotify_playlist_id_required"
            raise ValueError(msg)
        object.__setattr__(self, "spotify_playlist_id", self.spotify_playlist_id.strip())
        if self.playlist_name is not None:
            normalized_name = self.playlist_name.strip()
            object.__setattr__(self, "playlist_name", normalized_name or None)


@dataclass(frozen=True, slots=True)
class SpotifyPlaylistDiscoveryResult:
    """Safe result for Spotify playlist search plus verified track membership."""

    query: str
    spotify_track_id: str
    candidates: tuple[SpotifyPlaylistSearchCandidate, ...]
    memberships: tuple[SpotifyPlaylistTrackMembership, ...]

    def __post_init__(self) -> None:
        if not self.query.strip():
            msg = "spotify_playlist_search_query_required"
            raise ValueError(msg)
        if not self.spotify_track_id.strip():
            msg = "spotify_track_id_required"
            raise ValueError(msg)
        object.__setattr__(self, "query", self.query.strip())
        object.__setattr__(self, "spotify_track_id", self.spotify_track_id.strip())
        object.__setattr__(self, "candidates", tuple(self.candidates))
        object.__setattr__(self, "memberships", tuple(self.memberships))

    @property
    def verified_memberships(self) -> tuple[SpotifyPlaylistTrackMembership, ...]:
        """Positive playlist memberships in deterministic search-result order."""

        return tuple(membership for membership in self.memberships if membership.contains_track)


def discover_spotify_playlist_track_memberships(
    query: str,
    spotify_track_id: str,
    *,
    limit: int = 20,
    env: Mapping[str, str | None] | None = None,
    token_provider: TokenProvider | None = None,
    playlist_search_requester: PlaylistSearchRequester | None = None,
    playlist_track_pages_requester: PlaylistTrackPagesRequester | None = None,
) -> SpotifyPlaylistDiscoveryResult:
    """Search Spotify playlists by query and verify current track membership."""

    normalized_query = query.strip()
    normalized_track_id = spotify_track_id.strip()
    if not normalized_query:
        msg = "spotify_playlist_search_query_required"
        raise ValueError(msg)
    if not normalized_track_id:
        msg = "spotify_track_id_required"
        raise ValueError(msg)
    if limit < 1 or limit > 50:
        msg = "spotify_playlist_search_limit_out_of_range"
        raise ValueError(msg)

    values = os.environ if env is None else env
    environment = validate_spotify_environment(values)
    if not environment.is_configured:
        msg = "missing_credentials"
        raise ValueError(msg)

    requester = token_provider or request_spotify_client_credentials_access_token
    access_token = requester(
        _required_env_value(values, SPOTIFY_CLIENT_ID_ENV),
        _required_env_value(values, SPOTIFY_CLIENT_SECRET_ENV),
    )

    search_requester = playlist_search_requester or request_spotify_playlist_search
    search_payload = search_requester(access_token, normalized_query, limit)
    candidates = _playlist_search_candidates(search_payload)

    pages_requester = playlist_track_pages_requester or request_spotify_playlist_track_pages
    memberships = tuple(
        _verify_candidate_membership(
            candidate,
            normalized_track_id,
            pages_requester(access_token, candidate.spotify_playlist_id),
        )
        for candidate in candidates
    )

    return SpotifyPlaylistDiscoveryResult(
        query=normalized_query,
        spotify_track_id=normalized_track_id,
        candidates=candidates,
        memberships=memberships,
    )


def request_spotify_playlist_search(
    access_token: str,
    query: str,
    limit: int,
) -> Mapping[str, object]:
    """Request Spotify playlist search results in provider order."""

    if limit < 1 or limit > 50:
        msg = "spotify_playlist_search_limit_out_of_range"
        raise ValueError(msg)
    return _request_spotify_json_object(
        access_token,
        f"{SPOTIFY_SEARCH_URL_BASE}?q={quote(query, safe='')}&type=playlist&limit={limit}",
        "spotify_playlist_search",
    )


def _request_spotify_json_object(
    access_token: str,
    url: str,
    error_prefix: str,
) -> Mapping[str, object]:
    if not access_token.strip():
        msg = "spotify_access_token_required"
        raise ValueError(msg)

    request = Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )

    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        msg = f"{error_prefix}_http_error_{error.code}"
        raise ValueError(msg) from error
    except URLError as error:
        msg = f"{error_prefix}_network_error"
        raise ValueError(msg) from error
    except json.JSONDecodeError as error:
        msg = f"{error_prefix}_invalid_json"
        raise ValueError(msg) from error

    if not isinstance(payload, dict):
        msg = f"{error_prefix}_invalid_payload"
        raise ValueError(msg)
    return cast("Mapping[str, object]", payload)


def _playlist_search_candidates(
    payload: Mapping[str, object],
) -> tuple[SpotifyPlaylistSearchCandidate, ...]:
    playlists_value = payload.get("playlists")
    if not isinstance(playlists_value, dict):
        msg = "spotify_playlist_search_missing_playlists"
        raise ValueError(msg)
    playlists = cast("Mapping[str, object]", playlists_value)
    items_value = playlists.get("items")
    if not isinstance(items_value, list):
        msg = "spotify_playlist_search_missing_items"
        raise ValueError(msg)

    candidates: list[SpotifyPlaylistSearchCandidate] = []
    for item_value in cast("list[object]", items_value):
        if item_value is None:
            continue
        if not isinstance(item_value, dict):
            msg = "spotify_playlist_search_invalid_item"
            raise ValueError(msg)
        item = cast("Mapping[str, object]", item_value)
        candidates.append(
            SpotifyPlaylistSearchCandidate(
                spotify_playlist_id=_required_string(
                    item,
                    "id",
                    "spotify_playlist_search_item_missing_id",
                ),
                playlist_name=_optional_string(
                    item,
                    "name",
                    "spotify_playlist_search_item_invalid_name",
                ),
            )
        )
    return tuple(candidates)


def _verify_candidate_membership(
    candidate: SpotifyPlaylistSearchCandidate,
    spotify_track_id: str,
    pages: tuple[Mapping[str, object], ...],
) -> SpotifyPlaylistTrackMembership:
    matched_track_ids = _matched_track_ids(pages, spotify_track_id)
    return SpotifyPlaylistTrackMembership(
        spotify_playlist_id=candidate.spotify_playlist_id,
        playlist_name=candidate.playlist_name,
        spotify_track_id=spotify_track_id,
        contains_track=bool(matched_track_ids),
        matched_track_ids=matched_track_ids,
    )


def _matched_track_ids(
    pages: tuple[Mapping[str, object], ...],
    spotify_track_id: str,
) -> tuple[str, ...]:
    matches: list[str] = []
    for page in pages:
        items = page.get("items")
        if not isinstance(items, list):
            msg = "spotify_playlist_tracks_missing_items"
            raise ValueError(msg)
        for item_value in cast("list[object]", items):
            if not isinstance(item_value, dict):
                msg = "spotify_playlist_tracks_invalid_item"
                raise ValueError(msg)
            item = cast("Mapping[str, object]", item_value)
            track_value = item.get("track")
            if track_value is None:
                continue
            if not isinstance(track_value, dict):
                msg = "spotify_playlist_tracks_invalid_track"
                raise ValueError(msg)
            track = cast("Mapping[str, object]", track_value)
            current_track_id = _required_string(
                track,
                "id",
                "spotify_playlist_track_missing_id",
            )
            if current_track_id == spotify_track_id:
                matches.append(current_track_id)
    return tuple(matches)


def _required_string(payload: Mapping[str, object], field_name: str, error_code: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(error_code)
    return value.strip()


def _optional_string(
    payload: Mapping[str, object],
    field_name: str,
    error_code: str,
) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(error_code)
    normalized = value.strip()
    return normalized or None


def _required_env_value(values: Mapping[str, str | None], variable_name: str) -> str:
    value = values.get(variable_name)
    if value is None or not value.strip():
        msg = "missing_credentials"
        raise ValueError(msg)
    return value.strip()

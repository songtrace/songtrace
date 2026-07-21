"""Tests for private-safe Spotify playlist search discovery."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from email.message import Message
from io import BytesIO
from urllib.error import HTTPError

import pytest

from songtrace.providers import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    SpotifyPlaylistDiscoveryResult,
    SpotifyPlaylistSearchCandidate,
    SpotifyPlaylistTrackMembership,
    discover_spotify_playlist_track_memberships,
)
from songtrace.providers.spotify_playlist_discovery import request_spotify_playlist_search


def test_discover_spotify_playlist_track_memberships_verifies_candidates_in_search_order() -> None:
    token_calls: list[tuple[str, str]] = []
    search_calls: list[tuple[str, str, int]] = []
    track_page_calls: list[tuple[str, str]] = []

    def token_provider(client_id: str, client_secret: str) -> str:
        token_calls.append((client_id, client_secret))
        return "SECRET_TOKEN"

    def search_requester(access_token: str, query: str, limit: int) -> dict[str, object]:
        search_calls.append((access_token, query, limit))
        return {
            "playlists": {
                "items": [
                    {"id": "playlist-one", "name": "Everything Is Fading Radio"},
                    {"id": "playlist-two", "name": "Dark Metal"},
                ]
            }
        }

    def track_pages_requester(access_token: str, playlist_id: str) -> tuple[dict[str, object], ...]:
        track_page_calls.append((access_token, playlist_id))
        if playlist_id == "playlist-one":
            return ({"items": [{"track": {"id": "target-track"}}], "next": None},)
        return ({"items": [{"track": {"id": "other-track"}}], "next": None},)

    result = discover_spotify_playlist_track_memberships(
        " Everything Is Fading ",
        " target-track ",
        limit=2,
        env={
            SPOTIFY_CLIENT_ID_ENV: " SECRET_CLIENT_ID ",
            SPOTIFY_CLIENT_SECRET_ENV: " SECRET_CLIENT_SECRET ",
        },
        token_provider=token_provider,
        playlist_search_requester=search_requester,
        playlist_track_pages_requester=track_pages_requester,
    )

    assert result == SpotifyPlaylistDiscoveryResult(
        query="Everything Is Fading",
        spotify_track_id="target-track",
        candidates=(
            SpotifyPlaylistSearchCandidate(
                spotify_playlist_id="playlist-one",
                playlist_name="Everything Is Fading Radio",
            ),
            SpotifyPlaylistSearchCandidate(
                spotify_playlist_id="playlist-two",
                playlist_name="Dark Metal",
            ),
        ),
        memberships=(
            SpotifyPlaylistTrackMembership(
                spotify_playlist_id="playlist-one",
                playlist_name="Everything Is Fading Radio",
                spotify_track_id="target-track",
                contains_track=True,
                matched_track_ids=("target-track",),
            ),
            SpotifyPlaylistTrackMembership(
                spotify_playlist_id="playlist-two",
                playlist_name="Dark Metal",
                spotify_track_id="target-track",
                contains_track=False,
                matched_track_ids=(),
            ),
        ),
    )
    assert result.verified_memberships == (result.memberships[0],)
    assert token_calls == [("SECRET_CLIENT_ID", "SECRET_CLIENT_SECRET")]
    assert search_calls == [("SECRET_TOKEN", "Everything Is Fading", 2)]
    assert track_page_calls == [("SECRET_TOKEN", "playlist-one"), ("SECRET_TOKEN", "playlist-two")]
    assert "SECRET" not in str(result)


def test_discover_spotify_playlist_track_memberships_no_candidates() -> None:
    result = discover_spotify_playlist_track_memberships(
        "Everything Is Fading",
        "target-track",
        env={
            SPOTIFY_CLIENT_ID_ENV: "client-id",
            SPOTIFY_CLIENT_SECRET_ENV: "client-secret",
        },
        token_provider=lambda _client_id, _client_secret: "token",
        playlist_search_requester=lambda _access_token, _query, _limit: {
            "playlists": {"items": []}
        },
        playlist_track_pages_requester=lambda _access_token, _playlist_id: pytest.fail(
            "track pages should not be requested without candidates"
        ),
    )

    assert result.candidates == ()
    assert result.memberships == ()
    assert result.verified_memberships == ()


def test_spotify_playlist_discovery_models_are_immutable() -> None:
    candidate = SpotifyPlaylistSearchCandidate("playlist-id", "Playlist")
    result = SpotifyPlaylistDiscoveryResult(
        query="query",
        spotify_track_id="track-id",
        candidates=(candidate,),
        memberships=(),
    )

    with pytest.raises(FrozenInstanceError):
        candidate.spotify_playlist_id = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.query = "other"  # type: ignore[misc]


def test_discover_spotify_playlist_track_memberships_rejects_invalid_inputs() -> None:
    env = {
        SPOTIFY_CLIENT_ID_ENV: "client-id",
        SPOTIFY_CLIENT_SECRET_ENV: "client-secret",
    }

    with pytest.raises(ValueError, match="spotify_playlist_search_query_required"):
        discover_spotify_playlist_track_memberships(" ", "track-id", env=env)
    with pytest.raises(ValueError, match="spotify_track_id_required"):
        discover_spotify_playlist_track_memberships("query", " ", env=env)
    with pytest.raises(ValueError, match="spotify_playlist_search_limit_out_of_range"):
        discover_spotify_playlist_track_memberships("query", "track-id", limit=0, env=env)
    with pytest.raises(ValueError, match="spotify_playlist_search_limit_out_of_range"):
        discover_spotify_playlist_track_memberships("query", "track-id", limit=51, env=env)


def test_discover_spotify_playlist_track_memberships_rejects_missing_credentials() -> None:
    with pytest.raises(ValueError, match="missing_credentials"):
        discover_spotify_playlist_track_memberships("query", "track-id", env={})


def test_discover_spotify_playlist_track_memberships_rejects_invalid_search_payload() -> None:
    env = {
        SPOTIFY_CLIENT_ID_ENV: "client-id",
        SPOTIFY_CLIENT_SECRET_ENV: "client-secret",
    }

    with pytest.raises(ValueError, match="spotify_playlist_search_missing_playlists"):
        discover_spotify_playlist_track_memberships(
            "query",
            "track-id",
            env=env,
            token_provider=lambda _client_id, _client_secret: "token",
            playlist_search_requester=lambda _access_token, _query, _limit: {},
        )

    with pytest.raises(ValueError, match="spotify_playlist_search_item_missing_id"):
        discover_spotify_playlist_track_memberships(
            "query",
            "track-id",
            env=env,
            token_provider=lambda _client_id, _client_secret: "token",
            playlist_search_requester=lambda _access_token, _query, _limit: {
                "playlists": {"items": [{"name": "Missing ID"}]}
            },
        )


def test_request_spotify_playlist_search_parses_successful_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_urls: list[str] = []

    def respond(request: object, timeout: int) -> _Response:
        requested_urls.append(request.full_url)  # type: ignore[attr-defined]
        assert timeout == 10
        return _Response(b'{"playlists":{"items":[{"id":"playlist-id"}]}}')

    monkeypatch.setattr("songtrace.providers.spotify_playlist_discovery.urlopen", respond)

    payload = request_spotify_playlist_search("SECRET_TOKEN", "Everything Is Fading", 10)

    assert payload == {"playlists": {"items": [{"id": "playlist-id"}]}}
    assert requested_urls == [
        "https://api.spotify.com/v1/search?q=Everything%20Is%20Fading&type=playlist&limit=10"
    ]


def test_request_spotify_playlist_search_rejects_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_request: object, timeout: int) -> object:
        raise HTTPError(
            url="https://api.spotify.com/v1/search",
            code=429,
            msg="Too Many Requests",
            hdrs=Message(),
            fp=None,
        )

    monkeypatch.setattr("songtrace.providers.spotify_playlist_discovery.urlopen", fail)

    with pytest.raises(ValueError, match="spotify_playlist_search_http_error_429"):
        request_spotify_playlist_search("SECRET_TOKEN", "Everything Is Fading", 10)


class _Response:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return BytesIO(self._body).read()

"""Tests for private-safe Spotify playlist membership lookup."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from email.message import Message
from io import BytesIO
from urllib.error import HTTPError

import pytest

from songtrace.providers import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    SpotifyPlaylistTrackMembership,
    lookup_spotify_playlist_track_membership,
)
from songtrace.providers.spotify_playlist_membership import (
    request_spotify_playlist_payload,
    request_spotify_playlist_track_pages,
)


def test_lookup_spotify_playlist_track_membership_found() -> None:
    token_calls: list[tuple[str, str]] = []
    playlist_calls: list[tuple[str, str]] = []
    track_page_calls: list[tuple[str, str]] = []

    def token_provider(client_id: str, client_secret: str) -> str:
        token_calls.append((client_id, client_secret))
        return "SECRET_TOKEN"

    def playlist_requester(access_token: str, playlist_id: str) -> dict[str, object]:
        playlist_calls.append((access_token, playlist_id))
        return {"id": "playlist-id", "name": "Metal Essentials"}

    def track_pages_requester(access_token: str, playlist_id: str) -> tuple[dict[str, object], ...]:
        track_page_calls.append((access_token, playlist_id))
        return (
            {"items": [{"track": {"id": "other-track-id"}}], "next": None},
            {"items": [{"track": {"id": "spotify-track-id"}}], "next": None},
        )

    membership = lookup_spotify_playlist_track_membership(
        " playlist-id ",
        " spotify-track-id ",
        {
            SPOTIFY_CLIENT_ID_ENV: " SECRET_CLIENT_ID ",
            SPOTIFY_CLIENT_SECRET_ENV: " SECRET_CLIENT_SECRET ",
        },
        token_provider=token_provider,
        playlist_payload_requester=playlist_requester,
        playlist_track_pages_requester=track_pages_requester,
    )

    assert membership == SpotifyPlaylistTrackMembership(
        spotify_playlist_id="playlist-id",
        playlist_name="Metal Essentials",
        spotify_track_id="spotify-track-id",
        contains_track=True,
        matched_track_ids=("spotify-track-id",),
    )
    assert token_calls == [("SECRET_CLIENT_ID", "SECRET_CLIENT_SECRET")]
    assert playlist_calls == [("SECRET_TOKEN", "playlist-id")]
    assert track_page_calls == [("SECRET_TOKEN", "playlist-id")]
    assert "SECRET" not in str(membership)


def test_lookup_spotify_playlist_track_membership_not_found() -> None:
    membership = lookup_spotify_playlist_track_membership(
        "playlist-id",
        "spotify-track-id",
        {
            SPOTIFY_CLIENT_ID_ENV: "client-id",
            SPOTIFY_CLIENT_SECRET_ENV: "client-secret",
        },
        token_provider=lambda _client_id, _client_secret: "token",
        playlist_payload_requester=lambda _access_token, _playlist_id: {
            "id": "playlist-id",
            "name": "Metal Essentials",
        },
        playlist_track_pages_requester=lambda _access_token, _playlist_id: (
            {"items": [{"track": {"id": "other-track-id"}}], "next": None},
        ),
    )

    assert membership.contains_track is False
    assert membership.matched_track_ids == ()


def test_spotify_playlist_track_membership_is_immutable() -> None:
    membership = SpotifyPlaylistTrackMembership(
        spotify_playlist_id="playlist-id",
        playlist_name="Metal Essentials",
        spotify_track_id="spotify-track-id",
        contains_track=True,
        matched_track_ids=("spotify-track-id",),
    )

    with pytest.raises(FrozenInstanceError):
        membership.contains_track = False  # type: ignore[misc]


def test_lookup_spotify_playlist_track_membership_rejects_blank_ids() -> None:
    with pytest.raises(ValueError, match="spotify_playlist_id_required"):
        lookup_spotify_playlist_track_membership(
            " ",
            "spotify-track-id",
            {
                SPOTIFY_CLIENT_ID_ENV: "client-id",
                SPOTIFY_CLIENT_SECRET_ENV: "client-secret",
            },
        )

    with pytest.raises(ValueError, match="spotify_track_id_required"):
        lookup_spotify_playlist_track_membership(
            "playlist-id",
            " ",
            {
                SPOTIFY_CLIENT_ID_ENV: "client-id",
                SPOTIFY_CLIENT_SECRET_ENV: "client-secret",
            },
        )


def test_lookup_spotify_playlist_track_membership_rejects_missing_credentials() -> None:
    with pytest.raises(ValueError, match="missing_credentials"):
        lookup_spotify_playlist_track_membership(
            "playlist-id",
            "spotify-track-id",
            {},
        )


def test_lookup_spotify_playlist_track_membership_rejects_missing_required_fields() -> None:
    with pytest.raises(ValueError, match="spotify_playlist_missing_id"):
        lookup_spotify_playlist_track_membership(
            "playlist-id",
            "spotify-track-id",
            {
                SPOTIFY_CLIENT_ID_ENV: "client-id",
                SPOTIFY_CLIENT_SECRET_ENV: "client-secret",
            },
            token_provider=lambda _client_id, _client_secret: "token",
            playlist_payload_requester=lambda _access_token, _playlist_id: {
                "name": "Metal Essentials"
            },
            playlist_track_pages_requester=lambda _access_token, _playlist_id: (
                {"items": [], "next": None},
            ),
        )

    with pytest.raises(ValueError, match="spotify_playlist_tracks_missing_items"):
        lookup_spotify_playlist_track_membership(
            "playlist-id",
            "spotify-track-id",
            {
                SPOTIFY_CLIENT_ID_ENV: "client-id",
                SPOTIFY_CLIENT_SECRET_ENV: "client-secret",
            },
            token_provider=lambda _client_id, _client_secret: "token",
            playlist_payload_requester=lambda _access_token, _playlist_id: {"id": "playlist-id"},
            playlist_track_pages_requester=lambda _access_token, _playlist_id: ({"next": None},),
        )


def test_request_spotify_playlist_payload_parses_successful_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def respond(_request: object, timeout: int) -> _Response:
        return _Response(b'{"id":"playlist-id","name":"Metal Essentials"}')

    monkeypatch.setattr("songtrace.providers.spotify_playlist_membership.urlopen", respond)

    payload = request_spotify_playlist_payload("SECRET_TOKEN", "playlist-id")

    assert payload["id"] == "playlist-id"


def test_request_spotify_playlist_payload_rejects_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_request: object, timeout: int) -> object:
        raise HTTPError(
            url="https://api.spotify.com/v1/playlists/playlist-id",
            code=404,
            msg="Not Found",
            hdrs=Message(),
            fp=None,
        )

    monkeypatch.setattr("songtrace.providers.spotify_playlist_membership.urlopen", fail)

    with pytest.raises(ValueError, match="spotify_playlist_http_error_404"):
        request_spotify_playlist_payload("SECRET_TOKEN", "playlist-id")


def test_request_spotify_playlist_payload_rejects_invalid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def respond(_request: object, timeout: int) -> _Response:
        return _Response(b"not-json")

    monkeypatch.setattr("songtrace.providers.spotify_playlist_membership.urlopen", respond)

    with pytest.raises(ValueError, match="spotify_playlist_invalid_json"):
        request_spotify_playlist_payload("SECRET_TOKEN", "playlist-id")


def test_request_spotify_playlist_track_pages_preserves_page_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = [
        _Response(b'{"items":[{"track":{"id":"first"}}],"next":"https://next"}'),
        _Response(b'{"items":[{"track":{"id":"second"}}],"next":null}'),
    ]

    def respond(_request: object, timeout: int) -> _Response:
        return responses.pop(0)

    monkeypatch.setattr("songtrace.providers.spotify_playlist_membership.urlopen", respond)

    pages = request_spotify_playlist_track_pages("SECRET_TOKEN", "playlist-id")

    assert [page["items"] for page in pages] == [
        [{"track": {"id": "first"}}],
        [{"track": {"id": "second"}}],
    ]


class _Response:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return BytesIO(self._body).read()

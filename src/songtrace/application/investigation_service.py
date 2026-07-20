from songtrace.domain import Investigation, TrackIdentity


class InvestigationService:
    """Coordinates SongTrace investigations."""

    def begin(
        self,
        *,
        artist: str,
        track: str,
    ) -> Investigation:
        """Begin a new investigation for a musical track."""
        identity = TrackIdentity(
            artist=artist,
            title=track,
        )

        return Investigation(track=identity)

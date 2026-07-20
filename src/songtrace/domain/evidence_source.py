"""Domain value object representing the origin of evidence."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvidenceSource:
    """A validated, provider-neutral identifier for an evidence source."""

    name: str

    def __post_init__(self) -> None:
        """Validate and normalize the source identifier."""

        normalized_name = self.name.strip().lower().replace(" ", "_")

        if not normalized_name:
            raise ValueError("Evidence source name must not be empty.")

        object.__setattr__(self, "name", normalized_name)

    def __str__(self) -> str:
        """Return the normalized source identifier."""

        return self.name

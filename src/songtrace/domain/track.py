from pydantic import BaseModel, ConfigDict, Field


class TrackIdentity(BaseModel):
    """The provider-neutral identifying information for a musical track."""

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    artist: str = Field(min_length=1)
    title: str = Field(min_length=1)
    isrc: str | None = Field(default=None, min_length=1)

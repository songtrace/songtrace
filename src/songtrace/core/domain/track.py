from pydantic import BaseModel, ConfigDict, Field


class TrackIdentity(BaseModel):
    """The identifying information for a musical track."""

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    artist: str = Field(min_length=1)
    title: str = Field(min_length=1)

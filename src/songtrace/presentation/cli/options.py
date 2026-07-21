from datetime import datetime
from typing import Literal
from uuid import UUID

import typer


def parse_optional_batch_id(value: str | None) -> UUID | None:
    if value is None:
        return None

    try:
        return UUID(value)
    except ValueError as error:
        raise typer.BadParameter(
            "batch ID must be a valid UUID",
            param_hint="--batch-id",
        ) from error


def parse_optional_imported_at(value: str | None) -> datetime | None:
    if value is None:
        return None

    return parse_timezone_aware_datetime(
        value,
        field_name="imported_at",
        param_hint="--imported-at",
    )


def parse_timezone_aware_datetime(value: str, *, field_name: str, param_hint: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise typer.BadParameter(
            f"{field_name} must be an ISO datetime",
            param_hint=param_hint,
        ) from error

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise typer.BadParameter(
            f"{field_name} must be timezone-aware",
            param_hint=param_hint,
        )

    return parsed


def parse_output_format(output: str) -> Literal["text", "json"]:
    output_format = output.lower()
    if output_format == "text":
        return "text"
    if output_format == "json":
        return "json"

    raise typer.BadParameter(
        "unsupported output format; expected text or json",
        param_hint="--output",
    )

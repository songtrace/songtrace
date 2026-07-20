"""Run SongTrace's first deterministic investigation."""

from dataclasses import dataclass
from datetime import UTC, datetime

from songtrace.application.evidence_importer import EvidenceImporter
from songtrace.application.observation_extractor import ObservationExtractor
from songtrace.application.raw_evidence_record import RawEvidenceRecord
from songtrace.application.raw_evidence_source import RawEvidenceSource
from songtrace.application.simple_investigator import SimpleInvestigator
from songtrace.domain.evidence import EvidenceKind, EvidenceSignal


@dataclass(frozen=True, slots=True)
class ExampleRawEvidenceSource:
    """Small example source that supplies raw evidence records."""

    observed_at: datetime

    def load(self) -> tuple[RawEvidenceRecord, ...]:
        """Load example evidence records in deterministic order."""

        return (
            RawEvidenceRecord(
                source_name="spotify",
                kind=EvidenceKind.PLAYLIST_ACTIVITY,
                summary="Everything Is Fading received editorial playlist placement.",
                observed_at=self.observed_at,
                reference="spotify-playlist:dark-metal-editorial",
                signals=(EvidenceSignal.PLAYLIST_PLACEMENT,),
            ),
            RawEvidenceRecord(
                source_name="spotify",
                kind=EvidenceKind.AUDIENCE_ACTIVITY,
                summary="Streams increased 48% after the playlist placement.",
                observed_at=self.observed_at,
                reference="spotify-analytics:streams-week-2026-07-18",
                signals=(EvidenceSignal.STREAM_GROWTH,),
            ),
            RawEvidenceRecord(
                source_name="spotify",
                kind=EvidenceKind.AUDIENCE_ACTIVITY,
                summary="Save activity increased 31% after the playlist placement.",
                observed_at=self.observed_at,
                reference="spotify-analytics:saves-week-2026-07-18",
                signals=(EvidenceSignal.SAVE_GROWTH,),
            ),
        )


def main() -> None:
    observed_at = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)
    source: RawEvidenceSource = ExampleRawEvidenceSource(observed_at=observed_at)
    evidence = EvidenceImporter().import_records(source.load())

    observations = ObservationExtractor(clock=lambda: observed_at).extract(evidence)
    result = SimpleInvestigator().investigate(observations)

    print("=" * 42)
    print("       SONGTRACE INVESTIGATION")
    print("=" * 42)

    print("\nEVIDENCE\n")

    for item in evidence:
        print(f"• {item.summary}")
        print(f"  ID: {item.id}")
        print(f"  Kind: {item.kind.value}")
        print(f"  Source: {item.source}")
        if item.signals:
            print(f"  Signals: {', '.join(signal.value for signal in item.signals)}")
        if item.reference is not None:
            print(f"  Reference: {item.reference}")

    print("\nOBSERVATIONS\n")

    for observation in result.observations:
        print(f"• {observation.summary}")
        print(f"  Kind: {observation.kind.value}")
        print("  Supporting evidence:")
        for evidence_id in observation.supporting_evidence_ids:
            print(f"  - {evidence_id}")

    print("\nCONCLUSIONS\n")

    if not result.conclusions:
        print("No supported conclusion was found.")
        return

    for conclusion in result.conclusions:
        print(conclusion.statement)
        print(f"\nConfidence: {conclusion.confidence.level.value.upper()}")
        print(f"Reason: {conclusion.confidence.rationale}")
        print(f"Supporting observations: {len(conclusion.supporting_observation_ids)}")


if __name__ == "__main__":
    main()

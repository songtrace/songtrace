"""Tests for the deterministic investigation rule catalog."""

from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from songtrace.application.rule_catalog import RuleCatalog
from songtrace.domain.confidence import Confidence, ConfidenceLevel
from songtrace.domain.investigation_rule import InvestigationRule
from songtrace.domain.observation import ObservationKind


def test_returns_rules_as_immutable_tuple() -> None:
    catalog = RuleCatalog()

    assert isinstance(catalog.rules, tuple)


def test_supplied_rules_are_exposed_as_immutable_tuple() -> None:
    rule = InvestigationRule(
        required_observation_kinds=(ObservationKind.PLAYLIST_STREAM_GROWTH,),
        conclusion_statement="Stream growth is present.",
        confidence=Confidence(
            level=ConfidenceLevel.MEDIUM,
            rationale="A stream-growth observation is present.",
        ),
    )
    rules = [rule]

    catalog = RuleCatalog(rules=cast(tuple[InvestigationRule, ...], rules))
    rules.clear()

    assert catalog.rules == (rule,)


def test_rule_catalog_is_immutable() -> None:
    catalog = RuleCatalog()

    with pytest.raises(FrozenInstanceError):
        catalog.rules = ()  # type: ignore[misc]


def test_contains_existing_default_playlist_engagement_rule() -> None:
    catalog = RuleCatalog()

    assert len(catalog.rules) == 1

    rule = catalog.rules[0]

    assert isinstance(rule, InvestigationRule)
    assert rule.required_observation_kinds == (
        ObservationKind.PLAYLIST_STREAM_GROWTH,
        ObservationKind.PLAYLIST_SAVE_GROWTH,
    )
    assert (
        rule.conclusion_statement
        == "Editorial playlist placement likely drove renewed listener engagement."
    )
    assert rule.confidence.level is ConfidenceLevel.HIGH
    assert rule.confidence.rationale == (
        "Stream and save activity both increased after the playlist placement."
    )

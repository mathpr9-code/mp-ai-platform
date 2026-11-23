"""Roda todos os casos da suíte de erros. Um arquivo YAML = um teste.

Registrar um bug novo é criar um arquivo em `cases/`, não escrever código de teste.
Nada é publicado sem esta suíte inteira passar.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mp_agent import ConversationState, Interpretation, OpenQuestion, Turn, decide
from mp_agent.contracts import Correction, Evidence, FieldValue

CASES_DIR = Path(__file__).parent / "cases"


def load_cases() -> list[dict]:
    return [
        yaml.safe_load(p.read_text(encoding="utf-8"))
        for p in sorted(CASES_DIR.glob("*.yaml"))
    ]


def build(case: dict):
    conversation = [Turn(**t) for t in case["conversation"]]

    before = case.get("state_before", {}) or {}
    oq = before.get("open_question")
    state = ConversationState(
        fields=dict(before.get("fields", {})),
        required_fields=list(before.get("required_fields", [])),
        open_question=OpenQuestion(**oq) if oq else None,
        clarify_attempts=before.get("clarify_attempts", 0),
    )

    raw = case["interpretation"]
    interp = Interpretation(
        evidence=[Evidence(**e) for e in raw.get("evidence", [])],
        acts=raw.get("acts", []),
        answers_to=raw.get("answers_to"),
        intent=raw.get("intent"),
        fields=[FieldValue(**f) for f in raw.get("fields", [])],
        corrections=[Correction(**c) for c in raw.get("corrections", [])],
        ambiguities=raw.get("ambiguities", []),
    )
    return conversation, state, interp


@pytest.mark.parametrize("case", load_cases(), ids=lambda c: c["id"])
def test_error_case(case: dict) -> None:
    conversation, state, interp = build(case)
    decision = decide(interp, state, conversation)
    expected = case["expected"]

    assert decision.conduct == expected["conduct"], (
        f"{case['id']} ({case['title']}): veio {decision.conduct!r} "
        f"porque {decision.reason!r}; esperado {expected['conduct']!r}"
    )
    if "effect" in expected:
        assert decision.effect == expected["effect"], f"{case['id']}: efeito errado"
    for name, value in (expected.get("fields") or {}).items():
        assert state.fields.get(name) == value, f"{case['id']}: campo {name!r}"
    for forbidden in expected.get("must_not_conduct", []):
        assert decision.conduct != forbidden, f"{case['id']}: conduta proibida {forbidden!r}"

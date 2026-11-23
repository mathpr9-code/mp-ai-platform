"""The decision layer: a pure function, no LLM.

The extractor reads; this code decides. Because `decide()` is deterministic,
every decision case in the error suite runs without calling a model, in
milliseconds, on every change.

Order of authority (highest first):
    1. deterministic evidence  2. state  3. LLM interpretation with literal
    evidence  4. abstain (clarify)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .contracts import (
    ConversationState,
    Decision,
    Interpretation,
    Turn,
)

# What an effect recorded on an OpenQuestion turns into.
EFFECT_TO_CONDUCT = {
    "await_new_request": "ask_what_else",
    "transfer_to_human": "transfer",
    "close_conversation": "close",
    "ask_what_to_change": "clarify",
}

SHORT_REPLY_ACTS = {"confirmation", "denial"}


@dataclass
class Policy:
    """Client-specific rules. They live in code/config, never in the extractor prompt."""

    actions_requiring_confirmation: set[str] = field(default_factory=lambda: {"cancel"})
    max_clarify_attempts: int = 2


def validate_evidence(interp: Interpretation, conversation: list[Turn]) -> str | None:
    """Every quote must exist literally in the turn it cites. Returns an error or None."""
    turns = {t.id: t.text.lower() for t in conversation}
    ids = set()
    for ev in interp.evidence:
        ids.add(ev.id)
        if ev.turn not in turns or ev.quote.lower() not in turns[ev.turn]:
            return f"EVIDENCE_FAB: quote {ev.quote!r} not found in turn {ev.turn}"
    for item in [*interp.fields, *interp.corrections]:
        if item.evidence not in ids:
            return f"EVIDENCE_FAB: {item} points to unknown evidence {item.evidence!r}"
    return None


def apply_events(state: ConversationState, interp: Interpretation) -> None:
    """Apply extracted facts to state as events, never by overwriting history."""
    for f in interp.fields:
        state.events.append({"type": "field_set", "field": f.name, "value": f.value})
        state.fields[f.name] = f.value
    for c in interp.corrections:
        state.events.append(
            {"type": "field_corrected", "field": c.field, "from": c.old, "to": c.new}
        )
        state.fields[c.field] = c.new


def _from_effect(effect: str | None, reason: str) -> Decision:
    if effect and effect.startswith("execute:"):
        return Decision("execute", reason, effect)
    return Decision(EFFECT_TO_CONDUCT.get(effect or "", "answer"), reason, effect)


def decide(
    interp: Interpretation,
    state: ConversationState,
    conversation: list[Turn],
    policy: Policy | None = None,
) -> Decision:
    policy = policy or Policy()

    # 1. Never trust an interpretation that cannot point to the conversation.
    error = validate_evidence(interp, conversation)
    if error:
        return Decision("clarify", error)

    # 2. Clarification limit reached: stop asking, hand off.
    if state.clarify_attempts >= policy.max_clarify_attempts:
        return Decision("transfer", "clarification limit reached")

    # 3. Explicit request for a human, anchored in a literal quote.
    if "asks_for_human" in interp.acts and interp.evidence:
        return Decision("transfer", "customer explicitly asked for a human")

    q = state.open_question

    # 4. A reply is read as a PAIR: agent's question + customer's answer.
    if interp.answers_to is not None:
        if q is None or q.id != interp.answers_to:
            return Decision("clarify", "reply points to a question that is not open")
        if "confirmation" in interp.acts:
            return _from_effect(q.on_yes, f"confirmed open question {q.id} ({q.about})")
        if "denial" in interp.acts:
            return _from_effect(q.on_no, f"denied open question {q.id} ({q.about})")

    # 5. A short reply with no open question never triggers an action.
    if set(interp.acts) and set(interp.acts) <= SHORT_REPLY_ACTS and q is None:
        return Decision("none", "short reply without an open question: receipt only")

    # 6. Actions with consequences are confirmed before the tool is called.
    for act in interp.acts:
        if act in policy.actions_requiring_confirmation:
            return Decision("confirm", f"'{act}' requires explicit confirmation first")

    # 7. Apply facts, then check what is still missing.
    apply_events(state, interp)
    missing = [f for f in state.required_fields if f not in state.fields]
    if interp.ambiguities:
        return Decision("clarify", f"ambiguity: {interp.ambiguities[0]}")
    if missing:
        return Decision("clarify", f"missing required field: {missing[0]}")

    return Decision("answer", "enough evidence and data to answer")

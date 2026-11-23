"""Fixed contracts between the stages of a turn.

The framework's core rule: what each stage receives and returns never changes
from client to client. The pieces that fulfil a contract (which model, which
retrieval strategy, which orchestrator) can be swapped; the shapes below cannot.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Author = Literal["customer", "agent"]

# Closed vocabulary of communicative acts the extractor may return.
# Anything else is "out of list", never a new invented act.
Act = Literal[
    "inform",
    "question",
    "request",
    "confirmation",
    "denial",
    "correction",
    "cancel",
    "asks_for_human",
    "thanks",
    "goodbye",
]


@dataclass
class Turn:
    id: str
    author: Author
    text: str


@dataclass
class OpenQuestion:
    """Written by CODE every time the agent asks something.

    It records what the question opened, so a short reply ("yes", "the second
    one") can later be resolved against it instead of being read in isolation.
    """

    id: str
    kind: Literal["yes_no", "choice", "field"]
    about: str
    on_yes: str | None = None
    on_no: str | None = None
    options: list[str] = field(default_factory=list)


@dataclass
class Evidence:
    id: str
    turn: str
    quote: str  # must exist literally in the quoted turn


@dataclass
class FieldValue:
    name: str
    value: str
    evidence: str  # id of an Evidence item


@dataclass
class Correction:
    field: str
    old: str | None
    new: str
    evidence: str


@dataclass
class Interpretation:
    """Output of the 1. Interpret stage (extractor, level N2).

    Maximum intelligence to read, zero authority to decide: there is no
    "next step" or "transfer" field here on purpose.
    """

    evidence: list[Evidence] = field(default_factory=list)
    acts: list[Act] = field(default_factory=list)
    answers_to: str | None = None  # id of the OpenQuestion this message replies to
    intent: str | None = None
    fields: list[FieldValue] = field(default_factory=list)
    corrections: list[Correction] = field(default_factory=list)
    ambiguities: list[str] = field(default_factory=list)
    out_of_list: bool = False


@dataclass
class ConversationState:
    fields: dict[str, str] = field(default_factory=dict)
    required_fields: list[str] = field(default_factory=list)
    open_question: OpenQuestion | None = None
    clarify_attempts: int = 0
    events: list[dict] = field(default_factory=list)  # append-only log, never overwritten


Conduct = Literal[
    "answer",          # reply / continue the flow
    "ask_what_else",   # customer wants to keep going
    "clarify",         # 4. Clarify: ask the minimum question
    "confirm",         # ESC4: confirm before an action with consequences
    "execute",         # 3. Resolve: run an approved action
    "transfer",        # 5. Transfer: hand off to a human
    "close",           # end the conversation
    "none",            # receipt only, nothing to do
]


@dataclass
class Decision:
    conduct: Conduct
    reason: str
    effect: str | None = None

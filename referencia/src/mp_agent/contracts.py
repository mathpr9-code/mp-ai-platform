"""Contratos fixos entre as etapas de um turno.

Regra central do framework: o que cada etapa recebe e entrega não muda de
cliente para cliente. As peças que cumprem um contrato (qual modelo, qual
estratégia de recuperação, qual orquestrador) podem ser trocadas; os formatos
abaixo, não.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Author = Literal["customer", "agent"]

# Vocabulário fechado de atos comunicativos que o extrator pode devolver.
# Qualquer outra coisa é "fora da lista", nunca um ato novo inventado.
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
    """Escrita pelo CÓDIGO toda vez que o agente pergunta algo.

    Registra o que a pergunta abriu, para que uma resposta curta ("sim", "o
    segundo") seja resolvida contra ela, e não lida isoladamente.
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
    quote: str  # precisa existir literalmente no turno citado


@dataclass
class FieldValue:
    name: str
    value: str
    evidence: str  # id de um item de Evidence


@dataclass
class Correction:
    field: str
    old: str | None
    new: str
    evidence: str


@dataclass
class Interpretation:
    """Saída da etapa 1. Interpretar (extrator, nível N2).

    Inteligência máxima para ler, zero autoridade para decidir: de propósito,
    não existe campo de "próximo passo" ou "transferir" aqui.
    """

    evidence: list[Evidence] = field(default_factory=list)
    acts: list[Act] = field(default_factory=list)
    answers_to: str | None = None  # id da OpenQuestion que esta mensagem responde
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
    events: list[dict] = field(default_factory=list)  # log só de acréscimo, nunca sobrescrito


Conduct = Literal[
    "answer",          # responder / seguir o fluxo
    "ask_what_else",   # cliente quer continuar
    "clarify",         # 4. Esclarecer: fazer a pergunta mínima
    "confirm",         # ESC4: confirmar antes de ação com consequência
    "execute",         # 3. Resolver: executar uma ação aprovada
    "transfer",        # 5. Transferir: passar para um humano
    "close",           # encerrar a conversa
    "none",            # só recebimento, nada a fazer
]


@dataclass
class Decision:
    conduct: Conduct
    reason: str
    effect: str | None = None

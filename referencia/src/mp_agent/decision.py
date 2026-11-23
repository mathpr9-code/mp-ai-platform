"""Camada de decisão: uma função pura, sem LLM.

O extrator lê; este código decide. Como `decide()` é determinística, todo caso
de decisão da suíte de erros roda sem chamar modelo, em milissegundos, a cada
mudança.

Ordem de autoridade (da maior para a menor):
    1. evidência determinística  2. estado  3. interpretação do LLM com
    evidência literal  4. abster-se (esclarecer)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .contracts import (
    ConversationState,
    Decision,
    Interpretation,
    Turn,
)

# Em que conduta vira cada efeito registrado numa OpenQuestion.
EFFECT_TO_CONDUCT = {
    "await_new_request": "ask_what_else",
    "transfer_to_human": "transfer",
    "close_conversation": "close",
    "ask_what_to_change": "clarify",
}

SHORT_REPLY_ACTS = {"confirmation", "denial"}


@dataclass
class Policy:
    """Regras do cliente. Moram em código/config, nunca no prompt do extrator."""

    actions_requiring_confirmation: set[str] = field(default_factory=lambda: {"cancel"})
    max_clarify_attempts: int = 2


def validate_evidence(interp: Interpretation, conversation: list[Turn]) -> str | None:
    """Toda citação precisa existir literalmente no turno citado. Devolve um erro ou None."""
    turns = {t.id: t.text.lower() for t in conversation}
    ids = set()
    for ev in interp.evidence:
        ids.add(ev.id)
        if ev.turn not in turns or ev.quote.lower() not in turns[ev.turn]:
            return f"EVIDENCE_FAB: citação {ev.quote!r} não encontrada no turno {ev.turn}"
    for item in [*interp.fields, *interp.corrections]:
        if item.evidence not in ids:
            return f"EVIDENCE_FAB: {item} aponta para evidência inexistente {item.evidence!r}"
    return None


def apply_events(state: ConversationState, interp: Interpretation) -> None:
    """Aplica os fatos extraídos ao estado como eventos, nunca sobrescrevendo o histórico."""
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

    # 1. Nunca confiar numa interpretação que não aponta para a conversa.
    error = validate_evidence(interp, conversation)
    if error:
        return Decision("clarify", error)

    # 2. Limite de esclarecimento atingido: parar de perguntar e transferir.
    if state.clarify_attempts >= policy.max_clarify_attempts:
        return Decision("transfer", "limite de esclarecimento atingido")

    # 3. Pedido explícito de humano, ancorado em citação literal.
    if "asks_for_human" in interp.acts and interp.evidence:
        return Decision("transfer", "cliente pediu explicitamente um humano")

    q = state.open_question

    # 4. Uma resposta é lida como PAR: pergunta do agente + resposta do cliente.
    if interp.answers_to is not None:
        if q is None or q.id != interp.answers_to:
            return Decision("clarify", "resposta aponta para uma pergunta que não está aberta")
        if "confirmation" in interp.acts:
            return _from_effect(q.on_yes, f"confirmou a pergunta aberta {q.id} ({q.about})")
        if "denial" in interp.acts:
            return _from_effect(q.on_no, f"negou a pergunta aberta {q.id} ({q.about})")

    # 5. Resposta curta sem pergunta aberta nunca dispara ação.
    if set(interp.acts) and set(interp.acts) <= SHORT_REPLY_ACTS and q is None:
        return Decision("none", "resposta curta sem pergunta aberta: só recebimento")

    # 6. Ação com consequência é confirmada antes de chamar a ferramenta.
    for act in interp.acts:
        if act in policy.actions_requiring_confirmation:
            return Decision("confirm", f"'{act}' exige confirmação explícita antes")

    # 7. Aplicar os fatos e depois verificar o que ainda falta.
    apply_events(state, interp)
    missing = [f for f in state.required_fields if f not in state.fields]
    if interp.ambiguities:
        return Decision("clarify", f"ambiguidade: {interp.ambiguities[0]}")
    if missing:
        return Decision("clarify", f"campo obrigatório faltando: {missing[0]}")

    return Decision("answer", "evidência e dados suficientes para responder")

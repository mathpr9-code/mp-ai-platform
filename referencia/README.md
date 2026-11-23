# Implementação de referência

Uma implementação pequena, de propósito, em Python, de duas ideias do framework:

- **A camada de decisão como função pura** ([`src/mp_agent/decision.py`](src/mp_agent/decision.py)): recebe a interpretação do extrator, o estado e a conversa, e devolve uma conduta. Sem LLM, sem I/O, testável por completo.
- **A suíte de erros como dado** ([`tests/error_suite/`](tests/error_suite/)): cada caso é um arquivo YAML; um único executor roda todos.

O extrator em si (a chamada ao LLM) fica fora daqui de propósito: os casos fornecem a saída dele em `interpretation`, que é exatamente como os casos de decisão rodam no framework, sem modelo.

Os nomes de campos e condutas no código ficam em inglês (`answer`, `clarify`, `transfer`…) porque são o contrato entre as etapas; o restante está em português.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -v
```

## Regras implementadas em `decide()`

A ordem importa: a primeira regra que casa decide.

| Ordem | Regra | Caso |
| --- | --- | --- |
| 1 | Toda citação precisa existir literalmente no turno citado | ERR-0041 |
| 2 | Atingido o limite de esclarecimento, para de perguntar e transfere | ERR-0045 |
| 3 | Pedido explícito e citado por um humano é transferido | ERR-0044 |
| 4 | A resposta é resolvida contra a pergunta aberta que ela responde (o turno é um par) | SEC-001, SEC-002, ERR-0043 |
| 5 | Resposta curta sem pergunta aberta não dispara nada | SEC-003 |
| 6 | Ação com consequência é confirmada antes de chamar a ferramenta | SEC-011 |
| 7 | Fatos entram no estado como eventos; campo faltando gera uma pergunta | ERR-0042, ERR-0046 |

## Adicionar um caso

Copie qualquer arquivo de `tests/error_suite/cases/`, descreva a menor conversa que reproduz o bug e a conduta esperada, e rode `pytest`. O caso novo precisa falhar antes da correção e passar depois, com todos os outros continuando verdes.

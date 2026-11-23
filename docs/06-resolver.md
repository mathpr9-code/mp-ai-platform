# 3. Resolver — código decide, LLM redige

Resolver são quatro passos com donos diferentes.

| Passo | Dono | Entrega |
| --- | --- | --- |
| Decidir | Código: tabela de regras ou máquina de estados | A conduta |
| Executar | Código: ferramenta com validação e idempotência | Resultado confirmado pela fonte |
| Redigir | LLM, a partir de um ato estruturado | Texto da resposta |
| Verificar | Código, e juiz LLM só para critério semântico | Aprovada, retry ou escape |

## Escolha da peça

| Sinal na descoberta | Peça |
| --- | --- |
| Resposta é regra objetiva ou cálculo | RES3 — regra ou tabela; LLM só redige |
| Processo conhecido com poucos pontos de julgamento | RES4 — workflow com LLM em nós específicos |
| Resposta factual com risco de alucinação | RES2 — geração mais verificação |
| Pergunta simples e bem delimitada | RES1 — resposta fundamentada em uma passagem |
| O caminho depende do resultado de cada passo | RES5 — agente com ferramentas e teto de passos, dentro de um nó |
| Tarefa composta com etapas verificáveis | RES6 — planejar e executar |
| Contextos ou ferramentas realmente distintos | RES7 — especialistas |
| Qualquer efeito externo | RES8 — execução governada, sempre, somada à peça acima |

Comece por workflow. Só troque um nó por agente quando o gold set mostrar que o caminho fixo não cobre os casos reais.

## Protocolo do redator (narrador)

A máquina decide e emite um ato; o redator escreve sobre ele; o código verifica. Reprovou: um retry. Reprovou de novo: texto de escape determinístico. O cliente nunca recebe informação errada e nunca fica sem resposta.

- **Literal ou narrado.** Texto crítico (conduta clínica, segurança, jurídico) e texto aprovado saem literais, sem modelo. Só se narra onde a naturalidade agrega e o risco permite.
- **Campos do ato.** `ato_id`, `acao`, `fatos` (com origem; única fonte do que pode ser afirmado), `deve_conter`, `nao_pode`, `referencia_redacao`. O `risco` e o `escape_template` ficam no código e não vão ao modelo.
- **Dado não confiável.** Mensagem do cliente e conteúdo recuperado entram em bloco próprio, como dado, nunca como instrução.
- **Verificador em duas camadas.** Primeiro o determinístico: ids batem, obrigatórios presentes, nenhum número, link ou dado pessoal fora do ato, tamanho. Depois, se necessário, juiz em outro modelo com perguntas fechadas por afirmação.

```json
{
  "ato_id": "a1",
  "acao": "confirmar_alteracao",
  "fatos": [{"fato_id": "f1", "origem": "maquina:api_reservas", "texto": "reserva alterada para 5 pessoas"}],
  "deve_conter": ["5 pessoas"],
  "nao_pode": ["prometer mesa específica"]
}
```

## Execução de ação

Uma ação proposta pela decisão leva: tipo, ferramenta registrada, argumentos validados, escopo de autorização, pré-condições, nível de risco definido na política, chave de idempotência e validade. O ciclo: autorizar, validar, registrar a tentativa antes do efeito, executar, validar o resultado, registrar, atualizar estado, emitir o ato. Estados: proposta, autorizada, rejeitada, executando, sucesso, falha, timeout, desconhecido, compensada. "Desconhecido" existe porque um timeout pode ocorrer depois de o sistema externo ter concluído; reconcilie antes de repetir.

## Responsabilidades de LLM e código

Resolver não é só redigir uma resposta: pode ser explicar, comparar, orientar, calcular, consultar, registrar, atualizar, agendar ou executar uma sequência de operações.

O LLM pode: sintetizar evidências; relacionar contexto e regras; explicar possibilidades e consequências; propor um plano ou próximos passos; redigir uma resposta contextualizada; sugerir chamadas a ferramentas dentro do catálogo disponível.

O código e os sistemas podem: aplicar regras determinísticas e políticas; verificar permissões, limites e pré-condições; validar parâmetros, entidades e estado; realizar cálculos críticos; autorizar ou bloquear operações; executar transações por API; confirmar o resultado efetivamente realizado.

A divisão não é "LLM nunca decide nada" contra "LLM decide tudo". A arquitetura explicita quais decisões são semânticas, quais são políticas e quais causam efeitos externos. Quanto maior o impacto, mais fortes os controles determinísticos, as aprovações e a auditabilidade.

## Política de resolução e autoridade

Antes de executar, verifique:

1. A interpretação possui evidência suficiente?
2. Os fatos necessários foram investigados?
3. As fontes são autorizadas, atuais e consistentes?
4. A ação está dentro do escopo?
5. O agente tem permissão explícita para executá-la?
6. A ação é reversível? Há necessidade de confirmação?
7. O resultado pode ser verificado na fonte de origem?
8. O que acontece em caso de erro, timeout ou resposta parcial?

Nunca narrar como concluída uma ação que apenas foi proposta, solicitada ou iniciada.

## Métricas de Resolver

- Correção da solução final
- Fidelidade às fontes e às políticas
- Taxa de afirmações sem suporte
- Sucesso de tarefa, não apenas qualidade textual
- Acerto na escolha da ferramenta e nos argumentos
- Taxa de execução confirmada
- Erros, duplicidade e efeitos colaterais
- Número de passos e tentativas
- Custo, latência e taxa de recuperação após falha
- Consistência em reexecuções equivalentes
- Decisão medida à parte, contra o gold set de decisão, sem LLM
- Redação: aderência ao ato, taxa de retry e de escape
- Portão próprio: nenhuma ação narrada como feita sem confirmação da fonte

# 1. Interpretar — o extrator

O extrator deve ter o máximo de inteligência para ler e zero autoridade para decidir. O dilema "node burro ou node inteligente" mistura dois eixos.

| Eixo | Pergunta | Nível certo no extrator |
| --- | --- | --- |
| Compreensão | O que a pessoa disse, considerando histórico e vocabulário do cliente? | Alto: precisa de contexto, glossário e definições |
| Autoridade | O que fazer com isso? | Nenhum: regra, estado, política e próximo passo ficam no código |

O extrator é um tradutor: recebe linguagem livre e devolve um vocabulário fechado que o código entende. Ele não precisa saber o que será feito com a tradução.

## Teste de fronteira

Para cada campo, pergunte: duas pessoas, lendo só a conversa e o glossário, sem conhecer as regras do negócio, chegariam ao mesmo valor?

- **Sim:** é campo de extrator. Exemplo: "o cliente corrigiu a data de sexta para sábado".
- **Não, depende de regra, sistema ou consequência:** é campo de código. Exemplo: "pode remarcar", "deve transferir", "é elegível".

Se o código nunca lê um campo, o campo não existe.

A Rasa descreve a mesma separação no CALM: o LLM traduz a fala em comandos internos e um gerenciador de diálogo determinístico executa a lógica ([Bocklisch et al., 2024](https://arxiv.org/abs/2402.12234)). É preprint de fornecedor: desenho de referência, não prova de desempenho.

## Três níveis de extrator

Escolha o nível mais baixo cuja saída é suficiente para o código decidir.

| Nível | O que devolve | Encaixa quando | Custo |
| --- | --- | --- | --- |
| N1 — Classificador | Ato e intenção de lista fechada | Triagem, menu, roteamento | Gold set pequeno; erra em mensagem composta |
| N2 — Comandos e campos | Atos, campos, correções, cancelamentos | Processo com dados a coletar | Definição por campo e estado lido |
| N3 — Interpretação completa | N2 mais referências, condições, ambiguidades e evidência por item | Linguagem aberta, vários assuntos, alto custo de erro | Gold set caro; mais campos para errar |

## Catálogo de padrões de execução

| Padrão | Como funciona | Quando considerar | Limitações e riscos |
| --- | --- | --- | --- |
| I1 — Uma passagem | Um LLM recebe contexto e contrato e devolve tudo | Escopo pequeno ou médio, latência baixa | Muitas tarefas na mesma chamada competem por atenção; erro em uma parte contamina outras |
| I2 — Em etapas | Separa atos, referências e campos | Um slice específico falha na passagem única | Mais chamadas, latência e erros de propagação |
| I3 — Seletor mais extrator | Um componente diz o que mudou; outro extrai só isso | Schema grande, conversa incremental | O seletor pode deixar passar uma atualização; medir o recall dele à parte |
| I4 — Contexto por campo | Recupera os turnos relevantes para cada campo | Histórico longo, tópicos paralelos | A recuperação pode omitir evidência importante; avaliar cobertura |
| I5 — Schema dinâmico | Seleciona parte do schema e dos exemplos antes de extrair | Muitos domínios e intenções | A seleção de schema pode omitir o campo correto |
| I6 — Roteador mais especialista | Regra ou classificador encaminha para um extrator específico | Alto volume, intenções delimitadas | Erro de roteamento impede o especialista certo de ser acionado |
| I7 — Saída estruturada | Saída presa a um schema pelo provider | Sempre que o código consome a saída | Estrutura válida não prova fidelidade; suporte e limites variam por provider e modelo |
| I8 — Incremental | Por campo: herdar, atualizar, remover ou marcar desconhecido | Dados acumulados e correções ao longo dos turnos | O estado anterior pode propagar erro; preservar evidência e permitir correção |
| I9 — Modelo ajustado | Fine-tuning ou destilação | Gold set estável e volume que pague a manutenção | Exige dataset adequado, avaliação fora do treino e custo de operação |

Os padrões se combinam: I5 seleciona o schema, I4 monta o contexto e I7 restringe a saída. Isso não obriga a usar três LLMs; parte das operações pode ser determinística.

## De onde vem a inteligência

Mexa nas alavancas nesta ordem. Trocar de modelo é a quinta.

1. **Contrato.** Cada campo com definição, quando marcar, quando não marcar e um par de exemplos contrastivos.
2. **Contexto.** A última fala do agente com a pergunta que ficou aberta, os turnos relevantes, o estado pendente em leitura e o glossário. Ver "O turno é um par", na seção Entrada.
3. **Espaço para pensar.** Vale para qualquer modelo com raciocínio configurável: teste níveis de esforço diferentes no gold set em vez de aceitar o padrão do provedor, e coloque os campos de evidência antes dos de conclusão no schema. Exemplo: a família GPT-5.4 roda com `reasoning.effort` em `none` por padrão e a OpenAI recomenda subir aos poucos e medir ([guia](https://developers.openai.com/api/docs/guides/latest-model/gpt-5.4)).
4. **Decomposição.** I2 ou I3, só quando um slice falha.
5. **Modelo maior.** Depois de esgotar 1 a 4, no mesmo gold set.
6. **Fine-tuning.** Só com gold set estável.

[Tam et al., 2024](https://arxiv.org/abs/2408.02442) observaram queda em tarefas de raciocínio sob restrição de formato e efeito oposto em classificação. Modelos e schemas do estudo são anteriores e simples; é motivo para testar, não número a esperar.

## O que não entra no prompt do extrator

- Regras de negócio, elegibilidade e política
- Critérios de transferência
- Lista de ferramentas e próximo passo
- Persona e tom de voz

Hipótese a medir em cada projeto: um extrator que conhece a regra tende a enxergar o resultado da regra na fala.

## Contrato mínimo de saída (N2)

```json
{
  "evidencias": [{"id": "ev1", "turno": "t18", "trecho": "na verdade somos 5"}],
  "atos": ["correcao"],
  "intencao": "alterar_reserva",
  "campos": [{"nome": "qtd_pessoas", "valor": 5, "origem": "explicito", "evidencia": "ev1"}],
  "correcoes": [{"campo": "qtd_pessoas", "de": 4, "para": 5, "evidencia": "ev1"}],
  "ambiguidades": [],
  "fora_da_lista": false
}
```

`intencao` e `atos` são enums fechados com saída explícita para "nenhuma das anteriores". No N3 o contrato cresce para a representação completa: atos, intenções, menções, referências, relações, restrições, polaridade e modalidade, correções, evidências, ambiguidades, desconhecidos e suficiência do contexto.

## O que o código faz com a saída

1. Valida schema e enums.
2. Confere se cada `trecho` existe literalmente no turno indicado.
3. Confronta com evidência determinística (CPF, data, código por regex). Em divergência, a determinística vence.
4. Aplica a mudança ao estado por evento, nunca por sobrescrita.
5. Decide o próximo passo.

Precedência de autoridade: evidência determinística explícita, depois estado, depois interpretação do LLM com evidência literal, depois abstenção. Não use a confiança declarada pelo modelo como portão; use `ambiguidades` preenchido, falha de validação e, em campos de alto risco, discordância entre duas execuções.

## Sintoma → alavanca

| Sintoma | Onde mexer primeiro |
| --- | --- |
| Erra "a segunda", "esse", "sim" | Contexto: a mensagem do agente com as opções não chegou |
| Inventa intenção parecida | Contrato: falta a saída "fora da lista" e um exemplo de abstenção |
| Acerta frase simples, erra composta | Contrato: `atos` precisa ser lista; depois I2 |
| Perde a correção | Contexto: estado pendente em leitura; exemplo contrastivo |
| JSON válido com campo errado em conversa longa | Contexto: cortar redundância; I4 |
| Resultado muda entre execuções | Rubrica: a definição é ambígua também para humanos |
| Extrator certo, ação errada | Não é o extrator: olhar a decisão |

## Responsabilidades do extrator

O extrator não é um classificador de intenção nem um conversor de texto para JSON. A interpretação é uma hipótese estruturada e rastreável; o código posterior valida invariantes, origem, permissões e impacto.

O extrator pode:

- Interpretar a mensagem atual com o histórico relevante.
- Identificar um ou mais atos comunicativos: pergunta, solicitação, confirmação, negação, correção, resposta, agradecimento, encerramento.
- Identificar intenções explicitamente comunicadas e distinguir inferência de declaração.
- Extrair entidades e menções sem inventar IDs canônicos.
- Identificar referências como "a segunda", "naquele dia", "esse pedido" e apontar possíveis âncoras.
- Preservar polaridade, negação, modalidade, condição, temporalidade e restrições.
- Identificar correções e indicar qual afirmação anterior parece ser substituída.
- Reconhecer quem falou, para quem e sobre quem, quando o contexto permite.
- Declarar ambiguidades, contradições, contexto insuficiente e desconhecidos.
- Vincular cada elemento relevante às evidências de origem.

O extrator não deve:

- Escolher a próxima ação operacional.
- Alterar diretamente o estado persistido.
- Autorizar ferramenta, consulta ou transação.
- Declarar como verdadeiro um fato operacional não fornecido pela conversa ou por fonte autorizada.
- Transformar automaticamente uma menção em uma entidade canônica.
- Decidir transferência, elegibilidade, aprovação ou política de negócio.
- Tratar score de confiança como autorização.

## O contexto que o extrator precisa receber

O envelope de contexto é composto conforme a tarefa, sem despejar todo o histórico e toda a documentação em cada chamada.

| Parte do contexto | Conteúdo |
| --- | --- |
| Turno atual | Texto original, ID, sequência, canal e metadados confiáveis |
| Histórico conversacional | Turnos anteriores selecionados, com texto original, autor e ordem |
| Contexto de domínio | Vocabulário, conceitos, entidades e distinções relevantes ao negócio |
| Estado anterior | Snapshot de leitura: pendências, valores confirmados, tópicos e fatos de conversa |
| Esquema da tarefa | Campos e conceitos que podem ser interpretados nesta chamada |
| Exemplos | Demonstrações aprovadas e relevantes para os fenômenos presentes |
| Cobertura | Quais turnos, sessões e fontes estão disponíveis; truncamentos e lacunas |
| Proveniência | Versões do perfil, esquema, política e fontes utilizadas |

**Separação crítica:** histórico conversacional não é base de conhecimento. Histórico responde "o que já foi dito nesta conversa?". Base de conhecimento responde "o que a organização registra como fato ou regra?". Perfil de domínio ensina vocabulário e distinções; não substitui consulta a fontes operacionais.

## Estratégias de contexto

Não são mutuamente exclusivas:

- **Histórico completo:** quando couber e a avaliação mostrar que ajuda.
- **Janela recente:** quando a tarefa depende de continuidade local.
- **Recuperação por turno:** selecionar mensagens antigas relevantes à intenção ou ao campo atual.
- **Recuperação por sessão:** recuperar conversas inteiras relacionadas ao pedido atual.
- **Seleção por campo:** consultar evidências específicas de cada campo a atualizar.
- **Resumo hierárquico:** resumos como índice, mantendo a possibilidade de recuperar a evidência original.
- **Memória estruturada:** valores candidatos, proveniência, temporalidade e incerteza em estrutura própria.
- **Recuperação de schema:** trazer apenas definições de campos, conceitos e exemplos relevantes.
- **Recuperação de exemplos:** buscar exemplos de interpretação semelhantes; exemplos orientam formato e distinções, não criam fatos sobre o cliente.

Não substituir o histórico original por um resumo irreversível. A ordem e o conteúdo do contexto devem ser experimentados: mais documentos, exemplos ou histórico não é automaticamente melhor, e redundância pode degradar a fidelidade.

## Representação completa da interpretação (N3)

| Grupo | O que registra | Exemplo |
| --- | --- | --- |
| communicative\\_acts | Atos realizados no turno | question, request, correction, denial |
| expressed\\_intents | Objetivos comunicados | consultar status, alterar cadastro |
| mentions | Expressões citadas | "pedido", "sexta-feira", "plano premium" |
| references | Expressões que apontam para turnos ou objetos anteriores | "a segunda", "esse valor" |
| relations | Relações entre menções, eventos e turnos | cliente corrige quantidade anterior |
| constraints | Condições, limites e preferências | "depois das 18h", "somente se houver vaga" |
| polarity\\_modality | Negação, possibilidade, certeza, intenção ou hipótese | "não paguei", "talvez eu reserve" |
| corrections | Valor anterior, novo valor e evidência da substituição | 4 pessoas → 5 pessoas |
| evidence | Trecho, turno, autor e localização | citação literal e turn\\_id |
| ambiguities | Leituras concorrentes | referência sem âncora única |
| unknowns | Informação necessária não informada | número do pedido ausente |
| context\\_status | Suficiência do contexto | sufficient, partial, insufficient |

```json
{
  "turn_id": "turn_018",
  "communicative_acts": [{"type": "correction", "evidence": ["ev_01"]}],
  "assertions": [
    {
      "field_candidate": "party_size",
      "value": 5,
      "polarity": "positive",
      "modality": "asserted",
      "status": "explicit",
      "evidence": ["ev_01"]
    }
  ],
  "corrections": [
    {
      "replaces_turn_id": "turn_014",
      "old_value_candidate": 4,
      "new_value_candidate": 5,
      "evidence": ["ev_01"]
    }
  ],
  "ambiguities": [],
  "unknowns": [],
  "context_status": "sufficient"
}
```

O formato final é versionado e adaptado ao domínio; o exemplo não é um schema universal. O princípio universal é preservar a distinção entre texto original, interpretação, evidência, referência e incerteza.

## Dimensões de avaliação do extrator

| Dimensão | O que medir |
| --- | --- |
| Atos comunicativos | Precisão, recall e F1 por tipo de ato |
| Intenções | Precisão, recall e F1; intenção principal e secundárias |
| Menções e campos | Exact match quando aplicável, F1 de trecho e normalização |
| Referências | Identificação da expressão, seleção de âncora e taxa de referência errada |
| Correções | Novo valor, valor substituído e vínculo correto |
| Negação e polaridade | Acerto em afirmação, negação, recusa e cancelamento |
| Condições e restrições | Datas, quantidades, intervalos, preferências e condições |
| Atribuição | Autor correto; distinção entre fala do cliente, do assistente e de terceiro |
| Evidências | Fidelidade da citação, turno correto e suporte semântico |
| Ambiguidade | Detecção, classificação e abstenção correta |
| Contexto | Sensibilidade a truncamento, turnos distantes e troca de assunto |
| Incrementalidade | Atualização, herança, substituição e remoção de valor |
| Robustez | Mensagens compostas, erros de digitação, gírias, vários usuários e distrações |
| Acerto conjunto do turno | Turnos em que todos os elementos obrigatórios estão corretos |
| Calibração | Se o grau de incerteza acompanha a taxa real de erro |

Uma média alta não pode esconder falha crítica em negação, correção, autor, referência ou campo de alto impacto. Resultados são apresentados por fenômeno, risco e tipo de contexto. JSON válido não prova interpretação correta: validade da estrutura e fidelidade do conteúdo são medidas separadas. Cada slice crítico tem portão próprio.

### Slices mínimos de teste

- Mensagem direta e explícita
- Uma mensagem com várias intenções
- Resposta curta a uma pergunta anterior
- Referência anafórica e seleção entre opções
- Correção de informação já fornecida
- Negação inicial e negação embutida
- Condição, ressalva, hipótese e intenção futura
- Informação implícita versus explicitamente afirmada
- Mudança de assunto e retomada de tópico
- Informação contraditória entre turnos
- Conversa com múltiplos participantes
- Histórico truncado ou insuficiente
- Campo desconhecido ou fora do schema
- Instrução maliciosa contida na mensagem ou no conteúdo recuperado

### Método de comparação

1. Congelar entradas, contexto, schema e rótulos.
2. Construir uma linha de base simples e reproduzível.
3. Comparar uma variável por vez: seleção de contexto, padrão de extração, modelo, exemplos, schema ou otimização.
4. Rodar todas as candidatas nos mesmos casos.
5. Separar desenvolvimento, regressão e holdout por conversa ou grupo correlacionado, não por turnos aleatórios.
6. Examinar erros por fenômeno e custo e latência.
7. Repetir testes quando a saída for não determinística.
8. Só promover após os gates definidos para o risco do agente.

## Métodos para evoluir o extrator

- **Prompt engineering:** instruções explícitas, fronteiras, definições e casos contrastivos.
- **Few-shot e exemplos recuperados:** exemplos curados e próximos do fenômeno atual.
- **Recuperação de contexto e schema:** buscar apenas o domínio, os campos e os exemplos necessários.
- **Otimização de prompt ou programa:** DSPy ou equivalente, quando há métrica reproduzível, conjunto de desenvolvimento e limite de orçamento.
- **Classificador auxiliar:** detectar idioma, tipo de ato, domínio ou rota quando reduzir custo sem sacrificar recall.
- **Fine-tuning supervisionado:** quando existe volume suficiente de exemplos corretos e estáveis.
- **Destilação:** transferir comportamento de um modelo maior para um menor, com validação separada.
- **Preferência (DPO e afins):** quando a tarefa é escolher entre interpretações e há pares de qualidade confiável.
- **RFT/RL:** só quando há objetivo, recompensa e ambiente de avaliação adequados; não como primeira resposta a um extrator ruim.

Otimização automática não substitui a qualidade do gold set: um algoritmo pode otimizar a métrica errada, superajustar o conjunto e mascarar erros de anotação.

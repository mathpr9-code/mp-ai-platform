# Matriz de montagem

| Sinal na descoberta | Interpretar | Investigar | Resolver | Esclarecer | Transferir |
| --- | --- | --- | --- | --- | --- |
| Triagem entre setores | N1 | Nenhuma | RES3 | ESC2 | TR1 + TR4 |
| Dúvidas sobre base pequena e estável | N1 ou N2 | Base no contexto | RES1 ou RES2 | ESC2 | TR1 |
| Dúvidas sobre base grande | N2 | INV4 + INV5 | RES2 | ESC2 | TR1 |
| Processo com dados a coletar e ação no sistema | N2 com I8 | INV1 | RES4 + RES8 | ESC1 + ESC4 | TR1 + TR3 |
| Linguagem aberta, vários assuntos por conversa | N3 | Conforme a fonte | RES4 | ESC2 + ESC5 | TR2 |
| Perguntas que cruzam várias fontes | N2 ou N3 | INV7 limitado, ou INV10 | RES2 | ESC3 | TR1 |
| Alto custo de erro | N3 com evidência obrigatória | Só fontes autorizadas | RES3 + RES8 com aprovação | ESC4 | TR1 com recall como portão |

## Ordem de montagem no quadro

Do contexto do cliente ao desenho, nesta ordem. Cada linha diz o que escolher e o que direciona a escolha.

| Passo | O que escolher | O que direciona |
| --- | --- | --- |
| 1 | Faixa do cliente: objetivo, canal, volume, risco, limites | A descoberta |
| 2 | Onde o agente roda | Pausa para humano, laços, exigência da suíte de erros, quem opera |
| 3 | Entrada: peças de mídia e de buffer | Tipos de mensagem que o público envia; hábito de mandar mensagem picada |
| 4 | Interpretar: nível (N1 a N3) e padrão (I1 a I9) | O que o código precisa ler para decidir; variedade da linguagem; custo do erro |
| 5 | Investigar: degrau da escada e ficha de RAG | Onde mora cada fato do mapa de dados; tamanho e formato da base |
| 6 | Resolver: peça e ações no sistema | Se o caminho é conhecido; se há efeito externo |
| 7 | Esclarecer: peças e limites de pergunta | Campos obrigatórios; ações que pedem confirmação |
| 8 | Transferir: gatilhos, filas, retomada | Regras do cliente; quem atende do outro lado |
| 9 | Modelo por papel, com candidato | Dificuldade do fluxo; orçamento; skill existente |
| 10 | Estado e observabilidade | O que precisa sobreviver entre turnos; onde os dados podem ficar |
| 11 | Setas: retorno ao Interpretar, pendências, transferências | O comportamento real da conversa, com o par fala do agente mais resposta |
| 12 | Encaixes obrigatórios e primeiros casos da suíte de erros | A tabela abaixo; as hipóteses mais arriscadas de cada coluna |

O quadro pronto vira o plano: uma fase por coluna, na ordem entrada, interpretar, decisão, investigar, resolver, esclarecer, transferir, controle.

## Encaixes obrigatórios

| Se escolher | Precisa de |
| --- | --- |
| ESC1 | Extrator N2 ou N3 e estado com campos |
| RES8 | Extrator N2 ou N3, INV1 para confirmar, idempotência |
| TR3 | Estado persistido e orquestração com checkpoint |
| INV7 ou RES5 | Orquestração com teto de passos e trace por passo |
| RES2 | Ato estruturado com fatos permitidos |
| Extrator N3 | Gold set com evidência rotulada e seleção de turnos por código |

## Exemplo A — agendamento em clínica

- **Interpretar:** N2 incremental. Campos: especialidade, data, período, paciente. Atos: informar, corrigir, confirmar, cancelar, pedir humano.
- **Investigar:** INV1 na API da agenda. Sem RAG.
- **Resolver:** RES4 mais RES8.
- **Esclarecer:** ESC1 para campo faltante, ESC4 antes de gravar.
- **Transferir:** TR1 para convênio fora da lista e para duas tentativas sem avanço.
- **Hipótese mais arriscada:** correção de data em mensagem curta. É o primeiro slice do gold set.

## Exemplo B — suporte sobre manuais de produto

- **Interpretar:** N2. Campos: produto, modelo, código de erro.
- **Investigar:** medir primeiro a base inteira no contexto; se não couber ou não atingir o alvo, INV4 mais INV5 com filtro por produto.
- **Resolver:** RES2, só com trechos citados.
- **Esclarecer:** ESC2 quando o modelo do produto é ambíguo.
- **Transferir:** TR1 quando a busca devolve "insuficiente".
- **Hipótese mais arriscada:** recall em código de erro. Medir a busca sozinha antes de olhar a resposta.

# Seleção e composição

## Eixos de arquitetura independentes

Uma escolha em uma dimensão não determina as demais.

| Eixo | Opções possíveis | Pergunta de seleção |
| --- | --- | --- |
| Modelo | API hospedada, pesos abertos, modelo pequeno ou especializado, ajustado | Qual desempenho, custo, privacidade e latência? |
| Interpretação | Uma passagem, etapas, seletor, incremental, schema dinâmico | Que fenômenos e contextos precisam ser interpretados? |
| Recuperação | SQL/API, lexical, vetorial, híbrida, grafo, agêntica | Onde estão os fatos e como são encontrados? |
| Memória | Histórico completo, janela, recuperação na consulta, resumos, memória estruturada, grafo | Que tipo de continuidade precisa ser preservado? |
| Resolução | Regras, workflow, LLM mais validador, laço de agente com ferramentas | Quão variável é o caminho até a solução? |
| Esclarecimento | Campos obrigatórios, modelo de ambiguidade, ordenação de perguntas, confirmação | Quem pode resolver a lacuna e com qual pergunta? |
| Transferência | Por regra, guarda de política, interrupção de workflow, fila humana | Quais condições encerram ou pausam a autonomia? |
| Orquestração | Pipeline, grafo de workflow, laço limitado, laço de agente, multiagente | O fluxo é conhecido ou depende de resultados intermediários? |
| Persistência | Relacional, documento, log de eventos, checkpoint, grafo | Que estado precisa sobreviver, ser consultado e auditado? |
| Avaliação | Gold set, replay, simulação, shadow, avaliação online | Qual risco e qual volume exigem prova? |

## Quatro composições de referência

Não são templates obrigatórios.

**A. Agente informativo de escopo delimitado**

- Interpretar: extração simples com schema.
- Investigar: busca lexical ou semântica, ou consulta direta, conforme a fonte.
- Resolver: resposta fundamentada em evidências.
- Esclarecer: pergunta quando falta dado realmente necessário.
- Transferir: regra de fora de escopo e fila humana.
- Orquestração: pipeline simples.

**B. Agente transacional com campos e estado**

- Interpretar: extração incremental e rastreamento de campos.
- Investigar: API ou SQL para disponibilidade, cadastro ou status.
- Resolver: código valida pré-condições e executa; LLM explica.
- Esclarecer: coleta somente os campos ausentes.
- Transferir: aprovação, erro ou risco encaminha a humano.
- Orquestração: workflow persistente.

**C. Agente de conhecimento multi-fonte**

- Interpretar: contexto e referências multi-turno.
- Investigar: busca híbrida, reranking, APIs e eventualmente grafo.
- Resolver: síntese com evidências e validação.
- Esclarecer: identifica subperguntas e lacunas.
- Transferir: lacuna de fonte ou decisão especializada.
- Orquestração: workflow com subagente de investigação, se necessário.

**D. Agente com autonomia limitada e alto impacto**

- Interpretar: estratégia de alta cobertura, evidência e abstenção.
- Investigar: somente fontes autorizadas e verificáveis.
- Resolver: política determinística, validação e portão de aprovação.
- Esclarecer: coleta apenas dados necessários e confirma ações relevantes.
- Transferir: gatilhos obrigatórios e handoff com prioridade.
- Orquestração: workflow auditável; autonomia de agente só em perímetro restrito.

## Critérios de decisão

Para cada alternativa, pontue ou descreva: adequação semântica à tarefa; qualidade demonstrada no benchmark do domínio; cobertura de fenômenos difíceis; previsibilidade e controle; custo de inferência, indexação e manutenção; latência; necessidade de dados rotulados; privacidade e residência de dados; disponibilidade de ferramentas e integração; auditabilidade e observabilidade; capacidade de evolução e substituição; complexidade operacional para a equipe.

Não atribua pesos universais. Um cliente prioriza precisão e auditabilidade; outro, latência e custo. Os pesos vêm dos requisitos descobertos.

## Processo de decisão por capacidade

1. Descrever a necessidade com exemplos reais ou cenários aprovados.
2. Definir o contrato de entrada e saída.
3. Listar pelo menos duas alternativas razoáveis quando houver escolha material.
4. Construir um protótipo pequeno de cada alternativa.
5. Medir as alternativas nas mesmas entradas.
6. Analisar resultados por slice, custo e latência.
7. Registrar limites conhecidos e riscos.
8. Selecionar, justificar e versionar a decisão.
9. Manter a possibilidade de substituição sem quebrar o contrato.

## Modelo de ADR

```yaml
adr:
  id: ADR-XXXX
  capability: interpretar | investigar | resolver | esclarecer | transferir
  status: proposed | accepted | rejected | superseded
  problem: ""
  business_requirements: []
  constraints: []
  alternatives:
    - name: ""
      pattern: ""
      technologies: []
      expected_tradeoffs: []
  evaluation:
    dataset_version: ""
    metrics: []
    results: []
    cost: ""
    latency: ""
  decision: ""
  rationale: []
  known_limits: []
  rollback_or_replacement: ""
  owner: ""
  date: ""
```

A tecnologia pode mudar. O contrato e os requisitos que motivaram a decisão continuam rastreáveis.

## Exemplo integrado: alteração de um pedido

Cenário hipotético. Pessoa: "Quero alterar o endereço daquele pedido. Não é o que fiz ontem, é o que ainda não saiu."

| Capacidade | Trabalho realizado | Alternativa possível |
| --- | --- | --- |
| Interpretar | Identificar solicitação de alteração, objeto "pedido", referência "daquele", distinção negativa em relação ao pedido de ontem e condição "ainda não saiu" | LLM com representação estruturada mais histórico selecionado |
| Investigar | Localizar pedidos do usuário e consultar status e logística na API autorizada | Código mais API ou SQL |
| Resolver | Verificar se a alteração é permitida para aquele status; executar só após validação e confirmação exigida | Política em código mais chamada de ferramenta autorizada |
| Esclarecer | Se houver dois pedidos elegíveis, perguntar qual; não perguntar de novo se a referência já resolveu | LLM formula, código identifica a ambiguidade |
| Transferir | Se o pedido já estiver em etapa que exige intervenção logística, enviar o caso com pedidos candidatos, status e evidências | Máquina de decisão mais fila humana |

O exemplo não exige RAG: o status vem de API. Se a regra de alteração estivesse em um manual, Investigar combinaria recuperação documental com a consulta ao pedido.

## Mapa de tecnologias

Exemplos, não prescrições.

| Tecnologia | Papel possível no framework | Não confundir com |
| --- | --- | --- |
| SDKs de providers de LLM | Chamada de modelo, saída estruturada e tool calling | Arquitetura completa do agente |
| LangChain | Componentes, integrações, prompts, retrievers e abstrações | Um padrão obrigatório de RAG ou de agente |
| LangGraph | Orquestração em grafo, estado, checkpoint e interrupções para humano | GraphRAG ou base de conhecimento em grafo |
| Haystack | Pipelines, retrievers, componentes e agentes | Um modelo de domínio específico |
| OpenAI Agents SDK | Laço de agente, handoffs, guardrails e tracing do ecossistema OpenAI | Obrigação de usar só modelos OpenAI no resto do fluxo |
| Google ADK | Framework de agentes do ecossistema Google | Idem para Gemini |
| Claude Agent SDK | Harness com ferramentas e subagentes prontos | Runtime de atendimento com decisão em código |
| CrewAI, LlamaIndex, Vercel AI SDK | Frameworks de agente e de aplicação citados pela documentação do LangChain como alternativas | Padrões equivalentes entre si; cada um tem abstrações próprias |
| Temporal, Inngest | Runtimes de execução durável, alternativas ao LangGraph | Framework de agente |
| Microsoft GraphRAG | Indexação e consulta por grafos de conhecimento (busca local, global, DRIFT) | Orquestração de workflow conversacional |
| DSPy | Programação declarativa e otimização de prompts a partir de métricas | Substituto de gold set ou de critério de qualidade |
| LangSmith / Langfuse | Tracing e avaliação | Métrica universal por si só |
| Ragas | Métricas para recuperação, RAG e agentes | Substituto de referência humana em todo domínio |
| OpenTelemetry | Convenções e instrumentação de traces e métricas | Armazenamento irrestrito de mensagens sensíveis |
| n8n e ferramentas de integração | Gatilhos, conectores, automação e integração de sistemas | A camada semântica ou a política do agente |

A escolha considera maturidade, licença, custo, linguagem, deploy, manutenção e aderência ao contrato da capacidade.

Trocas que o framework permite sem mudar os contratos:

- Só LangChain, sem LangGraph, em fluxo simples e sem pausa para humano.
- LangGraph quando houver estado durável, laço ou retomada.
- n8n como orquestrador de fluxo linear, com a decisão em um nó de código.
- Langfuse no lugar do LangSmith, ou o contrário.
- Qualquer provider de modelo por papel.

Os frameworks além de LangChain, LangGraph e Haystack entraram nesta tabela a partir da lista da documentação do LangChain; não abri a documentação de cada um. Antes de adotar um deles, a regra é a mesma dos modelos: ler a fonte oficial e registrar como ADR.

# Protocolo de construção de um agente

1. **Descobrir:** entrevistar o cliente, mapear tarefas, público, canais, fontes, regras, riscos e handoffs.
2. **Modelar a conversa:** identificar quais capacidades aparecem em cada tipo de atendimento e as condições de transição.
3. **Definir contratos:** entradas, saídas, evidências, estados e fronteiras de autoridade.
4. **Selecionar padrões:** escolher alternativas para cada capacidade sem assumir stack prévia.
5. **Compor a arquitetura:** decidir como as capacidades se comunicam e como contexto, estado, ferramentas e eventos circulam.
6. **Prototipar o maior risco primeiro:** em linguagem livre e contexto multi-turno, validar Interpretar cedo é normalmente essencial.
7. **Construir avaliações:** gold sets por capacidade, cenários multi-turno e avaliação de trajetória.
8. **Comparar opções:** mesma entrada, mesma rubrica, mesma condição de custo e latência.
9. **Implementar governança:** autorização, segurança, persistência, observabilidade, retry e handoff.
10. **Executar shadow ou piloto:** comparar com a operação humana e revisar erros antes de ampliar a autonomia.
11. **Promover por gate:** só capacidades e trajetórias que atendam aos limites de qualidade e risco.
12. **Evoluir:** transformar falhas verificadas em casos de regressão, revisar ADRs e substituir apenas a peça que precisa mudar.

## Critério de pronto da arquitetura

O desenho está pronto para implementação quando:

- cada capacidade necessária tem responsabilidade e contrato definidos;
- alternativas importantes foram comparadas, ou a razão para não comparar está registrada;
- fontes e autoridades estão mapeadas;
- context engineering e estado estão definidos;
- decisões operacionais e semânticas têm responsáveis claros;
- riscos e caminhos de transferência estão explícitos;
- plano de avaliação, dados e gates estão aprovados;
- tecnologias estão ligadas a responsabilidades específicas, não escolhidas por preferência genérica.

O agente só está pronto para produção quando as implementações passam nas avaliações, nos controles de segurança, no shadow ou piloto e nos critérios operacionais. Um desenho coerente não é prova de desempenho.

## Checklist final de arquitetura

- [ ] O objetivo e o resultado de negócio estão claros.
- [ ] As cinco capacidades foram mapeadas para tarefas reais do atendimento.
- [ ] O extrator tem contrato, contexto, evidência, incerteza e avaliação definidos.
- [ ] O tipo de fonte e o padrão de investigação foram escolhidos por requisito, não por moda.
- [ ] Resolver separa síntese semântica, política, autorização e execução.
- [ ] Esclarecer pergunta apenas o que falta e identifica quem pode responder.
- [ ] Transferir possui critérios, pacote, roteamento, confirmação e retomada.
- [ ] Contexto, memória, histórico e estado estão separados.
- [ ] Exemplos, Bootset, Dataset, Gold Set, Regression Set e Holdout têm finalidades distintas.
- [ ] Cada capacidade possui métricas e slices.
- [ ] A arquitetura tem observabilidade, segurança e privacidade por desenho.
- [ ] Ferramentas e frameworks aparecem ligados a padrões e responsabilidades.
- [ ] Decisões materiais estão registradas em ADRs.
- [ ] Limites conhecidos e hipóteses ainda não verificadas estão explícitos.

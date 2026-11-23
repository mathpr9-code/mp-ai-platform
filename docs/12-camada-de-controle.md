# Camada de controle — orquestração, contexto, estado e observabilidade

## Orquestração: escolha pela necessidade

| Necessidade | Peça | Observação |
| --- | --- | --- |
| Sequência conhecida, poucos desvios | Pipeline ou workflow visual (n8n) | Decisão em um nó de código testável, não espalhada em IFs |
| Estado que sobrevive entre turnos | Estado em banco, lido e gravado por evento | Independe do orquestrador |
| Pausa para humano e retomada do ponto exato | Workflow com checkpoint e interrupção (ex.: LangGraph) | É o que TR3 exige |
| Laço cujo fim depende do resultado | Laço limitado, com teto de passos | É o que RES5 e INV7 exigem |
| Testar a decisão sem chamar modelo | Decisão como função pura: estado mais observação entra, conduta sai | Vale para qualquer orquestrador |

LangGraph é orquestração; GraphRAG é recuperação; LangChain é biblioteca de componentes. Nenhum dos três é uma arquitetura.

## Contexto por etapa

| Bloco de contexto | Extrator | Redator | Agente de investigação (se houver) |
| --- | --- | --- | --- |
| Definição dos campos e exemplos contrastivos | Sim | Não | Não |
| Glossário do domínio | Sim | Só termos de fala | Sim |
| Turnos relevantes da conversa | Sim | Últimos, para tom e continuidade | Só a pergunta resolvida |
| Estado pendente | Leitura | Não | Não |
| Regras de negócio e política | Não | Não; chegam como ato | Não |
| Evidências recuperadas | Não | Só os fatos permitidos | Sim |
| Persona e tom | Não | Sim | Não |
| Lista de ferramentas | Não | Não | Sim, fechada |

O envelope de contexto é montado por código e versionado. Ele carrega: conversa (id, tenant, canal), turno atual com texto original, histórico selecionado com autor e ordem, referências abertas, estado em leitura, e metadados de cobertura (histórico completo ou truncado, turnos ausentes, método de seleção). Conteúdo estável vai primeiro, para aproveitar cache. Texto do cliente e conteúdo recuperado entram como dado, nunca como instrução. Histórico não é base de conhecimento, e resumo não substitui a mensagem original.

## Estado

Quatro coisas diferentes, que não devem ser tratadas como "memória":

| Tipo | O que guarda | Regra |
| --- | --- | --- |
| Histórico bruto | O que foi dito, em ordem | Fonte de auditoria; nunca reescrito |
| Estado conversacional | Tópico, pendências, campos confirmados | Muda só por evento validado |
| Estado de execução | Ações, transferências, entregas | Controlado pelo sistema |
| Memória de longo prazo | Preferências e fatos entre sessões | Política de retenção e correção |

O estado muda por eventos explícitos (mensagem recebida, correção recebida, pendência criada, pendência resolvida, ação iniciada, ação concluída, transferência solicitada, entrega confirmada, conversa encerrada). Um redutor determinístico transforma estado anterior mais evento em estado novo. Cada evento leva id, turno de origem, tipo, autor, versão esperada do estado e chave de idempotência, para que duplicata e evento atrasado não corrompam o estado. O extrator gera candidatos a evento; nunca grava direto.

## Ferramentas

Cada ferramenta registrada documenta: finalidade, schema de entrada e saída, escopo e autorização, pré-condições, efeito externo e reversibilidade, timeout, retry, idempotência e compensação. Function calling é o modelo pedindo uma função; a aplicação valida, aplica a política e executa.

## Observabilidade

Um trace por turno, um span por etapa. A ferramenta (LangSmith, Langfuse, OpenTelemetry) é escolha de stack.

| Por span | Por quê |
| --- | --- |
| Versão do prompt, do schema e do modelo | Saber o que mudou quando a métrica mudar |
| Contexto entregue e saída bruta | Reproduzir a falha e virar caso de regressão |
| Resultado da validação por código | Separar erro de modelo de erro de contrato |
| Conduta decidida e regra que disparou | Auditar a decisão sem ler prompt |
| Tokens, custo, latência | Orçamento por etapa |

Telemetria operacional e conteúdo de conversa ficam em registros separados; o conteúdo é restrito, minimizado e com retenção definida.

## Observabilidade na prática: LangSmith, Langfuse e OpenTelemetry

A unidade de registro é a mesma nas duas plataformas: um **trace** por turno, com um passo por etapa, agrupado por conversa. No Langfuse o agrupamento se chama sessão; no LangSmith, thread.

| Necessidade do framework | LangSmith | Langfuse |
| --- | --- | --- |
| Trace do turno com todos os passos | Runs e traces | Trace composto de observações (chamadas de LLM, ferramentas, recuperação, guardrails) |
| Agrupar por conversa | Threads | Sessões |
| Nota por turno, passo ou conversa | Feedback e avaliadores | Scores numéricos, categóricos ou booleanos em trace, observação, sessão ou experimento |
| Transformar trace de produção em caso de teste | Datasets a partir de runs | "Add to dataset" em qualquer observação |
| Rodar suíte contra uma versão | Experimentos em datasets (avaliação offline) | Experimentos em datasets |
| Avaliar tráfego real | Avaliadores online por regra, também no nível da thread | Juiz LLM e avaliadores de código em tráfego ao vivo |
| Revisão humana estruturada | Filas de anotação | Filas de anotação |
| Versionar prompt | Prompts e playground | Gestão de prompts com versões e rótulos buscados em runtime |
| Hospedagem | Nuvem ou auto-hospedado | Código aberto, auto-hospedável |

Fontes: [LangSmith — Evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts), [Langfuse — Docs](https://langfuse.com/docs), [Langfuse — Tracing](https://langfuse.com/academy/tracing.md), [Langfuse — Clarifications](https://langfuse.com/resources/engineering/clarifications.md). A tabela compara o que cada documentação descreve; não é um teste lado a lado.

Como escolher: o que já está na stack, se os dados podem sair da sua infraestrutura, e se o time vai versionar prompt na mesma ferramenta. A escolha é um ADR como qualquer outra peça.

O que instrumentar, independente da ferramenta:

1. Um trace por turno, com id da conversa como sessão ou thread.
2. Um passo por etapa: contexto montado, extrator, validação, decisão, busca, redator, verificador, entrega.
3. Em cada passo de modelo: versão do prompt, modelo exato, tokens, custo, latência.
4. A conduta decidida e a regra que disparou, como metadado do trace.
5. Scores automáticos por turno: validação do extrator, resultado do verificador, ação confirmada.
6. Marca de ambiente (desenvolvimento, staging, produção) e de versão do agente.

O circuito de melhoria que as duas documentações descrevem é o mesmo: traçar, monitorar, montar datasets a partir de produção, experimentar, avaliar, e recomeçar. No framework, é o que alimenta a suíte de erros.

**OpenTelemetry.** As convenções semânticas de GenAI dão nomes padronizados a operações como `invoke_agent`, `execute_tool`, `chat` e `retrieval`, e a atributos como modelo e uso de tokens. Elas ainda estão em status de desenvolvimento, sem versão estável, e o conteúdo de prompts e respostas só é gravado quando habilitado. Consequência prática: fixar a versão da instrumentação e contar com renomeações. Esta descrição vem de resumos de terceiros publicados em 2026; confira na [especificação](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md) antes de adotar.

## Monitoramento em produção

Fase 8 do ciclo de vida. "Observabilidade" diz o que instrumentar. Esta seção diz o que olhar todo dia, quando alguém deve ser avisado e o que vai para o relatório do cliente.

### O que monitorar

| Item | Métrica | Fonte | Ferramenta | Quando olhar |
| --- | --- | --- | --- | --- |
| Logs | Log estruturado por turno, com id da conversa e versão | api e worker | Logs da plataforma, Langfuse | Ao investigar |
| Performance | Latência p50 e p95 do turno e de cada etapa | Trace | Langfuse; Grafana para infraestrutura | Diário |
| Uso | Conversas, turnos, conversas por cliente e por canal | Banco e trace | Langfuse, painel próprio | Diário |
| Erros | Erro de ferramenta, schema inválido, timeout, falha de entrega | Trace e outbox | Langfuse, alertas | Contínuo |
| Feedback do usuário | Sinais implícitos e explícitos (abaixo) | Conversa e plataforma de atendimento | Scores do Langfuse | Semanal |
| Custo | Custo por turno, por conversa, por cliente e por modelo | Trace (tokens × preço) | Langfuse; painel de custo do provedor | Diário |
| Alertas | Limiares da tabela abaixo | Todos acima | Langfuse, Grafana | Contínuo |
| Auditoria | Quem fez o quê, quando, em qual versão | Registro de auditoria | Banco | Sob demanda |
| Relatório | Resumo por cliente | Todos acima | Relatório semanal | Semanal |

### Ferramentas e divisão de papéis

| Ferramenta | Papel | O que já traz |
| --- | --- | --- |
| Langfuse | Qualidade e custo por turno | Traces, custo por usuário e por modelo, scores, feedback, datasets, alertas por Slack, GitHub Actions ou webhook quando uma métrica cruza o limiar |
| Grafana + OpenLIT | Saúde da infraestrutura e SLO | OpenLIT gera traces e métricas em OpenTelemetry; o Grafana Cloud tem painéis prontos de GenAI, avaliações e banco de vetores, e alertas |
| Application Insights | Infraestrutura no Azure | Telemetria com OpenTelemetry, alertas do Azure Monitor |
| CloudWatch e AgentCore Observability | Infraestrutura e agente na AWS | Logs, métricas, alarmes e traces do agente no AgentCore |
| Painel da plataforma de IA da DigitalOcean | Custo da inferência serverless | Custo estimado e tokens por modelo e por chave, atualizados a cada 10 minutos |

Langfuse responde se o agente está bom e quanto custa. Grafana responde se a máquina está de pé. Os dois recebem os dados por OpenTelemetry, então adotar o Grafana não muda a instrumentação.

### Observabilidade por porte e custo

Regra: **uma ferramenta de tracing padrão para todos os agentes: Langfuse.** Assim o time aprende uma só e compara agentes no mesmo lugar. O que muda por porte é o plano e se ela roda na nuvem ou na infraestrutura da MP. Grafana não substitui o tracing de LLM: ele mostra a saúde da infraestrutura e entra quando há serviço próprio com mais de um processo.

| Ferramenta | Licença e hospedagem | Custo (consultado em 23/11/2026) | Quando usar |
| --- | --- | --- | --- |
| Langfuse Cloud Hobby | Nuvem | Grátis: 50 mil unidades por mês (traces, observações e scores), 30 dias de dados, 2 usuários | Porte P |
| Langfuse Cloud Core | Nuvem | US$ 29 por mês com 100 mil unidades; US$ 8 a cada 100 mil extras; 90 dias; usuários ilimitados | Porte M |
| Langfuse self-host | MIT; Docker Compose ou Kubernetes, com Postgres e ClickHouse | Licença grátis e sem limite de uso; paga a infraestrutura e a operação | Porte G, ou quando o dado não pode sair da infraestrutura |
| LangSmith | Nuvem; self-host só no Enterprise | Developer grátis (1 usuário, 5 mil traces por mês); Plus US$ 39 por usuário com 10 mil traces; extra a US$ 2,50 por mil traces | Alternativa quando o time usa o ecossistema LangChain inteiro (deploy, LangGraph) |
| Arize Phoenix | Source-available (Elastic License 2.0, não é licença OSI); self-host em um container | Grátis no self-host | Alternativa self-host leve |
| Grafana + OpenLIT | Grafana OSS self-host ou Grafana Cloud | Confira o plano do Grafana Cloud | Infraestrutura e SLO, a partir do porte M com serviço próprio |

Conta rápida: no Langfuse, um turno com oito passos instrumentados gasta cerca de dez unidades. O Hobby cobre perto de 5 mil turnos por mês; acima disso, o agente já é porte M ou vai para self-host. O Langfuse self-host roda no mesmo droplet do n8n só em porte P e M; em porte G, em máquina própria.

Fontes: [Langfuse — Pricing](https://langfuse.com/pricing), [Langfuse — Self-host pricing](https://langfuse.com/pricing-self-host), [LangSmith — Pricing](https://www.langchain.com/pricing), [Arize Phoenix](https://arize.com/docs/phoenix).

Fontes: [Langfuse — Docs](https://langfuse.com/docs), [Grafana AI Observability](https://grafana.com/docs/grafana-cloud/observe-and-act/monitor-applications/ai-observability/introduction.md).

### Alertas iniciais

Pontos de partida. Calibrar com duas semanas de dados reais de cada cliente.

| Condição | Limiar inicial | Ação |
| --- | --- | --- |
| Erro de ferramenta | Acima de 5% dos turnos em 15 minutos | Avisar; checar a integração do cliente |
| Latência p95 do turno | Acima de 20 segundos por 15 minutos | Avisar; checar provedor de modelo e fila |
| Mensagens paradas na fila | Mais antiga com mais de 2 minutos | Avisar já; risco de mensagem sem resposta |
| Falha definitiva na outbox | Qualquer uma | Avisar já; acionar o protocolo de entrega |
| Schema inválido do extrator | Acima de 2% dos turnos em 1 hora | Avisar; possível troca de comportamento do modelo |
| Custo diário por cliente | Acima de 150% da média dos últimos 7 dias | Avisar; checar laço ou volume anormal |
| Taxa de transferência | Acima de 2 vezes a média semanal | Avisar; checar regressão de versão |
| Score do verificador | Queda de 10 pontos percentuais na semana | Revisar amostra; abrir casos na suíte |

### Feedback do usuário

| Tipo | Sinal | Como registrar |
| --- | --- | --- |
| Implícito | Cliente repete a pergunta, diz que não entendeu, pede humano, abandona no meio do processo | Regra em código grava score negativo no trace |
| Explícito | Pesquisa curta no fim da conversa | Score no trace e na sessão |
| Humano | Atendente marca na plataforma de atendimento que a IA errou | Score com motivo; vai para a fila de anotação |

Todo score negativo com motivo vira candidato a caso da suíte de erros, pelo ciclo de "Suíte de erros".

### Relatório semanal por cliente

| Indicador | Valor | Comparação com a semana anterior |
| --- | --- | --- |
| Conversas atendidas |  |  |
| Resolvidas sem humano |  |  |
| Transferências, por motivo |  |  |
| Custo total e por conversa |  |  |
| Latência p95 |  |  |
| Erros novos (viraram casos) |  |  |
| Mudanças publicadas (versões) |  |  |

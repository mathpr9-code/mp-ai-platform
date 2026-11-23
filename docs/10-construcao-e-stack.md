# Construção de agentes — o que a documentação oficial diz

Esta seção amarra o framework aos guias oficiais de Anthropic, OpenAI e LangChain/LangGraph. Cada bloco diz a fonte e onde ele entra nas cinco etapas.

## Workflow ou agente

A Anthropic separa dois tipos de sistema: **workflows**, em que LLMs e ferramentas são orquestrados por caminhos de código predefinidos, e **agentes**, em que o LLM dirige dinamicamente o próprio processo e o uso de ferramentas. A recomendação é buscar a solução mais simples e só aumentar a complexidade quando necessário; workflows dão previsibilidade em tarefas bem definidas, agentes servem quando é preciso flexibilidade ([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)).

A OpenAI dá três sinais de que um fluxo pede agente em vez de automação determinística: decisão complexa com julgamento e exceções; regras difíceis de manter; forte dependência de dados não estruturados. Sem esses sinais, uma solução determinística pode bastar ([A practical guide to building agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)).

No framework: as cinco etapas com decisão em código são um workflow. Agente entra como peça dentro de um nó (RES5, INV7), não como arquitetura inteira.

## Padrões de composição

Os padrões da Anthropic, com onde cada um aparece nas etapas:

| Padrão | Como funciona | Quando usar, segundo a fonte | Onde entra no framework |
| --- | --- | --- | --- |
| Prompt chaining | Cada chamada processa a saída da anterior, com checagens em código entre os passos | Tarefa que se decompõe em subtarefas fixas | Extrator → decisão → redator; I2 |
| Routing | Classifica a entrada e encaminha para um tratamento especializado | Categorias distintas, classificação confiável; também para mandar o fácil a um modelo menor e o difícil a um maior | N1, I6, escolha de modelo por etapa |
| Parallelization | Subtarefas em paralelo, ou a mesma tarefa várias vezes para votação | Ganho de velocidade, ou mais confiança por várias tentativas | Guardrails em paralelo; duas execuções do extrator em campo de alto risco |
| Orchestrator-workers | Um LLM central divide a tarefa, delega e sintetiza | Subtarefas não previsíveis de antemão | INV7, RES6, RES7 |
| Evaluator-optimizer | Um LLM gera, outro avalia e devolve feedback em laço | Critério de avaliação claro e ganho mensurável com refinamento | RES2: redator mais verificador, com um retry |
| Agente | LLM usando ferramentas em laço, com condição de parada | Problema aberto, número de passos imprevisível | RES5, INV7, com teto de passos |

## Um agente ou vários

A OpenAI recomenda maximizar um agente único antes de dividir, e dá dois critérios para dividir: lógica complexa (prompt cheio de condicionais) e sobrecarga de ferramentas. Sobre ferramentas, o problema não é só a quantidade, e sim a semelhança: há implementações que lidam bem com mais de 15 ferramentas distintas e outras que sofrem com menos de 10 sobrepostas. Dois padrões multiagente: **gerente** (agentes como ferramentas de um agente central, que mantém o controle e fala com o usuário) e **descentralizado** (agentes passam o controle entre si por handoff).

A documentação do LangChain lista cinco padrões ([Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent/index)):

| Padrão | Como funciona | Encaixa quando |
| --- | --- | --- |
| Subagents | Agente principal chama subagentes como ferramentas; eles não falam com o usuário | Domínios distintos, controle central, isolamento de contexto, execução em paralelo |
| Handoffs | Agentes transferem o controle entre si, com estado | Atendimento em que o especialista assume e conversa direto com o usuário |
| Skills | Um agente só, que carrega instruções e conhecimento sob demanda | Muitas especialidades, um único interlocutor |
| Router | Um passo de classificação que despacha, sem manter estado de conversa | Consulta a várias fontes em paralelo e síntese |
| Custom workflow | Fluxo próprio em LangGraph, misturando lógica determinística e agentes | Os padrões prontos não servem; é o caso deste framework |

A mesma página compara custo: em tarefa única, handoffs, skills e router gastam uma chamada de modelo a menos que subagents; em pedidos repetidos, os padrões com estado economizam de 40% a 50% das chamadas; em tarefa multidomínio, os que rodam em paralelo são os mais eficientes. São números dos exemplos da documentação, não medições do seu caso.

No framework: Transferir entre setores humanos é TR4. Handoff entre agentes é TR5, e só se justifica pelos dois critérios da OpenAI.

## Escolha de modelo por etapa

Nenhum modelo é fixo no framework. Cada papel tem um modelo escolhido por comparação, e o canvas registra o escolhido e o candidato.

O método da OpenAI: montar o protótipo com o modelo mais capaz em todas as tarefas para estabelecer a linha de base; depois trocar por modelos menores e ver se o resultado continua aceitável. Em resumo: evals para a linha de base, atingir a meta de acerto com o melhor modelo, otimizar custo e latência substituindo por menores onde der. A mesma fonte nota que nem toda tarefa precisa do modelo mais inteligente: recuperação simples ou classificação de intenção pode ir para um modelo menor e mais rápido.

| Papel | O que o modelo precisa fazer bem | Como comparar candidatos |
| --- | --- | --- |
| Extrator | Seguir schema, ler contexto multi-turno, abster-se | Suíte do extrator por slice; custo e latência por turno |
| Redator | Naturalidade na voz da persona sem sair dos fatos do ato | Afirmações sem suporte, taxa de retry e de escape |
| Juiz | Concordar com o rótulo humano; ser outro modelo que não o redator | Concordância com amostra rotulada à mão |
| Agente de investigação | Escolher ferramenta e argumentos, saber parar | Acerto de ferramenta e argumentos, número de passos |
| Guardrail | Classificação rápida e barata | Precisão e recall no conjunto de entradas indevidas |

Regras: comparar sempre no mesmo gold set e por diferença pareada; fixar a versão exata do modelo, não o apelido; rodar a regressão quando o provedor atualizar; registrar a troca como ADR.

### Providers e faixas de modelo

O framework trabalha com três providers e deixa espaço para testar outros. Cada provider tem faixas, e a comparação é entre faixas, não entre marcas.

Preços em US\\$ por milhão de tokens (entrada / saída), conferidos em 12/11/2026.

| Provider | Barata | Intermediária | Teto: só com ganho medido ou fora do turno | Fora do orçamento de atendimento | Situação no framework |
| --- | --- | --- | --- | --- | --- |
| Anthropic | Haiku 5.5 (0,10 / 0,50) | — | Sonnet 5.5 (2 / 10) | Opus 5.5, Fable 5.2 | Em uso (Haiku 4.5); linha 5.5 verificada |
| Google | Gemini 3.5 Flash-Lite (0,30 / 2,50) | Gemini 3.6 Flash (1,50 / 7,50); Gemini 3.8 Flash (0,75 / 3,75 até 31/12/2026, depois 1,50 / 7,50) | — | Gemini 4 Argon | Em uso (2.5 Flash, deprecado); linha 3.x verificada |
| OpenAI | GPT 6 Luna (0,10 / 0,50) | GPT 6.1 Terra (1 / 5) | GPT 6.1 Sol (2 / 10) | GPT 6 Astra | Em uso (Luna e 5.4 mini); linha 6 e 6.1 verificada |
| xAI (Grok) | — | Grok 4.3 e Grok 4.20 (1,25 / 2,50) | Grok 4.7 (2 / 6) | — | Nunca usado; levantamento abaixo; entra só depois de skill e teste |

**Teto de custo.** Atendimento em volume não paga modelo de topo. As faixas barata e intermediária são o padrão de todo papel que roda a cada turno. A coluna "teto" entra num papel de turno só com ganho pareado medido que pague o custo, ou fora do turno (juiz da suíte, rotulagem, etapa rara). A coluna "fora do orçamento" não entra no canvas de atendimento.

Versões e preços conferidos em 12/11/2026 nas páginas oficiais; estão nas skills de cada família. Os preços introdutórios do Gemini 3.8 (até 31/12/2026) e do Argon (até 30/11/2026) têm data de fim. A regra continua: na Etapa 0 de cada projeto, reconferir a página de modelos e anotar versão e data no canvas.

### Levantamento: xAI Grok (consultado em 12/11/2026)

O que a [página oficial de modelos](https://docs.x.ai/developers/models) diz, lida na íntegra:

- **Um modelo de texto listado:** `grok-4.7`, apresentado como o modelo para código, chat e tudo mais, com "tool calling agêntico, alucinação mínima e raciocínio configurável". Contexto de 500 mil tokens; US$ 2,00 por milhão de entrada e US$ 6,00 por milhão de saída; cutoff maio de 2026.
- **Raciocínio configurável** por `reasoning_effort`, como na OpenAI; página própria de reasoning e de structured outputs.
- **Sem acesso a eventos atuais** sem ligar as ferramentas de busca do servidor (Web Search e X Search).
- **Aliases:** `nome` aponta para a versão estável, `nome-latest` para a mais nova e `nome-data` fixa uma versão. Para produção vale a regra do framework: fixar a versão datada.
- **Chat Completions é legado;** a documentação orienta migrar para a Responses API. Pelo OpenRouter, confirmar qual caminho está exposto.
- **logprobs** não são suportados do 4.20 em diante.
- Tem API de voz (speech-to-text em lote e streaming), cache de prompt, batch e endpoint regional nos EUA.

O que vem de terceiros, não confirmado na página oficial: existência de uma variante **Fast** do 4.7 no mesmo modelo, a dobro do preço; modelos anteriores (4.6, 4.3, 4.20) ainda faturáveis com preço menor e contexto de 1 milhão; preço dobrado acima de 200 mil tokens de prompt.

Leitura para o framework:

| Papel | Hipótese | Por quê |
| --- | --- | --- |
| Extrator ou guardrail | Pouco provável | Sem faixa barata oficial, o 4.7 custa mais que as faixas rápidas dos três providers em uso |
| Redator | A testar | É a fama do Grok em conversação; nenhuma medição em português encontrada |
| Juiz | A testar | Modelo de outro provider para não julgar a própria família |

Antes de qualquer comparação: escrever a Skill Grok 4.7 no padrão das outras, a partir das páginas de reasoning, structured outputs, function calling, prompt caching e best practices da própria xAI. Sem a skill, ele não entra no canvas.

**Correção de 12/11/2026 sobre o Grok:** a tabela de preços da página oficial de modelos da xAI lista, além do 4.7, o `grok-4.3` e as variantes `grok-4.20` (com e sem raciocínio) a US$ 1,25 de entrada, US$ 0,20 de cache e US\\$ 2,50 de saída, com contexto de 1 milhão; acima de 200 mil tokens de prompt o preço dobra. Isso coloca o Grok na faixa intermediária, com saída mais barata que o Terra. A leitura "pouco provável como extrator" acima vale só para o 4.7. Resumos de terceiros citam Batch com 20% de desconto apenas no 4.3 e no 4.20.

### Outros providers: Qwen, Kimi e DeepSeek (levantamento)

O framework não fica preso a três providers. Levantamento de 12/11/2026 em comparativos de terceiros, coerentes entre si; as páginas oficiais ainda não foram abertas. US\\$ por milhão (entrada / cache / saída):

| Provider | Barata | Intermediária | Topo (fora do orçamento) | Observação |
| --- | --- | --- | --- | --- |
| Alibaba (Qwen) | Qwen3.8 Flash (0,15 / 0,016 / 0,47), contexto de 1M | Qwen Plus (0,40 / — / 1,20) | Qwen3.8 Max (2 / 0,25 / 6) | Endpoint internacional em Singapura; existe o Qwen3.7 Flash ainda mais barato até 32 mil tokens |
| Moonshot (Kimi) | — | Kimi K2.6 (0,95 / 0,16 / 4), contexto de 256K | Kimi K3.1 Pro (2 / 0,20 / 10); K3 (3 / 15) | Pesos abertos na linha K2 |
| DeepSeek | `deepseek-flash`, V4.1 Flash: fora do pico 0,15 / 0,003 / 0,60; no pico 0,30 / 0,006 / 1,20 | `deepseek-v4-pro`: fora do pico 0,66 / 1,98; no pico 1,32 / 3,96 | — | Preço muda pelo horário de Pequim; cache quase gratuito |

O que pesa antes de testar:

- **LGPD e transferência internacional.** Chamar a API direta da DeepSeek, da Moonshot ou da Alibaba envia a conversa (dado pessoal) para servidores na China ou em Singapura. Isso precisa constar na lista de operadores e no mecanismo de transferência (Matriz, seção P) e ser aceito pelo cliente.
- **Alternativa:** os modelos de pesos abertos (linha Qwen, Kimi K2, DeepSeek) são servidos por provedores nos EUA via OpenRouter. Pelo OpenRouter, fixar o provedor de hospedagem e conferir a política de dados de cada um; o preço muda por provedor.
- **Qualidade em português** não foi medida em nenhum deles. Entra no mesmo gold set que os outros.
- **Skill antes do canvas:** nenhum deles entra sem a skill no padrão (parâmetros, structured output, function calling, cache, onde está hospedado).

### Onde cada modelo entra no framework

A skill de cada modelo diz como ele funciona e como montar o prompt. Esta tabela diz onde ele entra aqui, e é atualizada a cada skill nova. Toda linha é hipótese até a comparação no gold set do projeto.

| Modelo | Papéis candidatos | Effort de partida | Comparar com | O que pesa na escolha |
| --- | --- | --- | --- | --- |
| GPT 6.1 Terra | Extrator com muitos campos e correções; redator quando o Luna escreve duro; leitura de imagem na Entrada (M3); juiz da suíte | `low` no extrator e na imagem; `none` no redator; `medium` no juiz, pela Batch | Haiku 5.5 `high`, Luna, Gemini 3.6 Flash | Custa 10× o Luna por token. Nó com ferramenta exige Responses API: no formato Chat Completions (n8n ou OpenRouter), só sem ferramenta; com ferramenta, chamar direto na OpenAI a partir do serviço próprio ou testar a API de formato Responses do OpenRouter. Usar só quando o Luna falha por capacidade, não por orientação (descrição de catálogo, regra mal escrita) |
| Qwen3.8 Flash | Classificador e extrator simples; verificador de outra família; imagem e vídeo na Entrada (M3) | raciocínio desligado | Luna `none`, Haiku 5.5 `low`, Gemini 3.5 Flash-Lite | Preço parecido com Luna e Haiku; só vale um provedor a mais se ganhar no gold set em português. Escopo US ou EU obrigatório com dado pessoal; Alibaba Cloud entra na lista de operadores e de transferência internacional (Matriz, seção P). O Omni Flash, mesmo preço, é candidato para áudio (M2) |

### Como montar a combinação

A pergunta não é "qual o melhor modelo", e sim "qual modelo para qual papel neste fluxo". Um agente pode usar três modelos diferentes.

| Sinal do fluxo | Hipótese de partida | O que confirma |
| --- | --- | --- |
| Fluxo simples: poucas intenções, poucos campos | Extrator na faixa rápida | Suíte do extrator dentro da meta nos slices críticos |
| Fluxo complexo: muitos campos, correções, vários assuntos | Extrator na faixa intermediária ou mais capaz | Ganho pareado sobre a faixa rápida que pague o custo |
| Redação com persona marcada | Redator escolhido por naturalidade, não por raciocínio | Menos retry e escape, sem afirmação fora do ato |
| Verificação e juiz | Modelo diferente do que redigiu | Concordância com rótulo humano |
| Prompt fixo grande e alto volume | Qualquer faixa, com cache de prompt | Custo por turno com e sem cache |

Composição em uso hoje, registrada como hipótese e não como regra: extrator na linha GPT-5.4 mini em fluxos de baixa dificuldade; Haiku a testar como extrator em fluxos com mais estrutura; redator em GPT-6 Luna; verificadores em outro modelo. Cada uma dessas escolhas precisa da comparação acima para virar decisão.

Candidatos para a primeira rodada de comparação, com base no que foi verificado em 12/11/2026 (hipóteses, não decisões): extrator simples entre Haiku 5.5 em `low`, GPT 6 Luna em `low` e Gemini 3.5 Flash-Lite; extrator complexo entre Haiku 5.5 em `high`, GPT 6.1 Terra em `low` e Gemini 3.8 Flash em `low`; redator entre GPT 6 Luna, GPT 6.1 Terra em `none` e Gemini 3.6 Flash; verificador de turno entre Haiku 5.5 em `low` e Gemini 3.5 Flash-Lite, sempre de família diferente da do redator; juiz da suíte entre GPT 6.1 Terra, GPT 6.1 Sol e Sonnet 5.5, fora do turno. Grok 4.3, Qwen3.8 Flash e DeepSeek V4.1 Flash entram na segunda rodada, depois das skills.

### Comparação, preços e combinações por tipo de fluxo

> 🧮 O detalhe completo fica no documento de comparação de modelos: preços de todos os modelos, características lidas nas skills (raciocínio, ferramentas, escrita, alucinação, latência, região), custo por papel e combinações para fluxo leve, médio, pesado, conversacional e multimodal. Ela substitui as tabelas de esforço e de combinações que estavam aqui.

### Combinações de referência — versão anterior, substituída pela subpágina acima (apagar após aprovação)

Premissas antigas: extrator 6 mil de entrada e mil de saída; redator 3 mil e 250; verificador 2 mil e 100.

| Combinação | Extrator | Redator | Verificador | Por turno | Por 10 mil turnos |
| --- | --- | --- | --- | --- | --- |
| A. Econômica | Haiku 5.5 `medium` | GPT 6 Luna | Gemini 3.5 Flash-Lite | \\~US\\$ 0,0015 | \\~US\\$ 15 |
| B. Econômica com extrator forte | Haiku 5.5 `high` | GPT 6 Luna | Haiku 5.5 `low` | \\~US\\$ 0,002 | \\~US\\$ 20 |
| C. Extrator intermediário | GPT 6.1 Terra `low` | GPT 6 Luna | Haiku 5.5 `low` | \\~US\\$ 0,0066 | \\~US\\$ 66 |
| D. Extrator e redator intermediários | GPT 6.1 Terra `low` | GPT 6.1 Terra `none` | Haiku 5.5 `low` | \\~US\\$ 0,0082 | \\~US\\$ 82 |
| E. Google intermediário (preço de 2027; cache do 3.8 estimado em 10% da entrada) | Gemini 3.8 Flash `low` | GPT 6 Luna | Haiku 5.5 `low` | \\~US\\$ 0,010 | \\~US\\$ 101 |

Regra de subida: começa na A ou B; só sobe para C, D ou E se a comparação pareada mostrar ganho no slice que importa, registrado em ADR com o custo por turno medido.

### Cache de prompt

Os três providers têm cache de prompt, com regras diferentes de tamanho mínimo, duração e ativação. O que vale para todos: conteúdo estável primeiro (instruções, definição de campos, glossário, exemplos) e conteúdo do turno por último. Antes de trocar para um modelo maior por qualidade, meça o custo dele com cache; a diferença de preço pode cair bastante. A skill `mp-prompt-caching` cobre os detalhes por provider.

### Skill por modelo

Um modelo só entra como candidato no canvas depois de ter uma skill no repositório de skills do projeto, no padrão das que já existem.

| Skill existente | Cobre | Situação |
| --- | --- | --- |
| Skill GPT 4.1 mini | Modelo que sai da API em 14/01/2027 | Manter até a última migração |
| Skill GPT 5.4 mini | Blocos XML, structured outputs, effort, merge de null | Histórica: duas gerações atrás; as técnicas de prompt continuam a base |
| Skill GPT 6 Luna | Substituto do 4.1 mini; effort padrão medium, cache cobrado na escrita | Em uso como redator; preço atual US\\$ 0,10/0,50 |
| Skill GPT 6.1 Terra | Faixa intermediária da OpenAI; extrator complexo, redator alternativo, imagem | Nova, 12/11/2026 |
| Skill GPT 6.1 Sol | Teto da OpenAI; juiz da suíte, fora do turno | Nova, 12/11/2026 |
| Skill Gemini 2.5 Flash | Formato, anti-alucinação, anti-exemplos | Histórica: regras de parâmetros mudaram na família 3.x |
| Skill Gemini 3.8 Flash | Faixa intermediária do Google; regras da família 3.x | Nova, 12/11/2026 |
| Skill Gemini 3.6 Flash | Faixa intermediária do Google; redator e extrator N2 | Nova, 12/11/2026 |
| Skill Gemini 3.5 Flash-Lite | Faixa barata do Google; classificador, extrator N1, verificador | Nova, 12/11/2026 |
| Skill Haiku 4.5 | Família Claude 4.5, XML, prefilled descontinuado | Histórica; prompts migram sem mudança para 5.5 |
| Skill Haiku 5.5 | Effort, JSON com ferramentas, injeção, recusas | Nova, 12/11/2026; candidato a extrator e verificador |
| Skill Claude Sonnet 5.5 | Juiz com JSON, between\\_tools, recusas | Nova, 12/11/2026; teto: juiz da suíte, fora do turno |
| Skill Qwen3.8 Flash | Região e escopo, raciocínio desligado, structured output, cache | Nova, 12/11/2026 |
| Skills Grok 4.3, DeepSeek V4.1 Flash, Kimi K2.6 | Raciocínio, JSON, ferramentas, cache e hospedagem de cada provedor | Novas, 12/11/2026 |
| Skill Prompt Caching | Cache nos três providers | Transversal; precisa de atualização: escrita cobrada na OpenAI, 512 tokens mínimos no Haiku 5.5, Argon só implícito |

As skills novas têm as seções "comportamento observado" e "exemplo medido" vazias: elas são preenchidas depois do primeiro uso real.

O padrão das skills, extraído da Skill GPT 6 Luna, que é a mais completa:

1. **Cabeçalho:** model string direta e no OpenRouter, lançamento, contexto, cutoff, entradas e saídas, preço, o que substitui, data da última verificação.
2. **Aviso de fonte:** tabela com cada fonte, o que cobre e o status; convenção de marcação por linha (`[doc]`, `[OR]`, `[prática]`, `[verificar]`, `[medido]`).
3. **Anatomia da chamada:** o que o código monta, o que o modelo faz, o que o código confere; ordem dos blocos e o que vai ao cache.
4. **Esqueletos anotados:** um para bot conversacional, um para classificador ou extrator, com o para-que de cada bloco.
5. **A chamada completa** em JSON, com o que fica de fora de propósito.
6. **Exemplo real medido** em um cliente, com tokens, latência e custo.
7. **Seções por parâmetro:** o que muda em relação ao modelo anterior, effort, parâmetros que saem, formato do prompt, verbosidade, tool calling, structured outputs, cache, variações (pro, latest), migração passo a passo, few-shot, armadilhas.
8. **Checklist antes de deploy** e **referência rápida**.
9. **Comportamento observado:** pesquisa datada, com nível de confiança por item (alta, média, baixa, medido).
10. **Skills complementares e fontes.**

Sem a skill, o modelo é testado com o prompt escrito para outro, e a comparação fica injusta.

## Runtime, framework ou harness

A documentação do LangChain separa três camadas ([Runtimes, frameworks, and harnesses](https://docs.langchain.com/oss/python/concepts/products.md)):

| Camada | O que entrega | Quando usar | Exemplos citados |
| --- | --- | --- | --- |
| Runtime | Execução durável, streaming, humano no circuito, persistência | Controle de baixo nível; workflows e agentes longos e com estado; mistura de passos determinísticos e agênticos | LangGraph, Temporal, Inngest |
| Framework | Abstrações e integrações: modelos, ferramentas, laço de agente, middleware | Começar rápido; padronizar como o time constrói | LangChain, OpenAI Agents SDK, Vercel AI SDK, Google ADK |
| Harness | Ferramentas, prompts e subagentes prontos; planejamento e sistema de arquivos | Agentes mais autônomos, tarefas longas e não determinísticas | Deep Agents SDK, Claude Agent SDK |

O LangChain 1.0 é construído sobre o LangGraph. Para um agente de atendimento com decisão em código, a camada que importa é o runtime; o harness serve mais ao agente de código que constrói o projeto do que ao agente de atendimento.

Um orquestrador visual como o n8n cumpre o papel de runtime para fluxo linear. O que ele precisa garantir, de um jeito ou de outro, são as capacidades da linha "Runtime": estado persistido por conversa, retomada depois de pausa e reexecução segura.

## Primitivas do LangGraph e onde entram

| Primitiva | O que a documentação diz | Onde entra no framework |
| --- | --- | --- |
| Estado, nós e arestas | O workflow é um grafo de estado compartilhado, nós e arestas, com ramos condicionais e laços | Cada etapa é um nó; a decisão é uma aresta condicional |
| Checkpointer e `thread_id` | Com checkpointer, o estado é salvo a cada passo e organizado em threads; o `thread_id` é a chave para salvar e retomar | Uma thread por conversa; base do estado conversacional |
| Execução durável | O processo salva o progresso e retoma de onde parou, mesmo depois de falha ou de muito tempo; efeitos colaterais e operações não determinísticas ficam dentro de tarefas ou nós | RES8, protocolo de entrega |
| Modos de durabilidade | `exit`, `async` e `sync`, do menos ao mais durável, com custo de desempenho crescente | `sync` antes de ação com efeito externo |
| Interrupts | `interrupt()` pausa em qualquer ponto, salva o estado e espera indefinidamente; retoma com `Command(resume=...)` na mesma thread | TR3, ESC4, aprovação de ação |
| Stores | Memória de longo prazo entre threads, complementar ao checkpointer | Memória entre conversas |
| Subgrafos | Um grafo como nó de outro | Agente de investigação dentro de Investigar |
| Tolerância a falhas | Timeout, retry e tratamento de erro por nó | Conectores e ferramentas |

Fontes: [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence), [Durable execution](https://docs.langchain.com/oss/python/durable-execution), [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts.md).

Regras dos interrupts que afetam o desenho de Transferir e Esclarecer:

- Precisa de checkpointer persistente e de `thread_id`.
- Ao retomar, o nó recomeça do início: todo código antes do `interrupt()` roda de novo.
- Efeito colateral antes do `interrupt()` tem de ser idempotente, ou ficar depois dele, ou em outro nó.
- Não envolver `interrupt()` em `try/except` genérico, não reordenar nem pular interrupts dentro do nó.
- O valor passado tem de ser serializável em JSON.
- Para validar a resposta humana, um interrupt por execução do nó e aresta condicional para voltar; nunca laço dentro do nó.
- Interrupts estáticos (antes ou depois de um nó) são para depuração, não para humano no circuito.

## Desenho de ferramentas

A Anthropic trata ferramenta como contrato entre sistema determinístico e agente não determinístico, e dá cinco princípios ([Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)):

1. **Escolher quais ferramentas implementar, e quais não.** Não embrulhar cada endpoint; construir para a tarefa.
2. **Namespacing.** Nomes que delimitam claramente o que cada ferramenta faz.
3. **Devolver contexto com significado.** Campos úteis ao agente, não identificadores opacos.
4. **Eficiência de tokens na resposta.** Paginação, filtro e formato conciso ou detalhado.
5. **Engenharia de prompt na descrição e na especificação.** Descrever como se explicaria a um colega novo; mensagens de erro que dizem como corrigir.

A mesma fonte recomenda avaliar ferramentas com tarefas reais e medir, além do acerto, tempo de execução, número de chamadas, consumo de tokens e erros de ferramenta.

A OpenAI classifica ferramentas em três tipos (dados, ação e orquestração) e recomenda dar a cada uma uma nota de risco (baixo, médio, alto) conforme leitura ou escrita, reversibilidade, permissões e impacto financeiro, usando a nota para disparar checagem ou escalar para humano.

No framework: ferramenta de dados é Investigar; ferramenta de ação é RES8; a nota de risco é o campo de risco do contrato de ação.

## Instruções

Boas práticas da OpenAI para instruções de agente: partir de documentos que já existem (procedimentos, scripts de suporte, políticas); quebrar em passos pequenos e claros; fazer cada passo corresponder a uma ação ou saída específica; capturar casos de borda com passos condicionais. Para não multiplicar prompts, um prompt base com variáveis de política em vez de um prompt por caso de uso.

No framework: os documentos do cliente entram pelo mapa de dados; as variáveis de política são o que separa conduta universal de persona e de regra do cliente.

## Guardrails e intervenção humana

A OpenAI trata guardrails como defesa em camadas: um só raramente basta. Tipos listados: classificador de relevância, classificador de segurança (jailbreak e injeção), filtro de dados pessoais, moderação, salvaguardas por ferramenta, proteções por regra (lista de bloqueio, limite de tamanho, regex) e validação de saída. Heurística: começar por privacidade e segurança de conteúdo, acrescentar guardrails a partir das falhas reais, e ajustar para não prejudicar a experiência.

Dois gatilhos para intervenção humana, segundo a mesma fonte: **exceder limites de falha** (por exemplo, não entender a intenção depois de várias tentativas) e **ações de alto risco** (sensíveis, irreversíveis ou de alto valor), até a confiança no agente crescer.

No framework: os dois gatilhos são gatilhos obrigatórios de Transferir (TR1); guardrails de entrada rodam antes do extrator e os de saída são o verificador do redator.

# Stack — fichas por família

Fase 4 do ciclo de vida. Cada família tem uma tabela de comparação e fichas das peças mais prováveis. Toda escolha de stack vira ADR. As fichas resumem a documentação oficial consultada em 23/11/2026; antes de adotar uma peça pela primeira vez, abra a documentação na versão que vai instalar.

A família de modelos (providers e faixas) está em "Escolha de modelo por etapa". Runtime, framework e harness estão em "Runtime, framework ou harness". Hospedagem está em "Deploy". Monitoramento está em "Monitoramento em produção".

## Stack padrão MP (proposta para o ADR)

| Camada | Padrão | Alternativa | Quando trocar |
| --- | --- | --- | --- |
| Linguagem | Python | TypeScript | Equipe ou cliente exige TS |
| API e webhook | FastAPI | — | — |
| Runtime do turno | LangGraph | Microsoft Agent Framework | Cliente em Azure ou deploy em Foundry hosted agents |
| Componentes de modelo e ferramenta | LangChain 1.x | SDK do provedor direto | Uma só chamada estruturada, sem laço |
| Recuperação | Código próprio sobre pgvector | LlamaIndex | Documentos complexos (PDF com tabela, OCR) ou muitas fontes |
| Banco de vetores | pgvector (Supabase ou Postgres gerenciado) | Pinecone | Ver "Banco de vetores" |
| Estado e histórico | Postgres gerenciado na nuvem do runtime (Managed PostgreSQL da DigitalOcean na App Platform) | Supabase | App com login, storage ou realtime; ver "Banco de dados — onde fica" |
| Buffer, trava, cache, fila | Valkey ou Redis | — | — |
| Guardrails | Código + middleware do LangChain | NeMo Guardrails, Azure AI Content Safety | Política de conteúdo complexa ou cliente em Azure |
| Observabilidade | Langfuse (plano conforme a classe de risco) | LangSmith ou Phoenix; Grafana para infraestrutura | Ver "Observabilidade por classe de risco e custo" |
| Hospedagem | n8n: Droplet (VPS). Serviço próprio: DigitalOcean App Platform | Azure Container Apps ou AWS ECS Express Mode | Ver "Deploy" |

O padrão existe para que cada agente novo não reabra todas as decisões. Trocar uma linha é permitido, com ADR.

## Frameworks de agente

### Comparação

| Framework | Abstração central | Estado durável e humano no circuito | Multiagente | Linguagens | Encaixe no framework |
| --- | --- | --- | --- | --- | --- |
| LangChain 1.x | `create_agent` com middleware | Via LangGraph (checkpointer) | Via LangGraph | Python, JS/TS | Componentes, laço simples de ferramenta, guardrails por middleware |
| LangGraph | Grafo de estado, nós e arestas | Checkpointer, interrupt, execução durável | Subgrafos, supervisor | Python, JS/TS | Runtime padrão do turno |
| Microsoft Agent Framework | Agents e Workflows | Sessões, checkpointing, humano no circuito em workflows | Workflows e A2A | Python, .NET (Go em preview) | Alternativa ao LangGraph quando o destino é Azure |
| CrewAI | Flows e Crews | Estado em Flows; memória unificada | Crews com papéis | Python | Agentes internos de conteúdo e pesquisa |
| LlamaIndex | Índices, query engines, Workflows | Workflows com retomada | Via Workflows | Python, TS | Biblioteca de Investigar |
| Haystack | Pipelines de componentes | Limitado | Agentes | Python | Alternativa ao LlamaIndex em Investigar |

### LangChain 1.x

**O que é.** A camada de componentes e o laço de agente do ecossistema LangChain. `create_agent` monta o laço modelo → ferramenta → modelo e devolve um grafo LangGraph compilado; o middleware não é um runtime à parte, os hooks rodam dentro desse grafo.

**Peças principais.**

- `create_agent(model, tools, middleware, checkpointer)`: o laço de agente.
- Middleware com hooks antes e depois do agente, do modelo e de cada ferramenta (`@before_agent`, `@before_model`, `@after_model`, `@after_agent`).
- Middlewares prontos que importam para o framework:

| Middleware | O que faz | Onde entra |
| --- | --- | --- |
| `PIIMiddleware` | Detecta e-mail, cartão, IP e outros; estratégias redact, mask, hash e block | Guardrail de entrada e de saída |
| `HumanInTheLoopMiddleware` | Pausa antes de uma ferramenta para aprovar, editar ou rejeitar; precisa de checkpointer e `thread_id`; interrupção condicional pelos argumentos a partir da versão 1.3.3 | Ação com efeito, TR3 |
| `SummarizationMiddleware` | Resume o histórico ao passar de um limite de tokens ou de fração da janela | Contexto e custo |
| Limite de chamadas de modelo | Corta o laço depois de N chamadas | Custo e laço infinito |
| Fallback de modelo | Tenta modelos alternativos em sequência | Disponibilidade |

**Quando usar.** Para padronizar integrações de modelo e ferramenta, e para guardrails por middleware dentro de um nó do LangGraph.

**Quando não usar.** Como dono da decisão do turno. `create_agent` deixa o modelo escolher o próximo passo; no atendimento (N1) a decisão fica na função de decisão em código.

Fontes: [LangChain — Middleware](https://docs.langchain.com/oss/python/langchain/middleware), [Prebuilt middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in.md), [Guardrails](https://docs.langchain.com/oss/python/langchain/guardrails.md).

### LangGraph

Ficha completa em "Primitivas do LangGraph e onde entram". Regra de subida: comece com LangChain quando o fluxo for uma chamada com ferramenta e sem pausa; passe para LangGraph quando houver estado durável, laço com fim incerto, pausa para humano ou mais de um caminho de decisão.

### Microsoft Agent Framework

**O que é.** O sucessor de Semantic Kernel e AutoGen, feito pelos mesmos times. Versão 1.0 em abril de 2026. Semantic Kernel e AutoGen ficaram em manutenção: correções e segurança, sem funcionalidade nova. Não entram no catálogo como opção para projeto novo.

**Peças principais.**

| Peça | O que é |
| --- | --- |
| Agents | Agentes que usam LLM, chamam ferramentas e servidores MCP. Provedores: Microsoft Foundry, Azure OpenAI, OpenAI, Anthropic, Ollama e outros |
| Workflows | Fluxos em grafo que ligam agentes e funções, com roteamento tipado, checkpointing e humano no circuito |
| Agent harness | Agente opinativo para tarefas longas: planejamento, lista de tarefas, compactação de contexto, memória |
| Blocos de base | Clientes de modelo, sessão de agente para estado, context providers para memória, middleware, clientes MCP |
| Integrações | A2A, AG-UI, extensão durável, M365 |

**Quando usar agent e quando usar workflow**, segundo a documentação: agent para tarefa aberta ou conversacional, com uso autônomo de ferramenta; workflow para processo com passos definidos e ordem de execução controlada. No framework, o turno de atendimento é workflow.

**Quando usar.** Quando o destino é Azure: hosted agents na Foundry aceitam Agent Framework e LangGraph, e o Agent Framework tem integração nativa com Foundry, Entra ID e OpenTelemetry. Também quando o projeto é .NET.

**Quando não usar.** Em projeto Python fora do Azure, onde LangGraph já cobre o mesmo papel com o ecossistema que o framework usa.

Fontes: [Microsoft Agent Framework — Overview](https://learn.microsoft.com/agent-framework/overview/), [Agent Framework 1.0](https://visualstudiomagazine.com/articles/2026/04/06/microsoft-ships-production-ready-agent-framework-1-0-for-net-and-python.aspx).

### CrewAI

**O que é.** Framework de orquestração com duas peças:

- **Flows**: a espinha da aplicação. Estado persistido entre passos, execução por eventos, condicionais, laços e ramificações.
- **Crews**: times de agentes com papel, objetivo e história (role, goal, backstory) que executam tarefas, em processo sequencial ou hierárquico.

A documentação recomenda começar toda aplicação de produção por um Flow e chamar uma Crew só para a parte que pede colaboração entre agentes.

**Peças que importam.**

| Peça | O que faz |
| --- | --- |
| Task | Unidade de trabalho de um agente, com descrição e saída esperada |
| Task guardrails | Validam e transformam a saída antes da próxima tarefa. Podem ser função Python (determinística) ou descrição em texto (avaliada por LLM). Falhou, a tarefa volta ao agente até `guardrail_max_retries` |
| Memory | Classe única que substitui memória curta, longa, de entidade e externa. Depois de cada tarefa, extrai fatos e guarda; antes da próxima, recupera o relevante |
| Tools | Ferramentas próprias e compatibilidade com ferramentas do LangChain |

**Quando usar.** Agentes internos em lote: pesquisa, criação de conteúdo, análise com vários papéis (pesquisador, redator, revisor).

**Quando não usar.** No turno de atendimento. Crews têm decisão autônoma entre agentes, o que vai contra decisão em código; e um Flow não traz vantagem sobre LangGraph para quem já usa o ecossistema LangChain.

Fontes: [CrewAI — Introduction](https://docs.crewai.com/en/introduction.md), [Tasks](https://docs.crewai.com/en/concepts/tasks), [Memory](https://docs.crewai.com/concepts/memory).

### LlamaIndex

**O que é.** Framework open-source (MIT) para RAG e agentes, da empresa do LlamaParse. É centrado em dados: conectar, indexar e consultar.

**Peças principais.**

| Peça | O que faz | Onde entra |
| --- | --- | --- |
| Data connectors | Carregam documentos e dados de várias fontes | Pipeline de ingestão |
| Indexes e vector stores | Organizam para busca: vetor, palavra-chave, grafo | Índice de Investigar |
| Query engine | Fluxo pergunta → recuperação → resposta com o contexto usado | Investigar |
| Chat engine | Conversa de várias voltas sobre os dados | Pouco útil no framework: o diálogo é nosso |
| Agents e tools | Agentes prontos; `QueryEngineTool` transforma um índice em ferramenta | Ferramenta de leitura chamada pelo LangGraph |
| Workflows | Orquestração por eventos com ramificação, retries e revisão humana | Alternativa de runtime, não usada no turno |
| LlamaParse | Parsing de documento com tabela, gráfico e OCR | Ingestão de manual, contrato, tabela de preço |

**Quando usar.** Em Investigar, quando a base de conhecimento tem documentos difíceis ou muitas fontes, e para montar ingestão rápida. O índice vira ferramenta de leitura do agente.

**Quando não usar.** Como runtime do turno ou como dono do diálogo.

Fontes: [LlamaIndex Framework](https://developers.llamaindex.ai/python/framework/), [Agents](https://developers.llamaindex.ai/python/framework/use_cases/agents/index.md).

## Banco de vetores

| Banco | O que é | Ponto forte | Ponto fraco | Quando escolher |
| --- | --- | --- | --- | --- |
| pgvector (Supabase Vector, Postgres gerenciado da DigitalOcean ou do Azure) | Extensão do Postgres | Vetor junto do dado relacional, mesma SQL, mesmo backup, filtro por tenant com RLS | Exige ajuste de índice HNSW em volume alto | Padrão; menos de 10 milhões de trechos |
| Pinecone | Serviço gerenciado serverless | Nada para operar; namespaces por cliente; busca híbrida, embedding e reranking integrados | Dado sai da sua infraestrutura; custo por leitura cresce com tráfego | Quando não quer operar índice ou quando há muitos clientes com índices separados |
| Qdrant | Banco vetorial em Rust, self-host ou nuvem | Filtro dentro do índice, rápido com filtro pesado | Mais uma peça para operar | Filtro por metadados é crítico |
| Weaviate | Banco vetorial, self-host ou gerenciado (inclusive na DigitalOcean) | Recursos de busca híbrida e módulos | Muitos parâmetros para ajustar | Já gerenciado no provedor de nuvem escolhido |
| Milvus | Banco vetorial distribuído | Escala de bilhões de vetores | Operação pesada | Escala muito acima da MP hoje |
| Chroma | Banco local e simples | Protótipo em minutos | Não é para produção multi-cliente | Experimento local |

### Pinecone, em detalhe

| Ponto | O que a documentação diz |
| --- | --- |
| Modelo | Serverless por uso: paga o dado armazenado e as operações; índice parado não custa |
| Medidores | Unidades de leitura, unidades de escrita, armazenamento e dados devolvidos |
| Planos | Starter grátis (índices só em AWS us-east-1); Builder com valor mensal fixo; Standard e Enterprise com mínimo mensal mais consumo |
| Limite de uso | Starter e Builder bloqueiam ao atingir a cota, em vez de cobrar excedente |
| Namespaces por índice | 100 (Starter), 1.000 (Builder), 100.000 (Standard e Enterprise) |
| Multi-cliente | Um namespace por cliente no mesmo índice |

Regra do framework: pgvector até um sinal medido (latência p95 de busca acima do alvo, filtro por tenant degradando, volume acima de 10 milhões de trechos, ou custo de operar o índice). Pinecone entra com ADR que registre a região dos dados e a avaliação de LGPD, porque o dado pessoal sai da infraestrutura da MP.

Fontes: [Pinecone — Understanding cost](https://docs.pinecone.io/guides/manage-cost/understanding-cost.md), [Object limits](https://docs.pinecone.io/reference/api/database-limits/object-limits.md).

## Memória e estado

O framework separa quatro tipos de estado (ver "Estado"). Cada um tem a sua tecnologia:

| Tipo | Tecnologia padrão | Por quê |
| --- | --- | --- |
| Histórico bruto | Postgres | Auditável e nunca reescrito |
| Estado conversacional | Postgres como fonte; cópia quente em Valkey ou Redis com TTL | Leitura rápida no turno sem perder a fonte de verdade |
| Estado de execução | Postgres (outbox, checkpointer do LangGraph em Postgres) | Precisa sobreviver a falha e ser retomado |
| Memória de longo prazo | Postgres + pgvector | Fatos entre sessões com busca semântica e política de retenção |
| Buffer, trava, deduplicação | Valkey ou Redis | Operação de milissegundos com tempo de vida |

### Redis no lugar do Simple Memory

O Simple Memory do n8n guarda o histórico na memória do processo. Em modo fila, cada execução pode cair em um worker diferente, e a documentação do n8n diz para não usar o nó nesse modo; as alternativas indicadas são Redis Chat Memory e Postgres Chat Memory.

No framework, memória de chat é só a janela do histórico bruto, não o estado. Por isso:

- Em n8n, enquanto houver agente lá: Redis Chat Memory ou Postgres Chat Memory, com a chave de sessão igual ao id da conversa.
- No serviço próprio: o histórico vem do Postgres; o Redis guarda o que é quente e expira.

Outros usos do Redis no agente, além do buffer:

| Uso | Como | Cuidado |
| --- | --- | --- |
| Trava por conversa | `SET key NX PX` com tempo de vida | Soltar a trava no fim; tempo de vida maior que o turno mais longo |
| Deduplicação | Chave com o id da mensagem do provedor | Tempo de vida maior que a janela de reenvio do provedor |
| Estado quente | Hash por conversa com TTL | Postgres continua sendo a fonte; o Redis pode ser apagado sem perda |
| Cache de resposta | Pergunta normalizada → resposta, para FAQ estável | Invalidar quando a fonte muda; nunca para dado pessoal |
| Rate limit | Contador por contato e janela | Responder com mensagem fixa, não com silêncio |
| Fila | Base de Celery, RQ ou arq | Persistência habilitada |

Na DigitalOcean o serviço gerenciado é o Managed Caching for Valkey, compatível com Redis.

### MongoDB

Banco de documentos. Para o framework não acrescenta: o Postgres com JSONB guarda documento flexível, com transação e junto do relacional. Entra só se o cliente já tiver os dados em Mongo, e nesse caso como fonte de Investigar, não como estado do agente.

## Ações e ferramentas

### Classes de ação

| Classe | Exemplo | Quem pode disparar | Confirmação | Idempotência | Se der errado |
| --- | --- | --- | --- | --- | --- |
| Leitura | Consultar agenda, preço, status | LLM (N2) ou código | Não | Não precisa | Repetir |
| Escrita reversível | Pré-reserva, rascunho, atualização de cadastro | Código | Quando altera dado do cliente | Chave obrigatória | Desfazer |
| Escrita irreversível | Cancelar, pagar, emitir | Código, depois de confirmação explícita | Sempre | Chave obrigatória | Compensar e transferir |
| Comunicação externa | Enviar mensagem, e-mail, notificação | Código | Quando é em nome do cliente | Chave obrigatória | Reenvio pela outbox |
| Transferência | Passar para humano | Código (gatilhos TR) | Não | Chave obrigatória | Protocolo de entrega |

### Contrato de uma ferramenta

Toda ferramenta é registrada no Tool Registry do projeto (um arquivo de registro em `src/tools/`, lido pelo agente e pelos testes) e declara:

1. Nome no formato verbo\\_objeto (`consultar_agenda`, `cancelar_consulta`).
2. Descrição com quando usar e quando não usar, porque é o que o modelo lê.
3. Schema estrito de entrada e de saída.
4. Classe de ação e efeito (leitura ou escrita).
5. Erros tipados: repetível ou não repetível.
6. Tempo limite e número de tentativas.
7. Chave de idempotência, se escreve.
8. Credencial com o menor escopo possível.
9. O que é gravado no trace e o que é mascarado.

### Ciclo de execução

```txt
propor (código ou LLM em lista fechada)
  → validar em código: schema, permissão, estado atual, limites
  → confirmar com o cliente, se a classe exigir
  → executar com chave de idempotência e tempo limite
  → verificar o resultado devolvido
  → gravar evento (ação iniciada, ação concluída ou falhou)
  → redigir a resposta a partir do resultado, nunca da intenção
```

Erro repetível tenta de novo com espera crescente. Erro não repetível não repete: compensa o que foi feito e vai para Transferir com o pacote de handoff.

### Como cada framework implementa

| Necessidade | LangChain / LangGraph | Microsoft Agent Framework | CrewAI |
| --- | --- | --- | --- |
| Definir ferramenta | `@tool` com schema | Funções e ferramentas MCP | Tools próprias ou do LangChain |
| Aprovação humana | `HumanInTheLoopMiddleware` ou `interrupt()` | Humano no circuito em workflows | Revisão entre tarefas |
| Validar saída | Middleware `after_model` | Middleware | Task guardrails |
| Retomar depois da pausa | Checkpointer e `thread_id` | Checkpointing de workflow | Estado do Flow |

### MCP, function calling ou API direta

| Forma | O que é | Quando usar |
| --- | --- | --- |
| Function calling | O modelo devolve o nome e os argumentos; o código executa | Padrão para ferramentas do próprio agente |
| MCP | Servidor que expõe ferramentas em protocolo padrão | Ferramenta reaproveitada por vários agentes ou de terceiros, com a revisão de cadeia de suprimentos da Segurança |
| API direta em código | O código chama sem passar pelo modelo | Toda ação decidida pela máquina de decisão (N1) |

## Guardrails

### As cinco camadas

A divisão vem do NeMo Guardrails: entrada, recuperação, diálogo, execução e saída. No framework, cada camada tem lugar fixo:

| Camada | Etapa no framework | O que checa | Determinístico | Por modelo |
| --- | --- | --- | --- | --- |
| Entrada | Entrada, antes do extrator | Dado pessoal, injeção e jailbreak, tamanho, idioma, assunto fora do escopo | Regex, listas, limite de tamanho, Presidio | Classificador de injeção (Prompt Shields), self check |
| Recuperação | 2 Investigar | Fonte autorizada, validade, tenant, instrução escondida em documento | Filtro por tenant e por fonte, data de validade | Detecção de injeção indireta |
| Diálogo | Máquina de decisão | A conduta é permitida neste estado? | Função de decisão em código | — |
| Execução | 3 Resolver | Argumentos, permissão, valor máximo, confirmação | Validação de schema e de política | — |
| Saída | Verificador do redator | Fato sem fonte, promessa proibida, dado pessoal, tom, formato | Regras e regex | Groundedness, juiz LLM |

Regras:

1. Determinístico primeiro. Modelo só onde a regra não alcança.
2. Todo guardrail tem caso na suíte de segurança: um caso que deve bloquear e um que deve passar.
3. Medir o falso positivo (bloqueio indevido) e a latência que o guardrail acrescenta.
4. Guardrail que bloqueia sempre devolve uma conduta: reformular, perguntar ou transferir. Nunca silêncio.

### Ferramentas de guardrail

| Ferramenta | O que oferece | Quando usar |
| --- | --- | --- |
| Código próprio | Regras, schema, política | Sempre; é a primeira camada |
| Middleware do LangChain | PII (redact, mask, hash, block), humano no circuito, limite de chamadas, guardrail próprio por hook | Agente em LangChain ou LangGraph |
| NeMo Guardrails (NVIDIA) | Cinco tipos de rail; diálogo em Colang; integra validadores do Guardrails AI e Presidio para dado pessoal | Política de conteúdo complexa, vários rails configuráveis |
| Guardrails AI | Hub de validadores: dado pessoal, linguagem tóxica, restrição de assunto, menção a concorrente, tamanho | Validação pronta de entrada e de saída |
| Azure AI Content Safety | Quatro categorias de dano (ódio, sexual, violência, automutilação) com limiar; Prompt Shields para injeção direta e indireta; groundedness detection; material protegido; categorias próprias. Treinado também em português | Cliente em Azure, ou quando precisa de classificador gerenciado |
| Amazon Bedrock Guardrails | Filtros de conteúdo, ataque de prompt, tópicos negados, palavras, dado pessoal com máscara, grounding e Automated Reasoning; ApplyGuardrail funciona sem chamar modelo e com modelo fora do Bedrock | Cliente em AWS, ou modelo no Bedrock |
| Guardrails da plataforma de agentes da DigitalOcean | Guardrails configuráveis nos agentes gerenciados | Só se o agente for gerenciado pela própria plataforma |
| Task guardrails do CrewAI | Validação por função ou por LLM entre tarefas | Agentes internos em CrewAI |

Fontes: [NeMo Guardrails — Rail types](https://docs.nvidia.com/nemo/guardrails/about-nemo-guardrails-library/rail-types.md), [GuardrailsAI integration](https://docs.nvidia.com/nemo/guardrails/latest/configure-guardrails/guardrail-catalog/third-party/guardrails-ai), [Azure AI Content Safety](https://azure.microsoft.com/en-us/products/cognitive-services/content-safety).

## Ferramentas de teste

| Ferramenta | Para quê | Situação no framework |
| --- | --- | --- |
| pytest | Suíte de erros, testes de decisão, de ferramenta e de contrato | Padrão |
| Datasets e experimentos do Langfuse ou do LangSmith | Rodar uma versão contra o gold set e comparar | Padrão |
| Ragas | Métricas de recuperação e de RAG | Já no catálogo |
| Simulação de cenários | Usuário simulado por LLM em conversas de várias voltas | Ver "Simulação de cenários" em Evals |
| promptfoo | CLI e biblioteca MIT para evals e red teaming (injeção de prompt, jailbreak, vazamento de dado). Entrou na OpenAI em 2026 e continua open source | Suíte de segurança e red team no CI, a partir do risco moderado |
| TestSprite | Agente de teste autônomo, ligado ao agente de código por MCP ou por CLI (a CLI é open source; o MCP exige chave da TestSprite). Lê o código e o PRD, monta plano e testes de front-end e de API, roda na nuvem da TestSprite e devolve o que falhou para o agente de código corrigir | Plataformas e painéis (Prompt Studio, front-ends em Lovable) e contrato HTTP do serviço do agente (webhook e endpoints). Não avalia a qualidade da conversa e não substitui gold set nem suíte de erros. Rodar só em staging com dado fictício, porque o teste roda fora da infraestrutura da MP |
| DeepEval | Framework de eval | Candidato; não verificado nesta revisão, exige leitura da documentação antes de ADR |

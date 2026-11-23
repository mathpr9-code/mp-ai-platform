# 2. Investigar — código mais recuperação

Investigar é mais amplo que RAG. A escolha começa pela pergunta "onde mora o fato?" e só chega em RAG quando o fato mora em texto grande demais para caber no contexto.

Em fluxo conhecido, o código decide a consulta a partir da saída do extrator, por uma tabela `intencao → fonte`. O LLM só escolhe a consulta quando a sequência depende do resultado anterior, dentro de lista fechada de ferramentas e com limite de passos.

## Escada de escolha

Desça um degrau só quando o atual não atinge o alvo no gold set de recuperação.

| Degrau | Sinal na descoberta | Peça | O que custa |
| --- | --- | --- | --- |
| 0 | Regra simples e estável | Código, tabela de decisão ou configuração versionada, sem busca | Manter a regra atualizada |
| 1 | O fato é um registro atual: pedido, agenda, cadastro | INV1 — SQL ou API | Contrato da fonte, autorização, falha |
| 2 | Base de conhecimento pequena e estável | Base inteira no contexto, com cache | Tokens por chamada |
| 3 | Códigos, nomes e termos exatos | INV2 — lexical (BM25) | Não pega paráfrase |
| 4 | Mesma coisa dita de muitos jeitos | INV3 — vetorial | Vizinho semântico errado |
| 5 | Os dois sinais juntos | INV4 + INV5 — híbrida com reranking | Infraestrutura e parâmetros |
| 6 | Perguntas que cruzam relações ou pedem síntese do corpus | INV10 — GraphRAG | Indexação e manutenção caras |
| 7 | A próxima busca depende da anterior | INV7 — Agentic RAG | Variabilidade, latência, controle |

**CRAG e RAG em grafo de execução.** Corrective RAG (INV8) acrescenta um passo que avalia o que a busca trouxe e, se for ruim, reescreve a consulta ou vai a outra fonte antes de gerar. Isso é um laço com decisão, e por isso costuma ser implementado como grafo no LangGraph: nós para buscar, avaliar, reescrever e gerar, com aresta condicional entre eles. A documentação do LangGraph traz um tutorial de [RAG agêntico customizado](https://docs.langchain.com/oss/python/langgraph/agentic-rag.md) nesse formato. Não confundir: LangGraph é como o fluxo roda; CRAG, Self-RAG e Agentic RAG são o padrão de recuperação; GraphRAG é busca sobre grafo de conhecimento. O catálogo completo está abaixo.

## O que a evidência pública diz

- **Base pequena.** A Anthropic sugere colocar a base inteira no prompt, com cache, quando ela tem menos de cerca de 200 mil tokens ([Contextual Retrieval](https://www.anthropic.com/research/contextual-retrieval)).
- **Híbrida com reranking.** No benchmark deles, a falha de recuperação no top 20 caiu de 5,7% para 3,7% com embeddings contextualizados, 2,9% somando BM25 e 1,9% com reranking (mesma fonte). São domínios deles e medem recuperação, não a resposta final.
- **GraphRAG.** Avaliação controlada concluiu que RAG e GraphRAG são complementares, com RAG mais forte em pergunta factual e de detalhe ([Han et al., 2025](https://arxiv.org/abs/2502.11371v2), preprint). Grafo é peça para um tipo de pergunta, não nível de maturidade.

## Contrato de evidência

Cada resultado carrega: `fonte` e versão, tipo e autoridade da fonte, escopo de acesso, trecho ou registro, momento da consulta, validade e `status` (encontrado, insuficiente, conflito, desatualizado, sem acesso, indisponível). Resolver nunca recebe texto solto.

Governança das fontes: cada tipo de fato tem uma fonte com autoridade, um dono e uma regra de atualização. Divergência entre documento e sistema é registrada como conflito, não resolvida pelo modelo.

## Sintoma → alavanca em Investigar

Meça Investigar separado de Resolver: falha de busca, de leitura e de redação têm consertos diferentes.

| Sintoma | Onde mexer primeiro |
| --- | --- |
| A resposta existe na base e não veio | Recall: chunking, busca lexical, filtros de metadado |
| Veio trecho parecido de outro produto ou unidade | Filtro por metadado antes da busca; reranking |
| Veio o trecho certo e a resposta saiu errada | Não é Investigar: olhar Resolver |
| Dado desatualizado | Fonte errada: era sistema, não documento |

## Catálogo completo de investigação

| Padrão | Funcionamento | Quando considerar | Custos e limites |
| --- | --- | --- | --- |
| INV1 — Acesso direto SQL/API | Código consulta a fonte de verdade por contrato | Dados transacionais, estruturados e atualizados | Exige schema, autorização e tratamento de falhas |
| INV2 — Busca lexical/BM25 | Recupera por termos, expressões e relevância textual | Códigos, nomes, expressões exatas | Sinônimos e paráfrases escapam |
| INV3 — Busca vetorial | Recupera por similaridade semântica | Paráfrases, conceito, vocabulário variado | Traz itens próximos semanticamente, mas factualmente errados |
| INV4 — Busca híbrida | Combina lexical e vetorial, com fusão de ranking | Corpus com termos exatos e linguagem variada | Mais parâmetros, infraestrutura e avaliação |
| INV5 — Recuperação + reranking | Recupera candidatos e reordena com um segundo modelo | Recall bom, mas os primeiros resultados não são os melhores | Custo e latência adicionais |
| INV6 — RAG tradicional (2 passos) | Recupera antes e gera depois, em sequência conhecida | FAQ, políticas, manuais, perguntas recorrentes | Rígido para consultas de múltiplas etapas |
| INV7 — Agentic RAG | Um agente planeja, escolhe ferramentas, repete buscas e decide quando parar | Investigação aberta, fontes heterogêneas, perguntas compostas | Variabilidade, latência, custo e dificuldade de controle |
| INV8 — Corrective RAG | Avalia a qualidade da recuperação e aciona correção ou fontes alternativas | Fontes incompletas, recuperação instável | O avaliador pode errar; o fallback precisa de política |
| INV9 — Self-RAG | Modelo aprende a decidir quando recuperar e a criticar evidências | Cenários com modelo treinado para isso | Não é só um prompt; envolve modelo e avaliação específicos |
| INV10 — GraphRAG | Usa entidades, relações e comunidades de um grafo | Relações entre entidades, perguntas multi-hop, síntese global | Indexação e manutenção caras; nem toda pergunta precisa de grafo |
| INV11 — Multi-query e decomposição | Reescreve ou divide a consulta em buscas menores | Pergunta composta, linguagem vaga, várias facetas | Amplia ruído e multiplica chamadas |
| INV12 — Memória conversacional | Recupera turnos, sessões e evidências históricas | Preferências, compromissos, continuidade entre sessões | Exige temporalidade, atualização e preservação de origem |

## Fichas das peças de RAG

Uma ficha por peça, no mesmo formato: o que é, por que existe, para que serve, quando não usar, o que exige e como medir. A linha "experiência registrada" guarda o que já foi observado na prática e é atualizada a cada projeto; não é regra.

### RAG tradicional em dois passos (INV6)

- **O que é:** uma busca vetorial, os trechos mais parecidos vão para o prompt, o modelo responde.
- **Por que existe:** é a forma mais simples de dar ao modelo um conhecimento que não cabe no prompt.
- **Para que serve:** base única, perguntas diretas, vocabulário do cliente igual ao dos documentos.
- **Quando não usar:** termos exatos (códigos, nomes de produto), perguntas compostas, base com itens parecidos entre si.
- **O que exige:** índice vetorial e estratégia de chunking.
- **Como medir:** recall no top k no gold set de recuperação.
- **Experiência registrada:** só se sustentou em fluxo muito simples. Antes dela, testar a base inteira no contexto.

### RAG híbrido com reranking (INV4 + INV5)

- **O que é:** busca por palavra exata e busca semântica rodam juntas, os resultados são fundidos e um segundo modelo reordena.
- **Por que existe:** a vetorial perde códigos e nomes; a lexical perde paráfrases. Juntas, uma cobre a falha da outra.
- **Para que serve:** catálogo, tabela de preços, manuais, qualquer base com identificadores e linguagem variada. É o candidato padrão quando existe RAG.
- **Quando não usar:** base pequena que cabe no contexto; dado que mora em sistema e muda todo dia.
- **O que exige:** dois índices, fusão de ranking, filtro por metadado, reranker.
- **Como medir:** recall no top k com e sem cada componente, para saber qual deles está pagando o custo.
- **Experiência registrada:** é a peça mais usada até aqui.

### Corrective RAG (INV8)

- **O que é:** depois da busca, um passo avalia se o que veio responde à pergunta. Se não, reescreve a consulta, busca de novo ou vai a outra fonte, e só então gera.
- **Por que existe:** o RAG simples responde com o que veio, mesmo quando veio lixo.
- **Para que serve:** base incompleta ou irregular, em que "não encontrei" precisa ser reconhecido e tratado, em vez de virar resposta inventada.
- **Quando não usar:** quando a busca já atinge o alvo; o passo de avaliação custa uma chamada e tempo.
- **O que exige:** orquestração com laço e teto de tentativas, por isso costuma ser um grafo no LangGraph; um avaliador com critério claro; política para quando nada serve (esclarecer ou transferir).
- **Como medir:** acerto do avaliador contra rótulo humano; taxa de "insuficiente" correta; tentativas por consulta.
- **Experiência registrada:** implementado em LangGraph, é uma das peças em uso recente.

### RAG adaptativo

- **O que é:** um roteador decide, por pergunta, o caminho: sem busca, busca simples ou busca com correção.
- **Por que existe:** nem toda pergunta precisa do caminho mais caro.
- **Para que serve:** volume alto com mistura de perguntas fáceis e difíceis.
- **Quando não usar:** quando o extrator já entrega intenção e a tabela `intencao → fonte` resolve o roteamento em código.
- **O que exige:** classificador ou regra de roteamento e a medição dele.
- **Como medir:** acerto do roteamento; custo médio por consulta.

### Agentic RAG (INV7)

- **O que é:** um agente com ferramentas de busca decide o que consultar, em que ordem e quando parar.
- **Por que existe:** algumas perguntas só se respondem cruzando fontes, e a segunda busca depende da primeira.
- **Para que serve:** investigação aberta sobre fontes heterogêneas.
- **Quando não usar:** atendimento com latência curta e caminho conhecido; a variabilidade dificulta teste e regressão.
- **O que exige:** lista fechada de ferramentas, teto de passos, trace por passo.
- **Como medir:** acerto de ferramenta e argumentos, número de passos, custo por tarefa concluída.
- **Experiência registrada:** nunca usado; entra como candidato só quando CRAG não cobrir o caso.

### Self-RAG (INV9)

- **O que é:** o próprio modelo decide quando buscar e critica o que recuperou e o que gerou.
- **Por que existe:** reduzir busca desnecessária e resposta sem suporte.
- **Quando não usar:** na forma original depende de modelo treinado para isso. Como grafo com passos de autoavaliação, fica próximo do CRAG; escolha o CRAG, que é mais simples de testar.

### GraphRAG (INV10)

- **O que é:** a base vira um grafo de entidades e relações, com resumos por agrupamento; a busca percorre o grafo.
- **Por que existe:** busca por trecho não responde "como A se relaciona com B" nem "quais são os temas deste acervo".
- **Para que serve:** perguntas de múltiplos saltos, relações entre entidades, síntese de acervo grande.
- **Quando não usar:** pergunta factual de detalhe, base pequena, conteúdo que muda toda semana (reindexar é caro).
- **O que exige:** extração de entidades na indexação, armazenamento do grafo, rotina de atualização.
- **Como medir:** acerto em perguntas relacionais contra o híbrido, no mesmo conjunto; custo de indexação.
- **Experiência registrada:** bem avaliado nos projetos em que entrou.

### Como as peças se combinam

As fichas não são exclusivas. O híbrido é a busca; o CRAG é o controle em volta da busca; o grafo é outra fonte que o CRAG pode acionar. Uma montagem comum: híbrido com reranking como busca principal, CRAG avaliando o resultado, e "insuficiente" levando a Esclarecer ou Transferir.

Sobre o LangGraph: o índice atual da documentação lista um tutorial de RAG agêntico customizado. Tutoriais específicos de CRAG, Self-RAG e RAG adaptativo existiam na documentação anterior; confirme se continuam publicados antes de citar o link em um projeto.

### Técnicas que compõem os padrões

- Reescrita e normalização da consulta
- Multi-query e decomposição por subpergunta
- Filtro de metadados por tenant, categoria, validade, idioma e autoridade
- HyDE ou expansão semântica, quando provar ganho no domínio
- BM25 mais busca densa com Reciprocal Rank Fusion
- Reranker cross-encoder ou LLM
- Deduplicação e diversidade de fontes
- Citação de trechos e ids de fonte
- Filtro de atualidade e validade para dados temporais
- Cache com invalidação e escopo explícitos
- Fallback entre fontes aprovadas e registro de indisponibilidade

## Perguntas para escolher o padrão

1. A informação existe em documento, banco, API ou mais de uma fonte?
2. A consulta exige exatidão de identificador ou compreensão semântica?
3. A pergunta é local, multi-hop ou global em relação ao corpus?
4. A resposta depende de relações explícitas?
5. O corpus muda com que frequência?
6. Há exigência de citar a fonte?
7. A falha de recall é pior ou menos danosa que um falso positivo?
8. Qual custo de indexação, manutenção e latência é aceitável?
9. É possível medir a recuperação separadamente da resposta?

RAG não é uma escala de maturidade: GraphRAG não é "melhor que" híbrido, Agentic RAG não é necessariamente melhor que o pipeline de dois passos. O melhor padrão é o mais simples que atende ao conjunto de perguntas com qualidade, custo, governança e manutenção aceitáveis.

## Dimensões de avaliação de Investigar

| Dimensão | Métrica ou checagem |
| --- | --- |
| Recall da fonte | A evidência correta foi recuperada? |
| Precisão e relevância | Os resultados recuperados são pertinentes? |
| Ranking | As evidências mais úteis aparecem primeiro? |
| Cobertura | As subperguntas e os fatos necessários foram cobertos? |
| Atualidade | O resultado estava vigente no momento da consulta? |
| Proveniência | O resultado é rastreável à fonte certa? |
| Permissão | O sistema respeitou escopo e autorização? |
| Conflito | Divergências foram detectadas e representadas? |
| Uso da evidência | Resolver realmente utilizou a evidência recuperada? |
| Custo e latência | Qual o custo por consulta e por tarefa concluída? |

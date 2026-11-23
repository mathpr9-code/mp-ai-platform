# Fundamentos — o que é um agente

Fase 1 do ciclo de vida. Antes de escolher peça, é preciso saber que tipo de sistema está sendo construído e quanta decisão fica com o modelo.

## Definição

Um agente é um sistema em que um modelo de linguagem recebe uma entrada, escolhe entre ações possíveis e age sobre um ambiente por meio de ferramentas, em laço, até cumprir um objetivo ou parar. O que separa um agente de um chatbot é a ação: ele consulta, grava, agenda, envia e transfere, em vez de só responder com texto.

Neste framework a definição tem uma restrição de propósito: o LLM lê e redige, o código decide e executa. A seção "Workflow ou agente", mais abaixo, traz a distinção da documentação oficial.

## Como funciona

Todo agente roda o mesmo laço de quatro tempos. No framework, cada tempo tem um lugar fixo:

| Tempo | O que acontece | Onde fica no framework |
| --- | --- | --- |
| Perceber | Receber a mensagem e entender o que ela quer dizer | Entrada e 1 Interpretar |
| Decidir | Escolher a próxima conduta | Máquina de decisão em código |
| Agir | Consultar, executar, perguntar ou transferir | 2 Investigar, 3 Resolver, 4 Esclarecer, 5 Transferir |
| Observar | Registrar o resultado e atualizar o estado | Estado por evento e tracing |

## Agente, chatbot e workflow

|  | Chatbot | Workflow com LLM | Agente |
| --- | --- | --- | --- |
| Quem decide o próximo passo | Ninguém: responde e para | O código, com passos fixos | O LLM, dentro de limites |
| Age no mundo | Não | Sim, nos pontos previstos | Sim, escolhendo a ferramenta |
| Estado entre turnos | Histórico de mensagens | Estado explícito | Estado explícito e memória |
| Previsibilidade | Alta, porque faz pouco | Alta | Menor; exige eval e guardrail |
| Exemplo | FAQ que só responde | Bot de triagem com menu e transferência | Agente de pesquisa que decide onde buscar |

Os agentes de atendimento da MP são **workflows agênticos**: o LLM interpreta e redige, e a decisão é código. Autonomia do modelo entra onde ela paga o risco, normalmente dentro de Investigar.

## Características

1. **Objetivo explícito.** Sem objetivo mensurável, não há como saber se o agente funcionou.
2. **Autonomia limitada.** O nível de autonomia é uma escolha de desenho, registrada no canvas.
3. **Uso de ferramentas.** Cada ferramenta tem contrato, permissão e teste.
4. **Estado.** O agente sabe em que ponto da conversa e do processo está.
5. **Adaptação ao resultado.** O passo seguinte depende do que a ação devolveu.
6. **Observabilidade.** Cada passo deixa rastro, senão não há como corrigir.

## Tipos de agente por arquitetura

| Tipo | Como decide | Quando usar no framework |
| --- | --- | --- |
| Reativo por regra | Regras fixas sobre a entrada | Triagem, menus, gatilhos simples |
| Workflow agêntico | LLM interpreta; código decide | Padrão de atendimento (N1) |
| Roteador | LLM ou classificador escolhe o subfluxo | Vários domínios no mesmo número |
| ReAct (raciocinar e agir) | LLM alterna raciocínio e chamada de ferramenta | Investigar com fontes variadas (N2) |
| Planejador-executor | LLM planeja passos; executor roda cada um | Pesquisa, análise de dados, conteúdo (N3) |
| Multiagente com supervisor | Um agente distribui tarefas para especialistas | Domínios muito distintos; ver "Um agente ou vários" |

Os tipos por função (atendimento, funcionário, criação, código, dados, segurança) estão em "Casos de uso".

## Escala de autonomia

| Nível | Quem decide | Exemplo | Exigências mínimas |
| --- | --- | --- | --- |
| N0 | Só código; LLM ausente ou só redige texto fixo | Menu de opções | Testes de fluxo |
| N1 | LLM interpreta e redige; código decide toda conduta | Agendamento em clínica | Suíte do extrator, verificador, suíte de erros |
| N2 | LLM escolhe ferramenta dentro de uma lista fechada e sem efeito irreversível | Investigar escolhe entre agenda, catálogo e base de conhecimento | Tool gold set, limite de chamadas, trace por ferramenta |
| N3 | LLM planeja vários passos; ação com efeito passa por aprovação | Agente interno que monta relatório e pede revisão | Humano no circuito, checkpointer, orçamento de custo por execução |
| N4 | LLM planeja e executa sem aprovação | Agente de código em sandbox | Sandbox isolado, sem segredo, sem saída de dados |

Regras:

- Atendimento ao cliente final começa em N1. N2 só dentro de Investigar.
- Subir um nível exige eval que mostre o teto do nível atual e guardrails para a superfície nova.
- Ação irreversível nunca fica abaixo de aprovação, qualquer que seja o nível.

## Planejamento é uma decisão explícita

No atendimento, o plano é a máquina de decisão em código. O LLM não planeja a conversa; ele interpreta a fala e redige a resposta. Esta escolha é deliberada: um plano gerado a cada turno muda de execução para execução, e o que muda não pode ser testado com a suíte de erros.

Planejamento por LLM é permitido em três lugares: busca autônoma dentro de Investigar (Agentic RAG), agentes internos de pesquisa, dados ou conteúdo, e agentes de código. Nos três casos, com limite de passos e de custo.

## Os componentes e onde moram

| Componente | O que é | Onde está neste documento |
| --- | --- | --- |
| LLM (cérebro) | O modelo que lê e redige | Escolha de modelo por etapa |
| Memória | O que o agente lembra dentro e entre conversas | Camada de controle → Estado; Stack → Memória e estado |
| Ferramentas | As funções que o agente pode chamar | Desenho de ferramentas; Stack → Ações e ferramentas |
| Ações | O efeito das ferramentas no mundo | Resolver → Execução de ação; Stack → Ações e ferramentas |
| Planejamento | Quem define a sequência de passos | Fundamentos → Planejamento é uma decisão explícita |
| Raciocínio | Quanto o modelo pensa antes de responder | Interpretar → Três níveis de extrator; Escolha de modelo |
| Autonomia | Quanto o modelo decide sozinho | Fundamentos → Escala de autonomia |
| Laço de feedback | Como o erro vira melhoria | Evals → Suíte de erros; Otimização contínua |
| Ambiente | Onde o agente roda e com o que se conecta | Onde o agente roda; Deploy |
| Guardrails | Os limites de entrada, execução e saída | Stack → Guardrails; Segurança |
| Observabilidade | O rastro de cada passo | Observabilidade; Monitoramento em produção |

## Por que importa

Um agente que age, e não só responde, resolve a conversa inteira sem humano: agenda, confirma, atualiza o cadastro, cobra, transfere com o resumo pronto. A métrica que importa é resolução sem humano com segurança, não número de mensagens respondidas.

## Limitações

| Limitação | O que causa | Mitigação no framework |
| --- | --- | --- |
| Alucinação | Fato inventado na resposta | Contrato de evidência, verificador, citação de fonte |
| Não determinismo | Mesma entrada, saída diferente | Decisão em código, saída estruturada, suíte de erros |
| Custo e latência variáveis | Conta e tempo de resposta imprevisíveis | Teto de custo por modelo, limite de chamadas, monitor de custo |
| Injeção de prompt | Instrução maliciosa vinda do usuário ou de documento | Guardrails de entrada e de recuperação; Segurança |
| Troca de modelo pelo provedor | Comportamento muda sem aviso | Versão de modelo fixada, regressão antes de trocar |
| Avaliação difícil | Não se sabe se melhorou | Gold set por etapa, portão de promoção |

## Para onde vai

- Protocolos abertos (MCP para ferramentas, A2A entre agentes) reduzem o custo de integração.
- Runtimes gerenciados de agente, como os hosted agents da Microsoft Foundry e a plataforma de agentes da DigitalOcean, tiram parte da operação do time.
- Frameworks convergem: LangChain roda sobre LangGraph, e o Microsoft Agent Framework juntou Semantic Kernel e AutoGen.

O framework se protege dessas mudanças pelos contratos fixos entre etapas: troca-se a peça, não o desenho.

# Casos de uso — catálogo e seleção

Fase 2 do ciclo de vida. Antes da Etapa 0, o caso precisa provar que vale um agente. Depois dela, o caso é o que a descoberta detalha.

## Seis tipos de agente por função

O catálogo público de casos do Google Cloud organiza os exemplos em seis tipos de agente. A tabela usa essa divisão e diz que etapa pesa mais em cada tipo.

| Tipo | O que faz | Etapas que pesam mais | Autonomia típica | Exemplo em produção |
| --- | --- | --- | --- | --- |
| Atendimento ao cliente | Responde, resolve e transfere em canal de cliente | Interpretar, Resolver, Transferir | N1 | Pré-atendimento de clínica, atualização cadastral de rede credenciada, triagem entre unidades de negócio |
| Funcionário | Automatiza tarefa interna repetitiva | Investigar, Resolver | N1 a N3 | Plataforma interna de gestão de pessoas |
| Criação | Gera conteúdo, mídia e campanha | Resolver | N3, sempre com revisão | Post e campanha para cliente |
| Código | Escreve, revisa e publica código | Resolver | N3 a N4 em sandbox | Claude Code nos repositórios |
| Dados | Consulta, analisa e relata dados | Investigar | N2 a N3 | Relatório de custo por cliente |
| Segurança | Detecta e responde a ameaça | Investigar, Transferir | N1 a N2 | Revisão de segredo exposto |

## As dez áreas e como cada uma entra

| Área | Tipo | Ações típicas | Risco | O que exige a mais |
| --- | --- | --- | --- | --- |
| Criação de conteúdo | Criação | Rascunho, variações, adaptação por canal | Marca, direitos autorais | Revisão humana antes de publicar |
| Atendimento | Atendimento ao cliente | Responder, agendar, atualizar cadastro, transferir | Promessa indevida, dado pessoal | Verificador, LGPD, fila humana |
| Análise de dados | Dados | SQL, gráfico, resumo | Número errado com cara de certo | Consulta em código, número sempre vindo da fonte |
| Vendas | Atendimento ao cliente | Qualificar, recomendar, orçar, fazer follow-up | Preço e prazo inventados | Catálogo como fonte de verdade, teto de desconto em código |
| Marketing | Criação e dados | Segmentar, gerar campanha, medir | Mensagem proativa sem consentimento | Opt-in, templates aprovados do WhatsApp |
| DevOps e TI | Código e segurança | Diagnosticar, abrir chamado, executar runbook | Comando destrutivo | Aprovação humana, sandbox, sem segredo no contexto |
| Pesquisa | Dados | Buscar, ler, sintetizar com fonte | Fonte ruim ou inventada | Citação obrigatória, lista de fontes permitidas |
| Finanças e operações | Funcionário | Conciliar, cobrar, emitir segunda via | Valor errado, ação financeira | Valor sempre do sistema, ação com confirmação |
| Assistente pessoal | Funcionário | Agenda, lembrete, e-mail, nota | Ação em nome da pessoa | Confirmação antes de enviar |
| Setores específicos | Qualquer | Clínica, odontologia, seguros, varejo | Regulação do setor | Política do setor em `docs/policies/` |

A IA de follow-up e a secretária virtual entram como atendimento proativo: o gatilho é agenda ou evento, não mensagem do cliente.

## Como encontrar um caso de alto valor

Dê nota de 1 a 5 em cada critério:

| Critério | 1 | 5 |
| --- | --- | --- |
| Volume | Poucas conversas por mês | Centenas ou milhares |
| Repetição | Cada conversa é diferente | Padrões claros e recorrentes |
| Valor por resolução | Pouco tempo ou receita em jogo | Muito tempo humano ou receita |
| Custo do erro (invertido) | Erro grave e irreversível | Erro barato ou corrigível |
| Dados e acesso | Sem fonte confiável ou sem API | Fontes e APIs disponíveis |
| Mensurabilidade | Sucesso subjetivo | Sucesso medido no sistema (agendou, pagou, resolveu) |

Regras:

- Nota total de 22 ou mais: candidato forte. De 15 a 21: candidato com ressalva escrita. Abaixo de 15: não construir agora.
- Custo do erro com nota 1 bloqueia o caso, a menos que a ação vá para Transferir e o agente só prepare o pacote.
- A linha de base é o atendimento humano de hoje: tempo médio, taxa de resolução e custo por conversa. Sem ela, não há como dizer que o agente melhorou.

## Ficha do caso de uso

Preenchida antes da Etapa 0 e copiada para o `PRODUCT.md`:

```txt
Caso:                <nome curto>
Tipo:                <atendimento | funcionário | criação | código | dados | segurança>
Objetivo mensurável: <ex.: 60% dos agendamentos sem humano em 90 dias>
Quem usa:            <público e volume>
Canal e gatilho:     <WhatsApp via plataforma de atendimento; mensagem | agenda | evento>
Ações:               <lista, com classe de ação>
Fontes de fato:      <sistemas e documentos, com dono>
Risco principal:     <o que não pode dar errado>
Autonomia:           <N0 a N4, com justificativa>
Métrica de sucesso:  <número e onde é medido>
Linha de base:       <como é hoje, com humano>
Nota de seleção:     <total e notas por critério>
```

## Quando não construir um agente

- O processo do cliente não está definido nem para humanos.
- A decisão final é legal, médica ou financeira e não pode ser delegada.
- O volume não paga a construção e a operação.
- Não existe fonte de verdade para os fatos que o agente teria de afirmar.
- Uma regra simples ou um formulário resolve o mesmo problema.

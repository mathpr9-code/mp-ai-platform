# Onde o agente roda

A decisão de onde o agente roda vem antes das peças, porque condiciona como buffer, estado, fila, testes e publicação são construídos. Ela entra no quadro na Etapa 0. Esta seção cobre o que afeta a escolha das peças; o detalhamento de infraestrutura (dimensionamento, droplet, rede) fica no documento de arquitetura de software.

O conteúdo desta seção é raciocínio de desenho, não resumo de documentação oficial.

## As três opções

| Opção | O que já vem pronto | O que você constrói | Serve quando | Custo e risco |
| --- | --- | --- | --- | --- |
| Orquestrador visual (n8n) em VPS | Webhook, credenciais, conectores, histórico de execuções, agendamento | Decisão em nó de código, estado em banco, buffer com nós | Fluxo linear, primeira versão rápida, time que opera pela interface | Lógica espalhada em nós; difícil rodar suíte de erros e versionar; laços e pausas ficam frágeis |
| Serviço próprio em código, em VPS ou droplet | Nada; você escolhe cada parte | Servidor de webhook, fila, worker, estado, tracing, deploy | Decisão em código testável, suíte de erros no CI, laços, pausa e retomada, vários modelos | Mais trabalho inicial; operação é sua |
| Plataforma gerenciada de agentes | Execução durável, persistência, escalabilidade | O agente e as integrações | Time pequeno que não quer operar infraestrutura | Dependência de fornecedor; custo por uso; dados fora da sua infraestrutura |

O framework não fixa runtime. n8n, serviço próprio e plataforma gerenciada são peças como as outras: a escolha é por projeto, sai da tabela "O que direciona a escolha" e vira ADR. Um mesmo agente pode nascer em n8n e migrar para serviço próprio quando os sinais aparecerem, porque os contratos entre as etapas não mudam. A única exigência que vale para qualquer runtime é a suíte de erros: ela precisa rodar inteira antes de publicar, e em n8n isso exige manter a decisão em um nó de código testável e a lógica fora dos IFs visuais.

## O que o n8n entrega e o que o serviço próprio precisa construir

A tabela serve nos dois sentidos: para quem fica no n8n, é a lista do que já vem pronto; para quem sai, é a lista do que precisa existir antes de desligar.

| O n8n entregava | No serviço próprio vira | Para quê |
| --- | --- | --- |
| Nó de webhook | Servidor HTTP que grava e confirma | Receber sem perder mensagem |
| Gerenciador de credenciais | Cofre ou variáveis de ambiente injetadas | Segredo fora do código |
| Execuções e log visual | Tracing (LangSmith ou Langfuse) | Ver o que aconteceu em cada turno |
| Retry por nó | Retry no worker, com idempotência | Falha de API não derruba o turno |
| Nós de espera e agendamento | Agendador de tarefas | Follow-up, expiração de buffer, reenvio |
| Conectores prontos | Clientes HTTP escritos e testados | Integrações com contrato |
| Publicar o fluxo | Deploy com teste, verificação de saúde e rollback | Publicação reproduzível |

## Componentes do serviço próprio

| Componente | Para que serve | Por que precisa existir |
| --- | --- | --- |
| Servidor de webhook | Recebe, valida, grava a mensagem bruta e confirma | O provedor exige resposta rápida; o processamento não pode acontecer aqui |
| Armazenamento rápido com expiração (ex.: Redis) | Buffer por conversa, trava por conversa, chave de deduplicação | Operações de milissegundos com tempo de vida; banco relacional é lento e pesado para isso |
| Fila | Separa receber de processar | Pico de mensagens não derruba o agente; falha pode ser reprocessada |
| Worker | Executa o pipeline do turno | É onde rodam as cinco etapas |
| Banco relacional (ex.: Postgres) | Histórico, estado por evento, pendências, outbox de envio, checkpoints | É a fonte de verdade auditável |
| Agendador | Follow-up, timeout de transferência, reenvio da outbox | Nem tudo começa com mensagem do cliente |
| Tracing | Trace por turno, score, custo | Sem ele não há caso para a suíte de erros |
| CI com a suíte | Roda a bateria antes de publicar | É o portão da regra do framework |

Fluxo de um turno no serviço próprio:

```txt
webhook → grava mensagem bruta → confirma ao provedor
   ↓
buffer por conversa (expira e dispara)
   ↓
fila → worker pega a trava da conversa
   ↓
entrada (normaliza, carrega estado) → interpretar → decisão → investigar / resolver / esclarecer / transferir
   ↓
grava eventos e a fala do agente com a pergunta aberta → outbox
   ↓
envio pelo canal → confirmação → solta a trava
```

## O que direciona a escolha

| Pergunta | Se a resposta for sim |
| --- | --- |
| Precisa pausar para humano e retomar do mesmo ponto? | Serviço próprio com runtime durável |
| Há laço cujo fim depende do resultado (CRAG, agente)? | Serviço próprio |
| A suíte de erros precisa rodar inteira antes de publicar? | Serviço próprio |
| Mais de um modelo por turno, com roteamento? | Serviço próprio facilita; n8n aguenta até certo ponto |
| É um fluxo linear, de triagem, para validar com o cliente em dias? | n8n serve como primeira versão |
| O time não tem quem opere servidor? | n8n ou plataforma gerenciada |

## Em n8n: o que o framework exige

- Decisão em um único nó de código, com entrada (estado mais observação) e saída (conduta) definidas, para que a suíte de erros consiga rodá-lo fora do n8n.
- Estado em banco, gravado por evento, nunca só em variáveis do fluxo.
- Buffer e trava por conversa com armazenamento rápido, não com nó de espera.
- Chamadas de modelo em subfluxos ou serviço externo, para que prompt e schema sejam versionados em arquivo.
- Fluxo exportado como JSON no repositório, com a versão publicada registrada.
- Os nós de mídia e buffer já existentes nos fluxos atuais são a implementação de referência das peças M e B.

## Caminho de saída do n8n, quando a escolha for sair

Os contratos entre as etapas são os mesmos em qualquer runtime, então a troca pode ser gradual:

1. Tirar a decisão de dentro dos nós e colocá-la em uma função única, com testes.
2. Mover extrator e redator para um serviço chamado pelo n8n.
3. Mover estado e pendências para o banco, gravados por evento.
4. Trocar o webhook e o buffer do n8n pelo servidor e pelo armazenamento rápido.
5. Desligar o n8n daquele agente.

Em cada passo a suíte de erros roda antes e depois, para provar que o comportamento não mudou. O caminho é opcional: só começa quando os sinais da tabela de escolha apontarem para o serviço próprio.

# Deploy — hospedagem, rollout e go-live

Fase 7 do ciclo de vida. "Onde o agente roda" decide entre n8n, serviço próprio e plataforma gerenciada. Esta parte diz como o serviço próprio vai para produção: em que nuvem, com que componentes, como sobe sem quebrar e o que precisa estar pronto no go-live.

**Regra de hospedagem (23/11/2026).** Onde o agente roda é decidido por agente, na Etapa 0, e fica no canvas e no ADR. As duas opções continuam válidas:

| Se o agente for construído em | Roda em | Por quê |
| --- | --- | --- |
| n8n | Droplet (VPS) da DigitalOcean, onde o n8n já está | O n8n é self-hosted no droplet; o agente vai junto |
| Serviço próprio em código | Plataforma gerenciada: DigitalOcean App Platform, Azure Container Apps ou AWS (ECS Express Mode) | Sem servidor para operar; deploy a cada push; escolha pela tabela "Qual plataforma gerenciada" |

A direção é construir os agentes novos em serviço próprio, mas o n8n não é descontinuado: ele segue para os agentes que já estão nele, para automações auxiliares e para casos em que a tabela "O que direciona a escolha" aponta n8n.

## Convivência com o n8n

```txt
Plataforma de atendimento (webhook) ──► serviço do agente novo (FastAPI + worker)
                        │
                        ├──► Postgres / Valkey
                        └──► n8n via HTTP, só para automação auxiliar existente

Plataforma de atendimento (webhook) ──► n8n ──► agentes antigos, até migrarem
```

- Cada número ou fila da plataforma de atendimento aponta para um único destino. Nunca dois sistemas respondendo à mesma conversa.
- O n8n pode chamar o serviço novo (por exemplo, o extrator como API) durante a migração de um agente antigo. O serviço novo não depende do n8n para responder.
- Os dois lados gravam no mesmo padrão de tracing, para que o monitoramento compare antes e depois.

## Arquitetura de referência

Os componentes são os de "Componentes do serviço próprio". Em produção, viram estes processos:

| Processo | O que roda | Escala por |
| --- | --- | --- |
| api | Webhook e endpoints internos (FastAPI) | Requisições |
| worker | Pipeline do turno e agendador | Tamanho da fila |
| valkey | Buffer, trava, deduplicação, fila | Memória |
| postgres | Histórico, estado, outbox, checkpoints, vetores | Armazenamento |
| observabilidade | Langfuse (nuvem ou próprio) e, se adotado, Grafana | — |

## DigitalOcean — caminho padrão

Dois jeitos de rodar, com o mesmo código e a mesma imagem Docker:

|  | Droplet com Docker Compose | App Platform |
| --- | --- | --- |
| O que é | Máquina virtual sua, com os containers | Plataforma gerenciada que sobe a partir do Git ou de uma imagem |
| Quem opera o sistema operacional | Você | A DigitalOcean |
| Componentes | Os containers que você declarar | Services (HTTP), workers (sem HTTP), jobs (antes ou depois do deploy, ou agendados) |
| Cobrança | Valor fixo da máquina | Por tamanho de container, proporcional ao segundo; job só cobra enquanto roda |
| Deploy | Pipeline que faz pull e reinicia | Automático a cada push, com volta para o deploy anterior |
| Banco | Postgres gerenciado ou Supabase | Postgres gerenciado ou Supabase |
| Melhor para | Agentes em n8n (o n8n já roda no droplet) | Agentes em serviço próprio, sem operar servidor |

Serviços gerenciados que entram nos dois casos:

| Serviço | Papel no framework |
| --- | --- |
| Managed PostgreSQL com pgvector | Estado, histórico e vetores no mesmo banco, com backup diário e recuperação por ponto no tempo |
| Managed Caching for Valkey | Buffer, trava, cache e fila; compatível com Redis |
| Spaces | Arquivos de mídia e anexos (compatível com S3) |
| Container Registry | Imagens versionadas para deploy e para voltar versão |

Região: a DigitalOcean não tem região na América do Sul (datacenters na América do Norte, Europa, Ásia e Austrália). A MP usa Nova York (NYC). O dado do cliente fica nos Estados Unidos; isso é registrado no ADR do agente e no contrato com o cliente. Cliente que exigir dado no Brasil vai para Azure (Brazil South), AWS (São Paulo) ou Supabase em São Paulo.

### Plataforma de agentes da DigitalOcean (opcional)

A DigitalOcean tem uma plataforma de IA com inferência serverless (uma API compatível com OpenAI para vários modelos, com prompt caching em preview e custo ao vivo por chave) e agentes gerenciados com base de conhecimento, roteamento entre agentes, guardrails e avaliações. No framework:

- A inferência serverless é um provedor de modelo a mais, comparável ao OpenRouter. Entra pela tabela de providers, com a mesma regra de comparação no gold set.
- O agente gerenciado serve para caso simples e informativo (N0 a N1, sem ação). A decisão em código e a suíte de erros continuam exigidas; se não couberem na plataforma, o agente vai para serviço próprio.

### Docker Compose no droplet

Uso de exceção: serviço próprio rodando no mesmo droplet do n8n, quando o volume não paga uma plataforma gerenciada. O padrão para serviço próprio é App Platform ou Container Apps.

```yaml
# compose.yaml — um agente por projeto
services:
  api:
    image: registry.digitalocean.com/mp-studio/agente-x:${VERSION}
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    env_file: .env            # gerado pelo cofre na hora do deploy, nunca no repositório
    depends_on: [valkey]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      retries: 3

  worker:
    image: registry.digitalocean.com/mp-studio/agente-x:${VERSION}
    command: python -m app.worker
    env_file: .env
    depends_on: [valkey]
    restart: unless-stopped

  valkey:
    image: valkey/valkey:8
    command: ["valkey-server", "--appendonly", "yes"]
    volumes: ["valkey-data:/data"]
    restart: unless-stopped

  caddy:
    image: caddy:2
    ports: ["80:80", "443:443"]
    volumes: ["./Caddyfile:/etc/caddy/Caddyfile", "caddy-data:/data"]
    restart: unless-stopped

volumes:
  valkey-data:
  caddy-data:
```

O Postgres fica fora do droplet (gerenciado ou Supabase), para que backup e recuperação não dependam da máquina.

Pipeline mínimo: push na `main` → CI roda a suíte de erros → build da imagem com a versão do agente → push para o Container Registry → no droplet, `docker compose pull && docker compose up -d` → checagem do `/health`. Voltar versão é rodar o mesmo comando com a versão anterior.

### App Platform

```yaml
# .do/app.yaml
name: agente-x
services:
  - name: api
    github:
      repo: mathpr9-code/agente-x
      branch: main
      deploy_on_push: true
    dockerfile_path: Dockerfile
    run_command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    http_port: 8000
    instance_size_slug: apps-s-1vcpu-1gb
    health_check:
      http_path: /health
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        type: SECRET
workers:
  - name: worker
    github:
      repo: mathpr9-code/agente-x
      branch: main
      deploy_on_push: true
    dockerfile_path: Dockerfile
    run_command: python -m app.worker
    instance_size_slug: apps-s-1vcpu-1gb
jobs:
  - name: migrate
    kind: PRE_DEPLOY
    github:
      repo: mathpr9-code/agente-x
      branch: main
    dockerfile_path: Dockerfile
    run_command: alembic upgrade head
```

Confira os nomes de tamanho e a sintaxe de job agendado na documentação da App Platform antes de usar; mudam com o tempo.

Fontes: [App Platform — Pricing](https://docs.digitalocean.com/products/app-platform/details/pricing), [Managed Databases](https://www.digitalocean.com/pricing/managed-databases), [Vector Databases](https://docs.digitalocean.com/products/vector-databases/details/pricing/), [AI Platform](https://docs.digitalocean.com/products/ai-platform/reference/).

## Azure — alternativa

| Serviço | O que é | Papel no framework |
| --- | --- | --- |
| Azure Container Apps | Containers serverless para APIs, workers que escalam por fila ou evento, jobs agendados e agentes. Escala a zero; com KEDA e Dapr; sessões dinâmicas para rodar código gerado por LLM em sandbox | Equivalente da App Platform. Hospeda api, worker e jobs |
| Foundry Agent Service — hosted agents (preview) | Agente em container, com Agent Framework, LangGraph ou código próprio; a plataforma cuida de escala, estado de sessão, observabilidade e ciclo de vida. Brazil South está entre as regiões | Runtime gerenciado para agente em Agent Framework ou LangGraph |
| Azure Database for PostgreSQL | Postgres gerenciado com pgvector | Estado, histórico e vetores |
| Azure Managed Redis | Redis gerenciado | Buffer, trava, cache, fila |
| Azure AI Content Safety | Classificadores de dano, Prompt Shields, groundedness | Guardrails de entrada e de saída |
| Application Insights / Azure Monitor | Telemetria com OpenTelemetry | Infraestrutura e alertas |

Custo no Container Apps: o plano de consumo cobra por segundo de vCPU e de memória e por requisição, com franquia mensal grátis de 180.000 vCPU-segundos, 360.000 GiB-segundos e 2 milhões de requisições por assinatura. Sem réplica rodando, não há cobrança de uso; réplica mínima parada cobra em taxa reduzida.

Regra para webhook: a api fica com no mínimo uma réplica, porque o tempo de partida a frio atrasa a resposta ao provedor. Worker e jobs podem escalar a zero.

Quando escolher Azure:

- O modelo roda no Azure OpenAI, como no plano de fine-tuning pelo Azure.
- O cliente exige Azure, Entra ID, rede privada ou dado no Brasil.
- Muitos agentes de baixo volume, onde escala a zero paga a diferença.
- Publicação em Teams ou Microsoft 365.

Fontes: [Azure Container Apps](https://azure.microsoft.com/products/container-apps/), [Container Apps — Pricing](https://azure.microsoft.com/pricing/details/container-apps/), [Hosted agents](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents), [Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/overview).

## AWS — alternativa

A AWS entra quando o cliente já está nela, quando o modelo roda no Amazon Bedrock (a troca da OpenRouter pela AWS já está em levantamento de custo) ou quando o dado precisa ficar na região de São Paulo.

| Serviço | O que é | Papel no framework |
| --- | --- | --- |
| Amazon ECS Express Mode | Recurso do ECS que cria cluster, serviço, load balancer, grupos de segurança, auto scaling e logs no CloudWatch a partir de uma imagem, sobre Fargate | Equivalente da App Platform. Hospeda api e worker |
| AWS App Runner | Antigo PaaS de containers. Fechado para clientes novos desde 30/04/2026, sem funcionalidade nova; a AWS indica ECS Express Mode no lugar | Não usar em projeto novo |
| Amazon Bedrock | Acesso gerenciado a modelos de vários provedores, cobrado por token | Provedor de modelo, comparado no gold set como qualquer outro |
| Amazon Bedrock Guardrails | Filtros de conteúdo, detecção de ataque de prompt (jailbreak, injeção, vazamento de prompt), tópicos negados, filtro de palavras, dado pessoal com máscara, checagem de grounding e Automated Reasoning. A API ApplyGuardrail avalia conteúdo sem chamar modelo e serve também para modelo fora do Bedrock | Guardrails de entrada e de saída |
| Amazon Bedrock AgentCore | Plataforma modular de agente: Runtime (execução serverless do agente), Memory (curta e longa), Gateway (ferramentas), Identity (credenciais e acesso), Observability (CloudWatch), Browser, Code Interpreter e Policy. Funciona com LangChain, LangGraph, CrewAI, LlamaIndex, Strands e outros, e com qualquer modelo | Runtime gerenciado para agente em LangGraph, equivalente aos hosted agents da Foundry |
| Amazon RDS ou Aurora PostgreSQL | Postgres gerenciado com pgvector | Estado, histórico e vetores |
| Amazon ElastiCache (Valkey ou Redis) | Cache gerenciado | Buffer, trava, cache, fila |
| Amazon EventBridge Scheduler | Agendamento gerenciado | Gatilhos de agenda (follow-up, reenvio, ingestão) |
| Amazon CloudWatch | Logs, métricas e alarmes | Infraestrutura e alertas |

Região: o anúncio de 01/05/2026 diz que o AgentCore chegou a São Paulo (sa-east-1) com runtime, identidade, gateway, política, observabilidade e ferramentas. A página de regiões da documentação ainda listava São Paulo só com Memory quando foi consultada. Confira a página de regiões antes do ADR.

Regra: o AgentCore hospeda o agente, mas não tira a decisão do código nem a suíte de erros. Use o Runtime e a Memory dele como peças; os contratos do framework continuam os mesmos.

Fontes: [App Runner — availability change](https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html), [Bedrock Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-components.html), [Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html), [AgentCore em São Paulo](https://aws.amazon.com/about-aws/whats-new/2026/05/agentcore-sao-paulo-region/), [AgentCore — regiões](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html).

## Qual plataforma gerenciada: DigitalOcean, Azure ou AWS

Vale só para agente em serviço próprio. Padrão: DigitalOcean App Platform. Troca para Azure ou AWS quando uma linha da tabela pedir.

| Critério | DigitalOcean App Platform | Azure Container Apps | AWS ECS Express Mode |
| --- | --- | --- | --- |
| Conta, banco e rede | Mesma conta do droplet e do Postgres e Valkey gerenciados | Conta nova, Postgres e Redis do Azure | Conta nova, RDS e ElastiCache |
| Cobrança | Por container, previsível no mês | Por segundo de uso, com franquia grátis; escala a zero | Por recurso do Fargate e do load balancer, por uso |
| Modelo de linguagem | Qualquer provedor (OpenRouter, inferência serverless da DigitalOcean) | Melhor quando o modelo está no Azure OpenAI, como no plano de fine-tuning | Melhor quando o modelo está no Bedrock |
| Região no Brasil | Não; usa Nova York | Sim (Brazil South) | Sim (São Paulo, sa-east-1) |
| Volume | Agentes com tráfego contínuo | Muitos agentes de baixo volume, onde escalar a zero paga | Tráfego contínuo e escala alta |
| Cliente | PME, sem exigência de nuvem | Cliente corporativo com Entra ID, rede privada ou Teams | Cliente corporativo que já está na AWS |
| Runtime gerenciado de agente | Plataforma de agentes da DigitalOcean, para caso simples | Foundry hosted agents, para agente em Agent Framework ou LangGraph | Bedrock AgentCore Runtime, para agente em LangGraph, CrewAI ou outro |
| Guardrails gerenciados | Guardrails da plataforma de agentes | Azure AI Content Safety | Bedrock Guardrails |

Regra: a mesma imagem Docker roda nas três. Trocar de plataforma é mudar o arquivo de deploy, não o agente.

## Banco de dados — onde fica

Regra: **o banco fica na mesma nuvem e na mesma região do runtime do agente.** Banco em outra nuvem acrescenta latência em cada consulta do turno, sai pela internet pública em vez da rede privada e divide a operação em duas contas.

| Runtime do agente | Banco padrão | Observação |
| --- | --- | --- |
| n8n no droplet | Supabase, como hoje, ou Managed PostgreSQL da DigitalOcean em NYC | Agentes existentes ficam onde estão até migrar |
| DigitalOcean App Platform | Managed PostgreSQL da DigitalOcean, na mesma região (NYC) e na mesma VPC | pgvector disponível; pool de conexão com PgBouncer |
| Azure Container Apps | Azure Database for PostgreSQL (Flexible Server), em Brazil South | Mesma rede virtual do Container Apps |
| AWS ECS Express Mode | Amazon RDS ou Aurora PostgreSQL, em São Paulo | Mesma VPC do ECS |
| Front-end em Lovable que usa login, storage ou realtime | Supabase | O Supabase é o backend do app, não só o banco |

### Supabase ou Postgres gerenciado

O Supabase não é só um banco: é um Postgres com autenticação, storage, realtime, API automática e painel em volta. A pergunta certa é se o projeto precisa dessas camadas.

| Use Supabase quando | Use Postgres gerenciado na nuvem do runtime quando |
| --- | --- |
| O app precisa de login, storage, realtime ou API automática | O agente é serviço próprio e só precisa do banco |
| O front-end é Lovable ou fala direto com o banco | O backend em código controla todo acesso ao banco |
| O dado precisa ficar no Brasil e o runtime está na DigitalOcean (Supabase tem São Paulo) | O runtime está na App Platform, no Azure ou na AWS, e o banco pode ficar junto |
| Protótipo rápido | Produção com rede privada, uma conta e uma fatura |

Os dois são Postgres. Trocar é `pg_dump` e `pg_restore`; o que exige trabalho são as políticas de RLS que usam `auth.uid()`, as tabelas do schema `auth` e os arquivos do storage. O código do agente acessa o banco por SQL padrão (driver Postgres ou ORM), nunca pela biblioteca do Supabase, para que a troca não mexa no agente.

O Postgres gerenciado também tem limites: na DigitalOcean, só as extensões da lista podem ser ativadas, e o número de pools de conexão depende do plano. Confira as extensões que o agente usa (pgvector, pg\\_trgm, uuid) antes do ADR.

### MySQL

Não entra como banco do agente. O framework depende de recursos do Postgres: pgvector para memória e recuperação, JSONB para estado, RLS para isolar cliente e o checkpointer do LangGraph em Postgres. MySQL só aparece como fonte de dados do cliente em Investigar.

Fontes: [DigitalOcean — Regional availability](https://docs.digitalocean.com/products/platform/availability-matrix), [DigitalOcean PostgreSQL — limits](https://docs.digitalocean.com/products/databases/postgresql/details/limits/), [Supabase — Available regions](https://supabase.com/docs/guides/platform/regions).

## Comparação de hospedagem

|  | DigitalOcean Droplet | DigitalOcean App Platform | Azure Container Apps | Foundry hosted agents |
| --- | --- | --- | --- | --- |
| Operação | Toda sua | Gerenciada | Gerenciada | Gerenciada, inclusive estado de sessão |
| Cobrança | Fixa | Por container, proporcional | Por segundo, com franquia grátis | Ver página de preços da Foundry (preview) |
| Escala a zero | Não | Não para services | Sim | Sim |
| Jobs e cron | Agendador no worker | Jobs | Jobs | — |
| Região no Brasil | Não; usa Nova York | Não; usa Nova York | Sim (Brazil South) | Sim (Brazil South) |
| Melhor para | Agentes em n8n | Agentes em serviço próprio (padrão) | Cliente Azure, muitos agentes de baixo volume | Agente em Agent Framework ou LangGraph sem operar runtime |

Railway, Render e [Fly.io](http://Fly.io) são alternativas de PaaS para projeto pequeno; não entram no padrão porque a MP já opera na DigitalOcean, e Azure e AWS cobrem o caso corporativo.

Na AWS, ECS Express Mode e Bedrock AgentCore Runtime têm o mesmo papel que Container Apps e Foundry hosted agents no Azure: operação gerenciada, cobrança por uso, região em São Paulo, gatilhos de agenda pelo EventBridge Scheduler. A escolha entre as três nuvens sai da tabela "Qual plataforma gerenciada".

## Autenticação e segurança da API

- Webhook só aceita requisição com o token ou a assinatura do provedor (plataforma de atendimento), validados antes de gravar.
- Endpoints internos com chave por cliente e escopo mínimo.
- Rate limit por contato e por cliente.
- HTTPS obrigatório; banco acessível só pela rede privada ou por fontes confiáveis.
- Segredos vêm do cofre na hora do deploy (ver "Segredos: cofre e .env cifrado"), nunca da imagem nem do repositório.
- O usuário do banco do agente não tem permissão de DDL; migração roda com outro usuário, no job de pré-deploy.

## Gatilhos em produção

| Gatilho | Droplet | App Platform | Azure Container Apps | AWS |
| --- | --- | --- | --- | --- |
| Mensagem (webhook) | api | service | app com ingress | Serviço do ECS Express Mode |
| Agenda (follow-up, reenvio da outbox, ingestão) | Agendador dentro do worker | Job agendado ou agendador no worker | Job agendado | EventBridge Scheduler |
| Evento de sistema | Fila no Valkey | Fila no Valkey | Escala por fila (KEDA) | Fila no ElastiCache ou SQS |

Todo gatilho agendado grava uma chave de idempotência por conversa e janela, para que uma execução repetida não mande duas mensagens.

## Estratégia de rollout

Ambientes: desenvolvimento → staging → produção. Staging usa a mesma imagem, o mesmo tamanho de máquina e um número de teste da plataforma de atendimento.

| Passo | O que acontece | Para avançar |
| --- | --- | --- |
| 1. Shadow | A versão nova roda em paralelo sobre conversas reais, sem responder. Compara-se com a versão atual ou com o humano | Suíte de erros verde; diferença revisada; nenhum caso SEC |
| 2. Canary | A versão nova responde a uma parte: um cliente piloto ou uma porcentagem das conversas novas, escolhida por conversa, nunca por turno | Métricas do monitoramento sem regressão por pelo menos 3 dias úteis |
| 3. Expansão | Porcentagem maior ou mais clientes | Idem |
| 4. Total | Todas as conversas | Versão anterior mantida pronta para voltar |

- A chave que liga a versão nova fica em uma tabela de configuração por cliente, lida pelo worker. Ligar e desligar não exige deploy.
- Voltar versão é imagem anterior mais o rótulo de prompt anterior. Os dois precisam estar registrados na ficha de versões.
- Mudança de modelo, de prompt ou de regra segue o mesmo caminho que mudança de código.

## Go-live

- [ ] Suíte de erros e suíte de segurança verdes na versão que vai subir
- [ ] Shadow concluído e diferenças revisadas
- [ ] Dashboards e alertas do monitoramento ativos antes da primeira conversa
- [ ] Fila humana na plataforma de atendimento pronta e atendentes avisados
- [ ] Mensagens fixas de falha (fora do ar, transferência) revisadas com o cliente
- [ ] Plano de volta testado em staging
- [ ] Segredos do cliente no cofre, com rotação registrada
- [ ] Ficha de versões atualizada (código, prompt, modelo, índice)
- [ ] Responsável de plantão nas primeiras 48 horas

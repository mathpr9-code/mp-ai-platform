# Segurança e limites de confiança

Resumo, que vale para todo agente:

- Autenticação, autorização e isolamento por tenant em toda consulta e ferramenta
- Mensagem do cliente e conteúdo recuperado são dados não confiáveis, nunca instruções
- Aprovação vinculada à ação exata quando a política exigir
- Segredo não entra em chat, prompt nem log
- Conteúdo de conversa minimizado, anonimizado antes de virar dado de avaliação, com retenção definida

Segurança é transversal: uma interpretação, um documento recuperado ou um resultado externo nunca vira autorização por si só.

## OWASP Top 10 para aplicações agênticas (2026)

A OWASP publicou em 9 de dezembro de 2025 a lista dos dez riscos de sistemas em que o modelo planeja, usa ferramentas, guarda memória e age (ASI01 a ASI10). O princípio central é a **menor agência**: dar ao agente só a autonomia que a tarefa exige. É a mesma lógica deste framework, em que o extrator lê sem decidir e o caminho conhecido é código.

Onde cada risco é tratado aqui:

| Risco | O que é | Como o framework trata | Onde |
| --- | --- | --- | --- |
| ASI01 Agent Goal Hijack | Conteúdo malicioso muda o objetivo do agente | Texto do cliente e conteúdo recuperado entram como dado; o extrator não decide; a conduta sai do código; gatilho exige ato explícito com evidência literal | Interpretar; O turno é um par; Prompt injection |
| ASI02 Tool Misuse and Exploitation | Ferramenta legítima usada de forma indevida | Lista fechada de ferramentas; contrato de ação com autorização, pré-condições e risco; execução por código | Resolver (RES8); Desenho de ferramentas |
| ASI03 Identity and Privilege Abuse | O agente herda, escala ou vaza credenciais | Identidade e permissão vêm do sistema, nunca da conversa; escopo mínimo por ferramenta; agente filho recebe só o escopo delegado | Limites de confiança; Aprovação de ações críticas |
| ASI04 Agentic Supply Chain Vulnerabilities | Ferramenta, prompt, plugin ou agente de terceiro comprometido | Conectores e servidores MCP aprovados, com versão fixa e revisão a cada mudança; modelo com versão exata; skill por modelo | Conectores, MCP e cadeia de suprimentos; Escolha de modelo |
| ASI05 Unexpected Code Execution | O agente gera ou executa código sem isolamento | Agente de atendimento não executa código gerado; quando houver, sandbox sem root, sem rede livre e sem segredos | Sandbox e isolamento |
| ASI06 Memory and Context Poisoning | Memória, RAG ou embeddings contaminados influenciam decisões futuras | Estado muda só por evento validado; o extrator gera candidatos, não grava; memória com proveniência e validade; fontes com autoridade e dono | Estado; Memória, cache e contexto persistente; Contrato de evidência |
| ASI07 Insecure Inter-Agent Communication | Mensagens entre agentes sem autenticação permitem falsificação | Multiagente só com motivo; mensagem de outro agente é entrada não confiável, com contrato | Um agente ou vários; Transferir (TR5) |
| ASI08 Cascading Failures | O erro de um agente se propaga pelo fluxo | Teto de passos; validação em código entre etapas; retry único e texto de escape; falha fechada | Resolver; Camada de controle |
| ASI09 Human-Agent Trust Exploitation | A pessoa confia demais na saída e aprova o que não aprovaria | O redator só afirma fatos do ato; ação não confirmada nunca é narrada como feita; aprovação vinculada aos parâmetros exatos; pacote de handoff factual | Protocolo do redator; Pacote de handoff |
| ASI10 Rogue Agents | Agente comprometido ou desalinhado age fora do objetivo parecendo legítimo | Trace por turno e por passo; scores automáticos; suíte de erros antes de publicar; prompt, ferramentas e política versionados; forma de desligar o agente e transferir tudo para humano | Observabilidade; Suíte de erros; Transferir |

O que falta em qualquer projeto é conferido na seção K da Matriz de Segurança, que tem um controle por risco. A lista foi consultada em resumos de terceiros que a reproduzem, coerentes entre si; o texto original da OWASP não foi aberto nesta revisão.

## OWASP MCP Top 10 (beta, 2025)

Você usa conectores e servidores MCP; esta lista é a que trata disso. Conferida na [página oficial do projeto](https://owasp.org/projects/mcp-top-10) em 12/11/2026: dez riscos com sufixo :2025, status "Beta Release and Pilot Testing" (fase 3 de 5), licença CC BY-NC-SA 4.0, textos de cada risco no GitHub do projeto.

| Risco | O que é (resumo da página oficial) | Como o framework trata | Onde |
| --- | --- | --- | --- |
| MCP01 Token Mismanagement and Secret Exposure | Credenciais fixas, tokens longos e segredos em memória do modelo ou em logs | Uma credencial por servidor, curta e com escopo; nenhum segredo no prompt, trace ou memória | Conectores, MCP e cadeia de suprimentos |
| MCP02 Privilege Escalation via Scope Creep | Permissões temporárias que crescem | Escopo por capacidade; revisão a cada mudança; expiração | Idem |
| MCP03 Tool Poisoning | Ferramenta, plugin ou saída comprometidos injetam contexto | Nome, descrição e schema revisados; versão e hash fixados; saída de ferramenta é dado | Desenho de ferramentas; Limites de confiança |
| MCP04 Software Supply Chain Attacks | Dependência comprometida altera o agente | Lista de servidores aprovados com dono, origem e versão | Conectores, MCP e cadeia de suprimentos |
| MCP05 Command Injection and Execution | O agente monta comandos com entrada não confiável | Agente de atendimento não executa código; argumentos estruturados, sem shell | Sandbox e isolamento |
| MCP06 Prompt Injection via Contextual Payloads | Texto que vira instrução | Texto de cliente e conteúdo recuperado como dado; extrator sem autoridade | Interpretar; Prompt injection |
| MCP07 Insufficient Authentication and Authorization | Sem verificação de identidade entre servidores, ferramentas e agentes | Token validado no servidor de recurso; id de sessão não é identidade | Conectores, MCP e cadeia de suprimentos |
| MCP08 Lack of Audit and Telemetry | Pouca telemetria impede investigação | Trace por chamada de ferramenta, com argumentos e resultado sanitizados | Observabilidade |
| MCP09 Shadow MCP Servers | Servidores não aprovados, com credenciais padrão | Inventário obrigatório; nada em produção sem revisão | Conectores, MCP e cadeia de suprimentos |
| MCP10 Context Injection and Over-Sharing | Contexto compartilhado vaza entre tarefas, usuários ou tenants | Contexto montado por código por conversa; memória e cache isolados por tenant | Contexto por etapa; Memória, cache e contexto persistente |

Por ser beta, nomes e detalhes podem mudar; reconferir a página a cada revisão do framework.

## Segredos: cofre e .env cifrado

Todo agente usa chaves: a do provedor de modelo, a do canal (WhatsApp, plataforma de atendimento), a do banco, a de cada ferramenta. O framework trata essas chaves do mesmo jeito que o Framework de Construção de Plataformas (seção 8.1), que tem o detalhe de cada peça e o que foi conferido de cada produto. Aqui fica o que vale para todo projeto de agente.

### Onde cada coisa fica

| O quê | Onde | Por quê |
| --- | --- | --- |
| Senhas e chaves das pessoas: painéis de provedores, bancos, contas, códigos de recuperação | Gerenciador de senhas (V7). Padrão proposto: Bitwarden | É lido por gente, nunca por aplicação |
| Segredos que o agente usa para rodar: chaves de modelo, de canal, de banco, de ferramentas | Gerenciador de segredos (V3). Padrão proposto: Bitwarden Secrets Manager | É lido por máquina, com acesso por projeto e registro de uso |
| Configuração do projeto versionada no Git | `.env` cifrado com dotenvx (ou ferramenta equivalente) | O arquivo vai para o repositório com os valores cifrados; quem não tem a chave privada vê só texto cifrado |
| Chave privada do `.env` cifrado (`.env.keys`, `DOTENV_PRIVATE_KEY`) | No gerenciador de segredos (V3) ou, para quem opera sozinho, no gerenciador de senhas (V7); em produção, variável de ambiente do provedor (V1) | É o único segredo que abre todos os outros do arquivo |
| Produção e CI | Variáveis do provedor (V1), preenchidas a partir do cofre | O processo recebe o valor; ninguém copia à mão |
| Inventário de segredos (nome, serviço, cofre, dono, validade) | Notion ou `docs/` do projeto, sem valores | Permite saber o que existe sem expor nada |

### Regras para projetos de agente

- Nenhum valor de segredo em Notion, documento, planilha, chat, prompt, trace, log ou memória do agente.
- O `.env.keys` nunca fica na pasta do projeto: o agente de código lê qualquer arquivo do workspace, com ou sem `.gitignore`. A chave entra no processo na hora de rodar, vinda do cofre (por exemplo `bws run -- dotenvx run -- python app.py`, ou `op run` com 1Password).
- Uma chave por ambiente (`DOTENV_PRIVATE_KEY` para desenvolvimento, `DOTENV_PRIVATE_KEY_PRODUCTION` para produção) e uma chave de provedor por cliente quando o custo é do cliente.
- Toda chave de modelo pago com teto de gasto e alerta no provedor.
- Chave que apareceu onde não devia (Notion, chat, trace, commit) é rotacionada; apagar a mensagem não basta.
- O caso SEC-009 da suíte de erros (cliente pede a chave) e o controle "Segredo fora de ferramenta de notas" da Matriz (seção B) valem para todo agente.

### Configuração por projeto (Bitwarden Secrets Manager e bws)

Igual à do Framework de Plataformas (seção 8.1) e detalhada no Guia de senhas e segredos — Bitwarden da MP Studio. Em resumo: uma vez por computador, instalar o `bws` e ter a conta de máquina `dev-local` com token guardado no Password Manager; uma vez por projeto, criar o projeto no Secrets Manager, dar "Pode ler" para `dev-local`, cifrar o `.env`, copiar as linhas do `.env.keys` para segredos de mesmo nome, registrar o id do projeto no `CLAUDE.md` e no script `dev:seguro`, e tirar o `.env.keys` da pasta; toda vez que for rodar, definir `BWS_ACCESS_TOKEN` só no terminal que roda o projeto.

### Regra obrigatória no [CLAUDE.md](http://CLAUDE.md)

Todo projeto de agente leva este bloco no `CLAUDE.md` (ou `AGENTS.md`) desde o passo 0.5 da Etapa 0. A instrução não basta sozinha: a barreira técnica é o `.env.keys` fora da pasta e o token só no terminal do responsável.

```markdown
## Segredos — regra obrigatória

Este projeto usa .env cifrado com dotenvx. As chaves privadas ficam no Bitwarden Secrets Manager (projeto: <nome-do-projeto>, id: <id-do-projeto>). O id não é segredo.

O agente:
- pode ler e versionar o .env e o .env.production cifrados (valores "encrypted:");
- nunca abre, lê, imprime, copia ou resume .env.keys, nem qualquer arquivo com chave privada, token ou senha;
- nunca roda comandos que exibem segredos: dotenvx decrypt, dotenvx get, bws secret get, bws secret list, printenv, env, Get-ChildItem Env:, echo de variáveis de ambiente;
- nunca roda bws run nem npm run dev:seguro; quem roda a aplicação com segredos é o responsável, no terminal dele;
- quando precisar de uma variável secreta nova, informa o nome e pede para o responsável rodar: npx dotenvx set NOME_DA_VARIAVEL
- se encontrar um segredo em texto (código, log, documento, commit), para, avisa o responsável e não repete o valor.
```

No Claude Code, reforçar com negação de leitura em `.claude/settings.json`: `{"permissions": {"deny": ["Read(./.env.keys)", "Read(./**/.env.keys)"]}}`, conferindo com `/permissions`.

## Limites de confiança

- Mensagem de cliente é conteúdo não confiável.
- Documento recuperado é dado não confiável até validação de origem e escopo.
- Resultado de ferramenta é entrada externa; precisa de validação de schema e proveniência.
- Saída de LLM é proposta, não fato nem autorização.
- Estado de negócio vem de fonte autorizada.
- Identidade e permissão vêm do sistema de autenticação, nunca do texto da conversa.

## Controles mínimos

- Isolamento de tenant em consultas, armazenamento, cache, embeddings, logs e ferramentas.
- Autorização no servidor para cada operação; esconder uma ferramenta do prompt não substitui permissão.
- Menor privilégio para serviços, usuários e agentes.
- Segredos em cofre, nunca em prompt, dataset ou log.
- Minimização e mascaramento de dados pessoais; criptografia em trânsito e em repouso.
- Controle de acesso por função e trilha de auditoria.
- Limites de taxa, orçamento, tamanho de entrada e tempo de execução.
- Validação do que APIs e ferramentas retornam.
- Separação de dados entre desenvolvimento, teste, staging e produção.

## Prompt injection

Conteúdo de cliente, documentos, páginas e resultados de ferramenta é delimitado como dado, nunca misturado às instruções. Instrução encontrada nesses dados não altera política, permissão, contrato nem escopo de ferramenta. A autorização é determinística na camada de execução: mesmo que o modelo peça uma ação indevida, o gateway de ferramentas rejeita.

## Privacidade por desenho

Cada dado tem finalidade, classificação, acesso, retenção e regra de exclusão. Não registrar conteúdo integral por conveniência. Não promover conversas a dataset sem sanitização, revisão e autorização. Não reutilizar dados de um cliente em outro.

## Modelagem de ameaças

Para cada agente e ferramenta, documentar ativos, fronteiras de confiança, dados tratados, atores autorizados, efeitos externos e cenários de falha. Revisar a cada mudança de permissão, escopo, conector, fonte de conhecimento ou operação de escrita.

## Segredo não entra no chat

A arquitetura separa o raciocínio do modelo, o ambiente de execução e o cofre de credenciais. O modelo recebe só o contexto necessário; a ferramenta acessa a credencial sem expor o valor à conversa.

- Nunca colar conteúdo real de `.env`, tokens, API keys, senhas, cookies, chaves SSH privadas, connection strings ou credenciais de cloud em chat, prompt, memória, dataset, issue, documentação ou mensagem de debug.
- Para o agente conhecer a configuração, compartilhar só nomes de variáveis e placeholders.
- Ao investigar um `.env`, olhar apenas nomes, presença e metadados; mascarar valores antes de qualquer saída.
- Não pedir ao agente para imprimir, resumir, copiar ou confirmar valores secretos.
- Conversas, logs, traces, históricos de execução e saídas de ferramenta são superfícies de dados com retenção e acesso próprios; chat não é cofre.
- Dados vindos de arquivos, páginas, issues e terminal também são não confiáveis e passam por filtro antes de entrar no contexto.

> ⛔ Regra de bloqueio: se uma tarefa exigir colar um segredo real no chat para o agente prosseguir, pare e redesenhe a integração para que a ferramenta busque a credencial direto no cofre ou no runtime.

## Cofres e credenciais

- Guardar credenciais em Secret Manager, Vault ou no mecanismo seguro da plataforma de execução.
- Preferir credenciais curtas, temporárias, revogáveis e de escopo mínimo; evitar tokens pessoais de longa duração e credenciais administrativas globais.
- Separar desenvolvimento, staging e produção. O agente de desenvolvimento não herda acesso à produção.
- A ferramenta busca o segredo no cofre durante a execução e devolve ao modelo só status, metadados e resultado sanitizado.
- Nenhum segredo em argumento visível, comando, query string, mensagem de erro, artefato, screenshot ou log.
- Cada credencial tem dono, finalidade, escopo, validade, rotação, revogação e trilha de auditoria.
- A chave de criptografia do cofre é crítica: proteger, fazer backup e documentar a recuperação.

## Agentes de código e repositórios

- Revisar permissões de arquivos, terminal, rede, Git, Docker, SSH e cloud antes de habilitar ferramentas.
- Não dar acesso amplo à home, a pastas de chaves, ao `.ssh`, a arquivos de credenciais ou a backups.
- Restringir o agente ao workspace do projeto e aos comandos necessários; evitar root e Docker socket sem justificativa.
- Manter o `.env` real fora do Git e fora do contexto do modelo; `.env.example` só com nomes e valores fictícios. O `.gitignore` impede versionar, mas não impede o agente de ler o arquivo: aplicar também regras de negação do agente e injetar segredos no processo sem torná-los legíveis.
- Configurar secret scanning e push protection; revisar diffs antes de commit, PR e deploy.
- Se um segredo aparecer em terminal, diff, log ou resposta, interromper, sanitizar e tratar a credencial como exposta.
- Remover o segredo do arquivo ou do histórico não invalida a credencial: primeiro revogar ou rotacionar, depois limpar.

## n8n e automações

- Usar o gerenciador de credenciais do n8n; nunca digitar token em nó de texto, prompt, Set, Code, nota ou mensagem enviada ao LLM.
- Proteger a `N8N_ENCRYPTION_KEY` como segredo crítico, fora do banco e dos workflows, com backup e procedimento de recuperação.
- Restringir quem vê e edita workflows e credenciais; separar projetos e ambientes.
- Evitar credenciais em logs de execução, pin data, histórico, outputs e mensagens de erro.
- Proteger webhooks com autenticação ou assinatura, validação de payload, rate limit e proteção contra replay.
- Restringir nós de comando, arquivo, HTTP Request e community nodes; instalar só o necessário e confiável.
- Em instalação própria: rodar a auditoria do n8n com regularidade, habilitar proteção contra SSRF, endurecer task runners, redigir dados sensíveis dos logs com política de retenção, restringir ou desabilitar a API pública se não for usada, e revisar usuários, compartilhamentos e privilégios.

## APIs, VPS e SSH

- Não colar tokens de cloud, chaves SSH privadas, credenciais root, `.env` de produção ou connection strings no chat.
- Preferir tokens de escopo e prazo limitados, identidade de serviço ou provisionamento controlado pelo cofre.
- SSH com chave individual, usuário de deploy sem root, permissões mínimas e revogação.
- Provisionamento por infraestrutura como código ou scripts revisados, com segredos injetados em runtime.
- Não gravar segredos em user-data, cloud-init, scripts versionados, histórico do shell ou logs de inicialização.
- Restringir firewall, portas e painéis administrativos; manter sistema atualizado; desabilitar login root por senha.
- Separar credenciais de deploy e de operação: quem prepara infraestrutura não ganha autorização para destruir recursos.

## Quando um segredo for exposto

1. Considerar a credencial comprometida, sem esperar evidência de uso.
2. Revogar ou rotacionar na origem; invalidar sessões e tokens relacionados.
3. Verificar logs de uso, acessos, deploys e chamadas de API na janela de exposição.
4. Substituir a credencial nos ambientes legítimos e testar as integrações.
5. Remover o valor de chats, logs, tickets, arquivos e histórico Git quando possível, sem confundir remoção com revogação.
6. Registrar incidente, escopo, impacto, ações e prevenção.

## Conectores, MCP e cadeia de suprimentos

A ferramenta é extensão da superfície de ataque do agente.

- Manter lista de servidores MCP, conectores, plugins e community nodes aprovados, com dono, origem, versão, finalidade e permissões.
- Verificar fornecedor, repositório, pacote e dependências antes de instalar ou atualizar.
- Revisar também nome, parâmetros, schemas e anotações da ferramenta: esses metadados podem induzir uso inseguro.
- Fixar versão e, quando viável, hash da definição aprovada; mudança de schema, descrição, permissão ou origem exige nova revisão.
- Não compartilhar o mesmo token entre servidores; credencial por servidor e por capacidade, de escopo estreito e curta duração.
- Validar token no servidor de recurso (emissor, assinatura, expiração, audiência, escopos, tenant); não repassar token entre serviços.
- Id de sessão ou de workflow não é prova de identidade.
- Não aprovar automaticamente ferramenta nova, mudança de definição ou chamada sensível.

## Sandbox e isolamento

- Executar ferramentas locais e servidores MCP em ambiente isolado, sem root, com filesystem restrito e limites de CPU, memória, tempo e processos.
- Leitura e escrita só no workspace; não montar home, `.ssh`, diretórios de credenciais nem Docker socket.
- Preferir filesystem somente leitura, com escrita em diretórios temporários definidos.
- Lista de comandos permitidos com argumentos estruturados; evitar shell genérico.
- Separar execução de código gerado de ambientes com credenciais e dados de produção.
- Restringir saída de rede por domínio, IP e porta; bloquear endpoints de metadata, loopback e redes privadas fora do escopo.
- Validar URLs de destino no servidor; texto do usuário ou do modelo não escolhe destinos internos.

## Exfiltração e saída de dados

- Classificar o dado antes de enviá-lo a modelo, conector, API externa ou telemetria.
- Aplicar redação antes de chamadas externas: credenciais, dados pessoais, financeiros, segredos comerciais e conteúdo de outro tenant.
- Definir destinos externos permitidos por agente e por tipo de dado.
- Limitar o que a ferramenta retorna: campos mínimos e referências, não dumps.
- Verificar se o resultado contém segredo ou dado de outro tenant antes de entrar no envelope de contexto.
- Registrar destino, tipo de dado, ferramenta e finalidade, sem o conteúdo secreto.
- Screenshots, anexos, saída de terminal e mensagens de erro são canais de vazamento.

## Anonimização em chamadas de modelo e de API

Regra: o modelo recebe o mínimo de dado pessoal que a etapa precisa. O que não muda a resposta não sai do sistema.

```txt
mensagem do cliente ou resultado de API
  → detectar dado pessoal (regex + Presidio, ou PIIMiddleware)
  → trocar por marcador (<CPF_1>, <TEL_1>, <NOME_1>)
  → guardar o mapa marcador → valor só no servidor, com tempo de vida da conversa
  → chamar o modelo com o texto pseudonimizado
  → validar a saída
  → trocar os marcadores pelos valores só na mensagem que vai para o cliente
```

| Dado | Vai para o LLM? | Como |
| --- | --- | --- |
| CPF, RG, cartão, conta bancária | Não | Marcador; o código usa o valor real na ferramenta |
| Telefone e e-mail | Não | Marcador; o canal já sabe o contato |
| Nome | Só o primeiro nome, se a resposta usa | Marcador ou primeiro nome |
| Endereço | Só quando a etapa precisa | Campos mínimos |
| Saúde e financeiro | Só o necessário, com base legal registrada | Classificação sensível no mapa de dados |
| Senha, token, chave | Nunca | Bloqueio na entrada; caso SEC |

- O resultado de toda API passa pela mesma pseudonimização antes de entrar no envelope de contexto, e a ferramenta devolve só os campos que a etapa usa.
- Traces e logs recebem o texto já pseudonimizado. O mapa de marcadores nunca vai para trace, log, dataset ou memória.
- Provedor de modelo: usar a opção de não reter e não treinar com os dados quando o provedor oferecer, e registrar no ADR a política de retenção do provedor escolhido.
- Dataset de eval e de fine-tuning só com dado pseudonimizado e revisado.
- Cada regra tem caso na suíte de segurança: dado pessoal da entrada não aparece no trace; marcador nunca chega cru ao cliente.
- Segredos seguem "Segredos — regra obrigatória": .env cifrado com dotenvx e chaves no Bitwarden Secrets Manager, nunca no projeto, no prompt ou no trace.

## Segurança por fase do ciclo de vida

| Fase | O que a segurança exige |
| --- | --- |
| 1 e 2. Fundamentos e casos de uso | Classificar o dado e o risco do caso; decidir se dado sensível entra |
| 3 a 5. Componentes, stack e design | Mapa de dados com classificação; faixa de segurança no canvas; segredos no cofre desde o primeiro commit |
| 6. Build e teste | Suite SEC verde; red team com promptfoo a partir do porte M |
| 7. Deploy | Segredos injetados no deploy; webhook autenticado; banco em rede privada |
| 8. Monitorar | Alerta de vazamento e de uso anômalo de ferramenta; auditoria |
| 9. Otimizar | Revisão de segurança a cada troca de modelo, prompt ou ferramenta; rotação de chaves |

## Memória, cache e contexto persistente

- Separar memória por usuário, agente, cliente e tenant; memória nunca é fonte de autorização.
- Guardar proveniência, data, escopo, classificação e confiança de cada fato persistido.
- Instrução encontrada em conversa, e-mail, site ou documento não é promovida a memória de sistema.
- Validar origem, permissão e conteúdo antes de persistir, contra envenenamento de memória.
- Aplicar validade, retenção, exclusão e revisão; permitir invalidar fatos antigos.
- Isolar cache, embeddings, resultados de busca e checkpoints por tenant, com filtro no servidor.
- Nunca guardar segredo em memória conversacional, vetor, cache ou dataset.

## Aprovação de ações críticas

- Classificar ações por risco: leitura, escrita reversível, comunicação externa, alteração privilegiada, ação financeira, ação destrutiva.
- Exigir aprovação humana para operações críticas, financeiras, externas ou destrutivas.
- A aprovação vale para a ação exata: agente, usuário, tenant, ferramenta, parâmetros, recurso e validade. Mudou um parâmetro, a aprovação cai.
- Antes de agir, revalidar identidade, autorização, pré-condições, estado atual e validade da aprovação.
- Em infraestrutura e produção: planejar, ver o diff, revisar, aplicar, com plano de volta.
- Agente filho herda só o escopo delegado, nunca as permissões do agente pai.
- Limites de profundidade, chamadas, orçamento e duração para laços e cascatas.

## Checklist antes de uma tarefa técnica

- [ ] O agente recebeu só os dados necessários, sem valor de segredo?
- [ ] A ferramenta tem escopo e permissões mínimos?
- [ ] O ambiente é dev ou staging, ou há autorização explícita para produção?
- [ ] O segredo vem do cofre ou do runtime, sem passar pelo contexto do modelo?
- [ ] Saídas, logs, traces e mensagens de erro são sanitizados?
- [ ] Comandos e alterações de infraestrutura foram revisados antes?
- [ ] A ação é auditável, reversível ou tem plano de recuperação?
- [ ] Há confirmação humana para ações destrutivas, privilegiadas ou de alto impacto?

## Testes de validação

- [ ] Ferramenta com descrição ou schema adulterado exige nova revisão
- [ ] Servidor MCP não acessa arquivos nem redes fora do escopo
- [ ] Token de um serviço não funciona em outro
- [ ] Saída de ferramenta com token ou dado pessoal é redigida antes do contexto e dos logs
- [ ] Memória de outro usuário ou tenant não é recuperável
- [ ] Envio de dado sensível a destino não autorizado é bloqueado
- [ ] Parâmetro alterado depois da aprovação invalida a aprovação
- [ ] Laços, cascatas, timeouts e limites de orçamento testados
- [ ] Auditoria do n8n executada, achados corrigidos e auditoria repetida

Nenhuma ferramenta, conector ou servidor MCP novo recebe acesso a dados ou execução em produção antes de revisão de origem, schema, permissões, sandbox, saída de rede, logs e mecanismo de revogação.

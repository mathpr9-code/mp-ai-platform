# 5. Transferir e fechar — a máquina de decisão

Toda conversa termina em um de três estados, decididos por código: resolvida e fechada, transferida para humano, ou abandonada por tempo.

| Classe de gatilho | Exemplos | Quem dispara | Métrica que manda |
| --- | --- | --- | --- |
| Obrigatório | Fora do escopo, autoridade humana, risco acima do limite, falha técnica persistente, limite de esclarecimentos | Código, por regra (TR1) | Recall: nenhuma pode ser perdida |
| Semântico | Pedido de humano, insatisfação, assunto sensível | Extrator sinaliza o ato; código aplica a política (TR2) | Precisão e recall por tipo de sinal |

O extrator nunca devolve "transferir". Devolve o que foi dito, por exemplo o ato `pede_humano`; a política decide o que isso causa.

| Sinal na descoberta | Peça |
| --- | --- |
| Uma fila, regras claras | TR1 — regra determinística |
| Linguagem livre com sinais de risco | TR2 — sinal semântico mais guardrail |
| Aprovação humana no meio do processo, com retomada | TR3 — pausa e retomada; exige estado persistido |
| Vários setores, prioridade, SLA | TR4 — roteamento por fila |
| Passagem para outro agente ou sistema | TR5 — handoff entre agentes |
| Dependência de sistema externo instável | TR6 — fallback por timeout |

## Pacote de handoff

O resumo é redigido por LLM; todos os outros itens saem do estado, por código. Enquanto o humano atua, o agente não responde. A lista de campos e os estados estão em "Contrato completo de handoff", abaixo.

## Protocolo de entrega

Vale para todo agente, com ou sem redator. Entre decidir a resposta e o cliente receber existe o canal, e o canal falha.

- Toda saída vai para uma outbox com id do turno, chave de idempotência e status.
- Estados: pendente, aceita pelo provedor, entregue, lida, falhou, desconhecido. HTTP 200 significa só "aceita"; não inferir entrega.
- Reenvio agendado usa a mesma saída e a mesma chave. A máquina não decide de novo nem chama modelo.
- Estado desconhecido é reconciliado com o provedor antes de reenviar.
- Falha definitiva com atendimento pendente aciona a contingência do canal, normalmente transferência com nota operacional.

## Quando transferir

Transferir não é enviar uma mensagem dizendo que alguém entrará em contato. É um protocolo de handoff com decisão, roteamento, pacote, confirmação, estado e retomada.

- Pedido explícito de atendimento humano, conforme a política do cliente
- Caso fora do escopo ou da competência autorizada
- Decisão que exige autoridade humana
- Risco que excede o limite aprovado para automação
- Fonte insuficiente após as investigações previstas
- Contradição material que não pode ser resolvida com segurança
- Falha técnica persistente ou ausência de sistema crítico
- Cliente insatisfeito ou situação em que a política prevê intervenção humana

Não confundir: falta de informação que o cliente pode fornecer pede Esclarecer. Falta de registro ou decisão que pertence à empresa pede Investigar ou Transferir. Incapacidade do extrator de interpretar com segurança pede esclarecimento ou transferência, conforme o risco.

## Contrato completo de handoff

- Id da conversa e referência do cliente, dentro do escopo permitido
- Motivo e categoria da transferência
- Prioridade e destino ou fila
- Resumo factual da necessidade, sem inventar
- Interpretação estruturada e evidências relevantes
- Fontes consultadas e resultados
- Ações já executadas e status confirmado
- Perguntas feitas e respostas recebidas
- Pontos pendentes, contradições e incertezas
- Riscos e restrições
- Instruções para continuidade
- Estado e versão necessários para retomada

Estados explícitos, conforme o sistema de atendimento: requested, queued, accepted, assigned, in\\_progress, completed, failed ou cancelled.

## Continuidade e garantia de entrega do handoff

- Registrar a transferência antes de informar sucesso.
- Usar chave de idempotência para evitar tickets ou encaminhamentos duplicados.
- Confirmar o aceite pelo sistema de destino, quando disponível.
- Tratar timeout, falha e reenvio.
- Manter o contexto acessível à equipe autorizada.
- Definir se o agente fica pausado, encerrado ou apto a retomar.
- Evitar que agente e humano respondam ao mesmo tempo sem coordenação.
- Registrar quando o caso volta para a automação e qual estado foi atualizado.

## Métricas de Transferir

- Recall de transferências obrigatórias
- Precisão das transferências
- Falso negativo de escalonamento, por nível de risco
- Falso positivo e transferências desnecessárias
- Handoff iniciado contra aceito
- Qualidade do pacote e contexto preservado
- Tempo até o aceite e o primeiro atendimento humano
- Duplicidade ou perda de encaminhamento
- Continuidade após a retomada
- Resultado final do caso após a intervenção humana
- Conversas encerradas com pendência aberta: alvo zero
- Mensagens perdidas ou duplicadas na entrega: alvo zero
- O recall das transferências obrigatórias tem portão próprio

O objetivo não é reduzir o volume de transferências a qualquer custo. É transferir corretamente e com continuidade quando a autonomia deixa de ser apropriada.

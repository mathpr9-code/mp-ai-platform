# Entrada — do webhook ao Interpretar

Boa parte dos erros atribuídos ao extrator nasce antes dele: mensagem picada, áudio não transcrito, estado não carregado, última fala do agente ausente. A entrada é orquestrada por código e é igual para qualquer agente. O LLM entra aqui só para converter mídia em texto (transcrever áudio, descrever ou ler imagem) e não decide nada: o texto derivado segue marcado com a origem, como dado; o que muda por cliente são as peças de mídia e de buffer.

## Os seis passos da entrada

| Passo | O que faz | Por quê | O que direciona a escolha |
| --- | --- | --- | --- |
| 1. Receber | Valida a origem do webhook, grava a mensagem bruta e confirma o recebimento na hora | O provedor reenvia quando não recebe confirmação rápida; processar dentro do webhook gera duplicata | Sempre igual |
| 2. Deduplicar | Descarta mensagem com id já visto | Reenvio do provedor não pode virar segunda resposta | Sempre igual |
| 3. Normalizar por tipo | Converte tudo em texto: áudio transcrito, imagem descrita ou lida, documento extraído | O extrator trabalha com texto; sem isso, mídia vira mensagem vazia | Quais tipos o público do cliente realmente envia |
| 4. Buffer | Junta as mensagens enviadas em sequência em um turno só | A pessoa escreve em três mensagens o que é uma frase; sem buffer são três execuções e respostas atravessadas | Canal e hábito do público |
| 5. Trava por conversa | Garante uma execução por conversa por vez | Duas execuções simultâneas leem o mesmo estado e gravam por cima uma da outra | Sempre igual; muda só a tecnologia |
| 6. Carregar e montar | Lê histórico, estado, pendência aberta e a última fala do agente, e monta o envelope de contexto | Sem isso o extrator lê a mensagem solta | Sempre igual |

## Peças de mídia

| Peça | O que faz | Para que serve | Quando não usar |
| --- | --- | --- | --- |
| M1 — Só texto | Mídia recebe resposta padrão pedindo texto | Primeira versão, público que só escreve | Público que manda áudio com frequência |
| M2 — Áudio transcrito | Transcreve e segue como texto | Público que fala em vez de digitar | Quando o custo por minuto não cabe no orçamento |
| M3 — Imagem | Modelo de visão descreve ou lê o conteúdo | Comprovante, foto de produto, print de erro | Quando a imagem exige decisão que só humano pode tomar |
| M4 — Documento | Extrai o texto do arquivo | PDF de pedido, exame, contrato | Documento sensível sem política de tratamento |

Regras para qualquer peça de mídia: guardar o original e o texto derivado; marcar a origem do texto (digitado, transcrito, lido de imagem), porque transcrição erra e o extrator precisa saber; definir a resposta para tipo não suportado (figurinha, localização, contato), em vez de ignorar.

## Peças de buffer

| Peça | Como funciona | Para que serve | Custo |
| --- | --- | --- | --- |
| B1 — Sem buffer | Cada mensagem é um turno | Canal em que a pessoa manda uma mensagem por vez | Respostas atravessadas em canal de mensagem |
| B2 — Janela fixa | Espera um tempo fixo depois da primeira mensagem | Simples de implementar | Corta quem digita devagar; atrasa quem manda uma só |
| B3 — Janela deslizante | O tempo recomeça a cada mensagem nova, com um teto máximo | Padrão para WhatsApp | Precisa de armazenamento rápido com expiração e de teto |
| B4 — Adaptativo | Janela curta se a mensagem parece completa, longa se parece cortada | Reduz latência sem perder mensagem picada | Regra a mais para testar e manter |

Parâmetros que entram no quadro: duração da janela, teto máximo de espera e o que fazer quando chega mensagem nova durante o processamento (entra no próximo turno, ou cancela a resposta em andamento). Os valores são calibrados por cliente; não há número universal.

Os fluxos atuais em n8n já têm nós de tratamento de texto, áudio e imagem e de buffer. Eles são a referência de implementação dessas peças e ainda precisam ser documentados aqui, nó por nó.

## O turno é um par: fala do agente mais resposta do cliente

Uma resposta curta só tem significado junto com a pergunta que a provocou. O erro mais comum de interpretação é ler "sim", "não", "ok" ou "a segunda" soltos.

Exemplo do erro: o agente pergunta "Posso ajudar com mais alguma coisa?", o cliente responde "sim", e o fluxo transfere para humano. O "sim" foi lido como gatilho porque a pergunta do agente não estava no contexto do extrator e nenhuma regra ligava a resposta à pergunta.

A correção é estrutural, em cinco regras:

1. **Toda fala do agente é gravada com o que ela abriu.** Quando o agente pergunta, o código grava a pergunta aberta: o tipo de resposta esperada, as opções e o que cada resposta causa. Quem grava é o código, que conhece o ato que mandou redigir, não o modelo.
2. **O extrator sempre recebe a última fala do agente e a pendência aberta.** Ele devolve a qual turno a mensagem responde.
3. **O código resolve a resposta contra a pendência.** Confirmação mais pendência X produz o efeito definido em X, e só esse.
4. **Resposta curta sem pendência aberta nunca dispara ação.** Vira esclarecimento.
5. **Gatilho semântico exige ato explícito com evidência literal.** Transferir por pedido do cliente precisa do ato `pede_humano` ancorado em um trecho como "quero falar com atendente". Polaridade solta não é gatilho.

O que o código grava junto com a fala do agente:

```json
{
  "turno": "t7",
  "autor": "agente",
  "texto": "Posso ajudar com mais alguma coisa?",
  "movimento": "close",
  "pergunta_aberta": {
    "id": "p7",
    "tipo": "sim_nao",
    "sobre": "continuar_atendimento",
    "se_sim": "aguardar_novo_pedido",
    "se_nao": "encerrar_conversa",
    "expira_em_turnos": 1
  }
}
```

O que o extrator devolve para a resposta "sim":

```json
{
  "evidencias": [{"id": "ev1", "turno": "t8", "trecho": "sim"}],
  "atos": ["confirmacao"],
  "responde_a": "p7",
  "intencao": null,
  "campos": [],
  "ambiguidades": [],
  "fora_da_lista": false
}
```

O código lê `confirmacao` mais `p7`, aplica `se_sim` e pergunta em que mais pode ajudar. Nenhum caminho leva a Transferir.

| O agente disse | O cliente respondeu | Leitura solta, errada | Leitura como par, certa |
| --- | --- | --- | --- |
| "Posso ajudar com mais alguma coisa?" | "sim" | Pedido de humano | Quer continuar; perguntar o quê |
| "Quer que eu te passe para um atendente?" | "sim" | Confirmação genérica | Aceitou a transferência oferecida |
| "Confirma o agendamento para sábado às 10h?" | "não" | Encerrar | Recusou a confirmação; perguntar o que mudar |
| Apresentou duas opções | "a segunda" | Mensagem sem sentido | Escolheu a opção 2 |
| Nenhuma pergunta aberta | "ok" | Confirmação de alguma ação | Recebimento; não dispara nada |
| Perguntou a data | "quanto custa?" | Data inválida | Mudou de assunto; a pendência da data continua aberta |

## Como o estado volta para o Interpretar

```txt
resposta decidida
   ↓
grava evento: fala do agente + movimento + pergunta aberta
   ↓
envia pelo canal (outbox)
   ↓
... cliente responde ...
   ↓
ENTRADA: recebe, deduplica, normaliza, buffer, trava
   ↓
carrega: histórico (quem disse o quê, em ordem) + estado + pendências abertas + última fala do agente
   ↓
INTERPRETAR: lê a mensagem como resposta àquilo que estava aberto
   ↓
código: fecha a pendência respondida, mantém as outras, decide
```

O histórico que o extrator recebe traz sempre autor e ordem. Sem isso ele não distingue o que a IA disse do que o cliente disse.

Casos que toda suíte de erros tem desde o primeiro dia: "sim" depois de pergunta de encerramento; "sim" depois de oferta de transferência; "não" depois de pedido de confirmação; "ok" sem pergunta aberta; "a segunda" depois de opções; mudança de assunto com pendência aberta; resposta a uma pergunta de dois turnos atrás.

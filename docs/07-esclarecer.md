# 4. Esclarecer — a pergunta mínima

Quem decide que falta algo é o código; o LLM só formula a pergunta.

Antes de perguntar, o código verifica nesta ordem:

1. O dado já está no histórico ou no estado?
2. Um sistema pode responder?
3. O cliente é a pessoa certa para responder, ou a lacuna é interna?
4. Qual o custo de seguir com a leitura mais provável e confirmar junto com a resposta?

Lacuna interna vai para Transferir, não para o cliente.

| Tipo de lacuna | De onde vem o sinal | Peça |
| --- | --- | --- |
| Campo obrigatório ausente | Código compara estado com campos exigidos | ESC1 — guiado por campo |
| Referência ou intenção ambígua | `ambiguidades` do extrator | ESC2 — guiado por ambiguidade |
| Várias lacunas ao mesmo tempo | Código ordena pela que destrava mais | ESC3 — maior ganho de informação |
| Ação com consequência | Política marca "confirmar antes" | ESC4 — escolha ou confirmação |
| Resposta do cliente não encaixou | Ato incompatível com a pendência | ESC5 — reparo |
| O cliente não é a fonte | Política | ESC6 — esclarecimento com humano |

Parâmetros do canvas, como pontos de partida a calibrar: uma pergunta por turno; duas tentativas para a mesma lacuna antes de transferir; lista de condutas que exigem confirmação.

O benchmark CLAMBER (ACL 2024) relatou que LLMs têm dificuldade em identificar ambiguidade e que chain-of-thought e few-shot trouxeram ganho marginal em parte das tarefas. Por isso o gatilho fica em sinais que o código lê.

## Tipos de lacuna e conduta

| Tipo | Exemplo | Conduta |
| --- | --- | --- |
| Ambiguidade linguística | "Pode ser aquela opção", sem âncora clara | Perguntar qual opção, se a âncora não puder ser recuperada |
| Campo obrigatório ausente | Falta a data necessária para uma operação | Solicitar o campo específico |
| Conflito entre informações | Duas datas diferentes na conversa | Confirmar qual substitui a anterior |
| Preferência não definida | Cliente ainda não escolheu entre alternativas | Apresentar opções relevantes |
| Fonte interna ausente | O cliente pergunta um dado que a empresa deveria possuir | Investigar outra fonte ou transferir; não obrigar o cliente a suprir a lacuna interna |
| Risco ou autoridade | Solicitação que exige aprovação humana | Transferir ou solicitar aprovação; não tratar como simples esclarecimento |

## Política de perguntas

Uma boa política de esclarecimento:

- Pergunta apenas o que é necessário para avançar.
- Prefere uma pergunta por vez quando as respostas dependem uma da outra.
- Não repete algo que já foi informado e validado.
- Não pergunta ao cliente dados que o sistema poderia consultar.
- Explica a razão quando a pergunta não é óbvia.
- Oferece alternativas quando isso reduz esforço.
- Preserva contexto e resposta anterior.
- Distingue "não sei", "não quero informar" e "não entendi".
- Para de insistir quando a pessoa não pode ou não deseja responder.

A decisão de perguntar considera a consequência de seguir com uma suposição, a capacidade do usuário de responder e o custo de mais um turno. Não otimizar apenas "quantas perguntas foram feitas": o objetivo é reduzir incerteza e aumentar a chance de resolução com o menor esforço razoável.

## Métricas de Esclarecer

- Precisão: perguntas realmente necessárias
- Recall: ambiguidades e lacunas relevantes identificadas
- Taxa de perguntas redundantes
- Taxa de pergunta ao interlocutor errado
- Número de turnos até a resolução
- Taxa de respostas úteis à pergunta
- Abandono após esclarecimento
- Sucesso da tarefa após a pergunta
- Esforço do usuário e qualidade da continuidade

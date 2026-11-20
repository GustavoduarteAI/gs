# Integração com o Fala, Lavoura!

O grupo entrega dois projetos na Global Solution 2026.2 sobre o mesmo problema: a assistência técnica não chega à maioria dos agricultores familiares.

| | Fala, Lavoura! | Mutirão |
| :- | :- | :- |
| Disciplina | Generative AI and Advanced Nets | AI for Robotic Process Automation |
| Lado | Frente: conversa com o agricultor | Bastidores: organiza o trabalho do técnico |
| Técnica central | Agente com RAG híbrido, clima, FAO-56, guardrails e Fiscal da Roça | RPA com Selenium, I/O, Excel e PLN clássico (Dicionário da Roça + TF-IDF + Regressão Logística) |
| Quando chama uma pessoa | Risco, emergência ou "não sei": grava na fila do técnico | Confiança baixa, assunto fora da ATER ou emergência de saúde: manda para a revisão do técnico |

## O caminho de um caso

1. A agricultora pergunta ao Fala, Lavoura!: *"Quanto de veneno eu ponho na bomba pra matar a lagarta?"*
2. Os guardrails do Fala, Lavoura! barram a dose, a lavoura responde em primeira pessoa e grava uma ficha anonimizada em `dados/fila_tecnico.jsonl` com o semáforo e o motivo.
3. A fila é copiada para `entrada/` do Mutirão (ou o modo `vigiar` a pega sozinho).
4. O Mutirão lê o JSONL linha a linha, transforma a ficha no formato dele (`FL-5443655f`), valida, classifica como **pragas**, prioriza e registra no sistema de ATER: protocolo `ATER-2026-000016`, Fitossanidade, prazo de 7 dias.
5. O Mutirão grava em `saida/retorno_fala_lavoura.jsonl` uma linha com `id_ficha`, protocolo, prioridade, equipe, prazo e a mensagem para a agricultora. O Fala, Lavoura! pode usar essa linha para trocar o status "aguardando técnico" por "protocolo ATER-2026-000016, técnico em até 7 dias".

## Contrato dos arquivos

**Entrada (escrita pelo Fala, Lavoura!, lida pelo Mutirão)**: um JSON por linha, como gravado por `falalavoura/fila.py`.

| Campo da ficha | Vira no Mutirão | Uso |
| :- | :- | :- |
| `id` | `id_solicitacao = "FL-" + id` | Idempotência e retorno |
| `quando` (`dd/mm/aaaa hh:mm`) | `data_hora` | Validação (aceita esse formato e ISO) |
| `municipio` (`"Campinas, SP"`) | `municipio` | Validação e clima no centro do município |
| `cultura` | `cultura` | Formulário e mensagem |
| `pergunta` + `o_que_a_foto_mostra` | `descricao` | Texto classificado (a descrição da foto feita pelo Gemini entra como contexto) |
| `semaforo` | `semaforo_ia` | Vermelho soma 2 pontos na prioridade |
| `motivo_do_encaminhamento` | `motivo_ia` | "Emergência" vira risco; "intoxicação" manda direto para o técnico com a mensagem de emergência |

Campos como `resposta_dada_pela_ia` e `fontes_consultadas` não são usados: o técnico vê a pergunta original, e o robô não depende do texto gerado.

**Saída (escrita pelo Mutirão, para o Fala, Lavoura!)**: `saida/retorno_fala_lavoura.jsonl`, aberto em modo de acréscimo (`"a"`), uma linha por ficha processada.

```json
{"id_ficha": "5443655f", "status": "registrada", "protocolo": "ATER-2026-000016", "prioridade": "MÉDIA",
 "assunto": "pragas", "equipe": "Casa da Agricultura - Fitossanidade (pragas)", "prazo_dias": 7,
 "mensagem": "Olá! Seu pedido sobre praga na lavoura (milho) em Campinas foi registrado...",
 "atualizado_em": "2026-11-18T19:42:40"}
```

`status` pode ser `registrada`, `revisao_humana`, `pendente` ou `rejeitada`. Exemplo completo em [evidencias/retorno_fala_lavoura_exemplo.jsonl](evidencias/retorno_fala_lavoura_exemplo.jsonl).

## O que os dois compartilham

- **Dicionário da Roça** ([dados/dicionario_da_roca.json](../dados/dicionario_da_roca.json)): o mesmo arquivo. No Fala, Lavoura! ele expande a consulta antes da busca nas fichas técnicas (o acerto da busca subiu de 66% para 82%). No Mutirão ele expande o texto antes do TF-IDF. No teste escrito à mão, o mesmo modelo acerta 92,6% com o dicionário e 88,9% sem ele. Ele corrige, por exemplo, "Minha DAP venceu, como faço o CAF novo?", que sem o dicionário cai em "outros".
- **Protocolo de emergência:** os dois usam os mesmos telefones (SAMU 192 e Disque-Intoxicação 0800 722 6001) e a mesma regra: intoxicação nunca depende só da máquina.
- **Linguagem simples:** as mensagens do Mutirão seguem o tom curto do Fala, Lavoura!, prontas para WhatsApp ou para virar áudio no gTTS.
- **Anonimização em duas camadas:** a ficha já sai anonimizada do Fala, Lavoura!, e o Mutirão mascara de novo CPF, telefone e e-mail de qualquer canal.

## Casos reais da fila nos testes

As quatro primeiras fichas do lote de entrada são casos que o Fala, Lavoura! encaminhou de verdade durante os testes do app.

| Ficha | Pergunta | Fala, Lavoura! | Mutirão |
| :- | :- | :- | :- |
| `87a630e1` | "como está o aquecimento?" | Amarelo: a base não cobre | Revisão do técnico (confiança 30%) |
| `5443655f` | "Quanto de veneno eu ponho na bomba pra matar a lagarta?" | Amarelo: pede técnico | Protocolo, pragas, MÉDIA |
| `70537f0c` | "Minha esposa passou veneno e está tonta e vomitando" | Vermelho: emergência | Técnico no topo da fila, URGENTE, mensagem com 192 e 0800 |
| `06b88330` | "Como planta quinoa" | Amarelo: a base não cobre | Revisão do técnico (confiança 36%) |

## Próximos passos da integração

- Fazer o Fala, Lavoura! ler o `retorno_fala_lavoura.jsonl` e mostrar o protocolo na conversa (hoje o arquivo é gerado, mas o app de GenAI ainda não o consome).
- Trocar a cópia de arquivo por uma pasta compartilhada ou uma fila de mensagens.
- Quando o técnico responder um caso, a resposta validada pode virar uma nova ficha técnica no RAG do Fala, Lavoura!.

# Proteção de dados, ética e ODS

## Resumo

O Mutirão usa apenas dados sintéticos e uma API pública sem chave, mas trata os dados como reais, seguindo os princípios de finalidade, necessidade e segurança da LGPD (Lei 13.709/2018). O nome vira pseudônimo; CPF, telefone e e-mail no texto são mascarados antes de chegar ao modelo, ao sistema de ATER ou ao relatório; e só o centro do município sai da máquina, para a previsão do tempo. Toda prioridade tem justificativa, baixa confiança vai para uma pessoa, emergência de saúde nunca fica só com o robô e ninguém fica sem resposta. O principal risco é o viés de acesso: o robô só vê quem consegue pedir. O protótipo contribui com os **ODS 2** (agricultura sustentável), **13** (adaptação ao clima), **3** (saúde) e **10** (redução das desigualdades, se o viés for monitorado).

## 1. Proteção de dados

| Princípio | Implementação |
| :- | :- |
| **Dados sintéticos** | Nomes, CPFs, telefones e textos inventados ([dados/gerar_dados.py](../dados/gerar_dados.py)). As fichas do Fala, Lavoura! vêm dos testes do app, já sem dados pessoais. |
| **Minimização** | O nome vira pseudônimo (`agr_xxxxxxxxxx`, SHA-256 com segredo no `.env`) e não aparece em nenhuma saída. |
| **Texto livre** | CPF, telefone e e-mail viram `[CPF]`, `[TELEFONE]` e `[EMAIL]` antes de qualquer etapa ([src/validacao.py](../src/validacao.py)). |
| **Localização** | A coordenada do sítio fica só no relatório interno, para os focos regionais. A API de clima recebe só o centro do município, arredondado. |
| **Nada pessoal sai da máquina** | Sem LLM externo na triagem. O retorno ao Fala, Lavoura! leva só o id da ficha, protocolo, assunto, equipe, prazo e a mensagem. |
| **Credenciais** | Senha do sistema de ATER e segredo do pseudônimo no `.env`, fora do Git. |
| **Transparência** | O log registra que houve mascaramento, nunca o dado. |

Num sistema real ainda seria preciso definir a retenção dos relatórios, controlar o acesso a `saida/` e informar o agricultor sobre o uso dos dados, de preferência em áudio e em linguagem simples.

## 2. Ética

- **Sem caixa-preta:** cada prioridade tem justificativa em texto, por exemplo *"assunto doencas (peso 2); chuva favorece doença de fungo: 21.0 mm em 3 dias (+2)"*.
- **O robô sabe quando não sabe:** baixa confiança e assuntos fora da ATER vão para o técnico (8 de 8 pedidos fora do escopo retidos no teste). Casos de risco são marcados como URGENTE mesmo na revisão.
- **Saúde primeiro:** suspeita de intoxicação vai para o técnico mesmo com confiança alta, e a resposta automática já diz o que fazer e para quem ligar, igual ao protocolo do Fala, Lavoura!.
- **Ninguém é descartado:** pedido rejeitado recebe mensagem dizendo o que faltou.
- **O técnico é realocado, não substituído:** sai da digitação e volta para o campo e para os casos que exigem julgamento.
- **O robô não recomenda produto nem dose:** ele só organiza a fila. A orientação continua com o técnico e o receituário agronômico.

### Riscos

| Risco | Impacto | Mitigação |
| :- | :- | :- |
| **Viés de acesso** | Comunidades sem sinal, sem cooperativa ou com pouca leitura pedem menos e parecem ter menos problemas; o KMeans pode reforçar isso. | Manter o balcão e o sindicato como canais; o Fala, Lavoura! aceita áudio; comparar os focos com o número de propriedades por município. |
| **Jeito de falar** | Regionalismos fora do Dicionário da Roça reduzem a confiança do modelo. | Dicionário compartilhado e fácil de ampliar; TF-IDF por letras; baixa confiança vai para o técnico, e esse atraso deve ser monitorado. |
| **Regras de urgência ingênuas** | Falar em "criança" já eleva a prioridade; "perdi tudo no ano passado" gera alarme falso; "o assentamento inteiro" não é reconhecido. | Preferência pela cautela; regras centralizadas e fáceis de revisar; erros listados em [evidencias_validacao.md](evidencias_validacao.md). |
| **Clima no centro do município** | Geada em baixada ou calor em encosta podem ser diferentes da previsão. | O clima só soma pontos e nunca rebaixa um pedido; a justificativa mostra os números. |
| **Confiança excessiva** | Com o tempo, ninguém confere o robô. | Relatório por execução, log detalhado e fila de revisão separada. |
| **Treino artificial** | O modelo aprende vícios dos templates (GIGO). | Retreinar com pedidos reais anonimizados e rotulados por técnicos de fora da equipe. |

## 3. ODS

| ODS | Meta | Contribuição |
| :- | :- | :- |
| **2. Fome zero e agricultura sustentável** | 2.3 e 2.4: dobrar a produtividade e a renda dos pequenos produtores; sistemas de produção resilientes | Pedido de praga, doença ou água chega mais rápido ao técnico certo; crédito e mercados públicos (Pronaf, PAA, PNAE) entram na mesma fila. |
| **13. Ação contra a mudança do clima** | 13.1: resiliência e capacidade de adaptação a riscos climáticos | Geada, calor sem chuva e chuva que favorece fungo sobem a prioridade antes do dano. |
| **3. Saúde e bem-estar** | 3.9: reduzir mortes e doenças por produtos químicos perigosos | Suspeita de intoxicação por agrotóxico nunca espera na fila: vai ao técnico e o agricultor recebe na hora os telefones de emergência. |
| **10. Redução das desigualdades** | 10.2: inclusão de todos | Vários canais, inclusive balcão físico, e nenhum pedido descartado. Só contribui de fato se o viés de acesso for acompanhado. |

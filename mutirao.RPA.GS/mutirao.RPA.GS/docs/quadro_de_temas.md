# Quadro de temas

Seis temas da disciplina, cada um com função real no fluxo. O critério de escolha foi: o tema resolve parte do problema ou só estaria ali para constar?

## Tema 1: Automação web com Selenium

| | |
| :- | :- |
| **Onde** | T6, [src/rpa_portal.py](../src/rpa_portal.py) |
| **O que resolve** | Substitui a digitação do técnico: login no sistema de ATER, preenchimento do formulário (assunto, município, comunidade, cultura, descrição, prioridade e equipe), registro e leitura do protocolo. |
| **Por que** | Sistemas públicos antigos raramente têm API; automatizar pela interface é o caso clássico de RPA. |
| **Detalhes** | Esperas explícitas (`WebDriverWait`) em vez de `sleep`; retry em erro 503; print da tela em falhas; Edge como alternativa se o Chrome não abrir; navegador sempre fechado (context manager); senha errada não gera tentativas repetidas de login. |
| **Sistema simulado** | Automatizar um sistema público real com dados sintéticos geraria protocolos falsos. O portal local reproduz login, formulário e protocolo (`ATER-2026-000001`) e pode simular instabilidade (erro 503). |

## Tema 2: Arquivos e I/O

| | |
| :- | :- |
| **Onde** | T1, [src/leitura.py](../src/leitura.py); modo `vigiar` em [main.py](../main.py); estado em [src/resiliencia.py](../src/resiliencia.py); retorno em [src/pipeline.py](../src/pipeline.py) |
| **O que resolve** | Lê a fila do técnico do Fala, Lavoura! (JSONL), CSV em CP1252 com `;` (balcão da Casa da Agricultura), CSV em UTF-8 (cooperativa), Excel (sindicato rural) e JSON (site). Grava o retorno ao Fala, Lavoura! em JSONL. |
| **Por que** | Os pedidos chegam como arquivo, cada canal num formato e encoding. A integração com o projeto de GenAI também é por arquivo. |
| **Conceitos aplicados** | **Encoding:** detecção com `charset_normalizer` e fallback UTF-8 → CP1252. **Chunking:** CSV lido em blocos de 500 linhas, só com as colunas necessárias e como texto. **Streaming linha a linha:** o JSONL é lido com um generator; uma linha cortada é registrada no log e pulada, sem perder as outras fichas. **Buffering:** hash SHA-256 calculado em blocos de 64 KB. **Modos:** `x` para o motivo da quarentena (nunca sobrescreve), `a` para o retorno ao Fala, Lavoura! (só acrescenta), estado gravado em `.tmp` e trocado de forma atômica. **Context manager:** todo arquivo aberto com `with`. **watchdog:** detecta arquivos novos e espera a cópia terminar. |

## Tema 3: Automação de Excel

| | |
| :- | :- |
| **Onde** | T1 (leitura) e T9 (relatório), [src/relatorio.py](../src/relatorio.py) |
| **O que resolve** | Entrega o relatório pronto para a Casa da Agricultura: resumo com indicadores e gráfico por assunto e prioridade, abas por situação (Registradas, Revisão do técnico, Rejeitadas, Pendentes, Focos regionais, Arquivos lidos), cores por prioridade, filtros e cabeçalho congelado. |
| **Por que** | A ATER trabalha com Excel. Calamine lê rápido (com fallback para openpyxl); XlsxWriter permite formatação condicional e gráficos. |
| **Resiliência** | Se a planilha estiver aberta no Excel, o relatório JSON é gerado mesmo assim. |

## Tema 4: Tratamento de erros e logs

| | |
| :- | :- |
| **Onde** | Todas as tarefas; [src/resiliencia.py](../src/resiliencia.py) e [src/logs.py](../src/logs.py) |
| **O que resolve** | Nenhuma falha previsível interrompe a execução inteira. |
| **Por que** | É o que diferencia um script de um robô. No campo, internet instável é a regra. |

| Falha | Caminho seguro |
| :- | :- |
| API de clima fora do ar | Timeout e 3 tentativas com espera crescente (1 s, 2 s); depois, última previsão salva (até 12 h) ou segue sem o critério de clima. Após 2 falhas seguidas, o disjuntor suspende a API na execução. |
| Sistema de ATER fora do ar | Checagem de saúde antes de abrir o navegador; pedidos vão para pendentes e são reprocessados na próxima execução. |
| Sistema instável (503) | Retry com espera exponencial em cada cadastro. |
| Senha errada | Sem novas tentativas de login; pedidos vão para pendentes. |
| Arquivo corrompido | Quarentena com o motivo; os demais seguem. |
| Linha quebrada na fila do Fala, Lavoura! | Só a linha é pulada (com aviso no log); as outras fichas do arquivo seguem. |
| Arquivo ausente | Registro no log; execução continua. |
| Arquivo de estado bloqueado (OneDrive, antivírus) | Até 10 novas tentativas de gravação; em último caso, gravação direta. |
| Dado inválido | Aba "Rejeitadas" com motivo e mensagem ao agricultor. |
| Execução repetida | Idempotência: nada é cadastrado em dobro. |
| Reenvio corrigido de pedido rejeitado | Assinatura do conteúdo detecta a mudança e o pedido é processado. |
| Dicionário da Roça ausente ou ilegível | O robô classifica sem ele e avisa no log. |
| Erro inesperado | `try/except` final no `main.py` grava o traceback no log. |

Logs no console e em `saida/logs/`, no formato `hora | nível | módulo | mensagem`, com a tarefa (T1 a T9) em cada linha.

## Tema 5: RPA + IA/PLN (HyperAutomation)

| | |
| :- | :- |
| **Onde** | T4 (classificação) e T8 (focos regionais), [src/modelo.py](../src/modelo.py) |
| **O que resolve** | Interpreta o texto livre do agricultor ("tem uns bichinhos verdes grudados embaixo da folha", "minha DAP venceu") e informa o assunto e a confiança. |
| **PLN** | (1) Normalização: minúsculas e sem acento. (2) **Expansão com o Dicionário da Roça**, o mesmo recurso do Fala, Lavoura!: 88 expressões populares ganham o termo técnico ao lado ("dinheiro do banco" → "pronaf crédito rural"). (3) TF-IDF de palavras (uni e bigramas) e de trechos de 3 a 5 letras, que toleram erro de digitação e escrita falada. (4) Regressão Logística com `class_weight="balanced"`, porque a base é desbalanceada de propósito (160 exemplos de pragas, 70 de crédito). |
| **Classe "outros"** | Pedidos que não são de assistência técnica (estrada, energia, documento, festa) têm um rótulo próprio e vão sempre para o técnico, nunca para o sistema de ATER. Na primeira rodada, sem essa classe, só 4 de 8 pedidos fora do escopo foram retidos; com ela, 8 de 8. |
| **Limiar** | Abaixo de 40% de confiança, a decisão vai para o técnico. O valor sai de uma regra fixa (maior acerto no automatizado com pelo menos 65% de automação), validada com validação cruzada aninhada. |
| **Emergência de saúde** | Intoxicação por agrotóxico vai para o técnico mesmo com confiança alta, e a mensagem ao agricultor já traz os telefones de emergência. |
| **Integração** | `MODELO_EXTERNO` no `.env` permite usar um modelo treinado em outra disciplina; se for inválido, o robô volta ao próprio. O semáforo e o motivo do Fala, Lavoura! entram como critérios de prioridade. |
| **KMeans** | Agrupa os pedidos registrados pela localização e mostra focos regionais (municípios, assunto mais comum, culturas e quantos são de prioridade alta), com link para o mapa. Serve para planejar dias de campo e visitas coletivas. |
| **Por que não XGBoost** | Base pequena e textual; a Regressão Logística treina em menos de 1 s e mostra o peso de cada palavra. |
| **Por que não LLM** | A IA generativa já está no Fala, Lavoura!, na conversa. Na triagem, um modelo próprio roda offline (internet no campo é ruim), sem custo, não envia o texto do agricultor a terceiros e dá sempre a mesma resposta para o mesmo texto. |

## Tema 6: BPM + qualidade de dados (GIGO)

| | |
| :- | :- |
| **Onde** | [docs/processo_as_is_to_be.md](processo_as_is_to_be.md); tarefas T1 a T9 em [src/pipeline.py](../src/pipeline.py); T3 em [src/validacao.py](../src/validacao.py) |
| **O que resolve** | O mapeamento AS-IS/TO-BE separa o repetitivo (triagem e digitação, para o robô) do que exige julgamento (casos ambíguos e emergências, para o técnico). As relações entre tarefas definem o código: a prioridade (T5) depende do assunto (T4) e o registro (T6) só ocorre após a validação (T3). |
| **GIGO** | Descrição curta, data no futuro ou inválida, município desconhecido sem coordenada dentro do estado e duplicatas são barradas antes do modelo. Dados pessoais são mascarados nessa etapa. A data do Fala, Lavoura! (`dd/mm/aaaa`) é aceita junto com o ISO dos outros canais. |
| **Monitorar** | Indicadores de cada execução no JSON e na aba Resumo, incluindo os retornos ao Fala, Lavoura!. |

**Complemento:** psutil registra memória e CPU de cada execução.

## Temas não usados

| Tema | Motivo |
| :- | :- |
| UiPath, Automation Anywhere, Blue Prism | Python é gratuito, multiplataforma e versionável no Git. |
| PyAutoGUI | Depende de coordenadas e resolução de tela; o Selenium interage direto com os elementos da página. |
| Pywinauto | O sistema legado é web, não desktop. |
| mmap, Dask, Vaex | Volume pequeno; o chunking do pandas atende. |
| Mineração de processos | Os logs já têm formato de eventos; fica como próximo passo. |
| Aprendizado por reforço | Não há ambiente com recompensa clara. |
| Tooling + MCP | O LLM fica no Fala, Lavoura!; o robô não chama modelo de linguagem. |

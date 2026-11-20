# Fábrica de Corpus CitizenTech — Agricultura Familiar

Ferramenta em Python que transforma documentos públicos sobre agricultura familiar em três
corpus prontos para o fine-tuning de um SLM voltado ao atendimento do cidadão.

**Global Solution | Processamento de Linguagem Natural, Chatbots e Virtual Agents**
Prof. Dr. Sérgio Eduardo Palmiere | FIAP | Turma 2TIAPR

## Integrantes

| Nome completo | RM | Turma |
|---|---|---|
| Claudio Alves | 568565 | 2TIAPR |
| Gustavo Duarte | 567066 | 2TIAPR |
| Leonardo Pereira | 567836 | 2TIAPR |

## O problema

O governo mantém um conjunto grande de políticas para a agricultura familiar: CAF, Pronaf,
Garantia-Safra, assistência técnica. As regras existem e estão publicadas. O que atravessa
no meio é a distância entre o documento e quem precisa dele. E no campo a internet é ruim o
ano inteiro, então um assistente que depende de nuvem falha com frequência exatamente onde
seria mais útil. Um SLM cabe num celular e continua respondendo offline, desde que tenha
sido treinado antes com o conteúdo certo. É esse conteúdo que esta ferramenta produz.

**Persona:** Dona Alzira, 54 anos, três hectares, planta feijão e milho. As perguntas dela
são "eu me encaixo?", "perdi a lavoura, eu tinha direito a alguma coisa?" e "em que porta eu
bato?". **ODS:** meta 2.3 (principal), 2.4 e 1.4.

## Como executar

### No Google Colab (recomendado)

1. Abra `GS_Fabrica_Corpus_CitizenTech.ipynb` no Colab.
2. `Ambiente de execução > Alterar tipo de ambiente > T4 GPU` (opcional; só acelera a
   seção 7.4, que é um experimento).
3. `Ambiente de execução > Executar tudo`.

A primeira célula instala as dependências (cerca de 1 minuto) e o notebook baixa sozinho os
documentos oficiais. Não é preciso subir nada à mão. No fim, a interface Gradio sobe com um
link público.

### Na sua máquina

```bash
pip install pypdf pdfplumber python-docx beautifulsoup4 lxml transformers torch spacy gradio
python -m spacy download pt_core_news_sm
python baixar_fontes.py
```

Depois é só abrir o notebook e executar as células na ordem. O `baixar_fontes.py` repõe a
pasta `fontes/` do zero, então dá para apagar os documentos e reproduzir tudo.

> O site do Planalto derruba a conexão com frequência. O downloader insiste até 12 vezes e,
> se ainda assim falhar, usa o espelho oficial do LexML.

## O que está aqui

| Caminho | O que é |
|---|---|
| `GS_Fabrica_Corpus_CitizenTech.ipynb` | o notebook, com as células já executadas |
| `fontes/` | os cinco documentos de entrada e o manifesto `FONTES.json` com as URLs |
| `corpus/` | os três `.jsonl` gerados e `estatisticas.json` |
| `RELATORIO.pdf` | o relatório exigido pelo enunciado |
| `RELATORIO.md` | o texto que gera o PDF |
| `AI_CONTEXT_PACKAGE.md` | pacote de contexto do projeto |
| `integrantes.txt` | nomes e RMs |
| `link_video.txt` | link do vídeo de demonstração |
| `baixar_fontes.py` | baixa as cinco fontes oficiais, para reproduzir a entrega do zero |

## Bibliotecas usadas

| Biblioteca | Para quê |
|---|---|
| `pypdf` e `pdfplumber` | extração de PDF; rodamos os dois e ficamos com o melhor por documento |
| `python-docx` | extração de DOCX, incluindo o texto das tabelas |
| `beautifulsoup4` + `lxml` | extração de HTML |
| `spacy` + `pt_core_news_sm` | reconhecimento de nomes de pessoa para a anonimização |
| `transformers` | tokenizer do modelo alvo (contagem de tokens) e o LLM do experimento |
| `torch` | backend do `transformers` |
| `gradio` | interface |

Tudo o mais é biblioteca padrão do Python (`re`, `json`, `unicodedata`, `collections`,
`hashlib`, `random`, `urllib`).

## Fontes dos documentos

| Formato | Documento | Órgão | Link |
|---|---|---|---|
| PDF | Como acessar Crédito Rural pelo Pronaf | MDA | [notícia oficial do MDA](https://www.gov.br/mda/pt-br/noticias/2024/10/cartilha-201ccomo-acessar-credito-rural-pelo-pronaf-passo-a-passo-para-a-agricultura-familiar201d-e-lancada-em-brasilia) e [PDF](https://www.conexsus.org/validacao/wp-content/uploads/2024/11/cartilha-pronaf-final.pdf) |
| PDF | Orientações do Programa Garantia-Safra | Ministério da Agricultura | [gov.br/mda](https://www.gov.br/mda/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/programa-garantia-safra/arquivos/manual6_atualizado_julho2019_orient-doc.pdf) |
| DOCX | Modelo de contrato de ATER | MDA | [gov.br/mda](https://www.gov.br/mda/pt-br/acesso-a-informacao/copy_of_acoes-e-programas/credito/manuais-e-formularios/modelo-contrato-de-ater-decred-13-04.21) |
| HTML | Lei 10.420/2002, Fundo Garantia-Safra | Planalto | [planalto.gov.br](https://www.planalto.gov.br/ccivil_03/leis/2002/l10420.htm) |
| TXT | Avisos meteorológicos oficiais | INMET | [apiprevmet3.inmet.gov.br](https://apiprevmet3.inmet.gov.br/avisos/ativos) |

Todos são documentos públicos de órgãos oficiais. A cartilha do Pronaf é distribuída pelo
link que a própria notícia do MDA publica, e a página do ministério informa que a reprodução
é gratuita desde que citada a fonte. O manifesto completo, com data de coleta, está em
`fontes/FONTES.json`.

## Formato dos corpus

```jsonl
# corpus_texto.jsonl
{"text": "...", "fonte": "cartilha_pronaf_credito_rural.pdf"}

# corpus_qa.jsonl
{"instruction": "Aposentadoria também entra como renda da família?", "input": "", "output": "...", "fonte": "..."}

# corpus_chat.jsonl
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."},
              {"role": "assistant", "content": "..."}, ...], "fonte": "..."}
```

## Uso de IA neste trabalho

O corpus de perguntas e respostas é gerado por regras sobre a estrutura dos documentos, e a
resposta é sempre extraída do texto de origem. A seção 7.4 do notebook é um experimento
separado que usa o **Qwen2.5-1.5B-Instruct** para gerar pares; o prompt está na variável
`PROMPT_QA` e no relatório. Todos os pares gerados por LLM passam pelo verificador
automático de fidelidade antes de entrar no corpus, e os reprovados ficam registrados nas
estatísticas. Além disso, a célula seguinte imprime uma amostra de 25% desses pares (acima
dos 20% exigidos) com o veredito do verificador ao lado, para a revisão manual do grupo.

Também usamos assistente de IA como apoio durante o desenvolvimento, para revisar código e
discutir alternativas de implementação. As decisões de projeto, os limiares, as fontes e a
redação dos exemplos de recusa são do grupo.

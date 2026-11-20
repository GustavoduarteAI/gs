# AI Context Package — Fábrica de Corpus CitizenTech

Documento de contexto gerado com apoio de IA, conforme a regra 6 das Regras do Jogo da
disciplina. Serve para que outra pessoa (ou outro agente de IA) consiga retomar este
projeto sem precisar ler o código inteiro.

---

## 1. Identificação

| Campo | Valor |
|---|---|
| Entrega | Global Solution, Fábrica de Corpus CitizenTech |
| Disciplina | Processamento de Linguagem Natural, Chatbots e Virtual Agents |
| Professor | Dr. Sérgio Eduardo Palmiere |
| Instituição / turma | FIAP, turma 2TIAPR |
| Grupo | Claudio Alves (568565), Gustavo Duarte (567066), Leonardo Pereira (567836) |
| Tema CitizenTech | Agricultura familiar: CAF, Pronaf, Garantia-Safra e assistência técnica |
| ODS | 2.3 (principal), 2.4 e 1.4 |

## 2. O que o projeto faz

Recebe documentos públicos em PDF, TXT, DOCX, HTML ou texto colado e devolve três corpus em
JSONL prontos para o fine-tuning de um SLM: texto puro, perguntas e respostas e
conversacional. Não treina modelo; o escopo acaba no corpus, como o enunciado define.

## 3. Arquitetura, em ordem de execução

```
baixar fontes oficiais (com espelho do LexML quando o Planalto cai)
   └─ extrair (pypdf | pdfplumber | python-docx | BeautifulSoup | texto cru)
        └─ PORTÃO DE QUALIDADE (4 medidas, 2 passadas)  ← passo extra do grupo
             └─ limpar (cabeçalho, rodapé, numeração, URL, hífen, marca de InDesign)
                  └─ normalizar (NFC, aspas, traços, espaços; mantém acento e maiúscula)
                       └─ anonimizar (CPF, CNPJ, e-mail, telefone, CEP, nome)
                            │   ← TESTE ADVERSARIAL do grupo mede o recall
                            └─ segmentar em 256–512 tokens do tokenizer do modelo alvo
                                 ├─ corpus_texto.jsonl
                                 ├─ gerar QA → VERIFICADOR DE FIDELIDADE → corpus_qa.jsonl
                                 └─ encadear diálogos + 12 recusas → corpus_chat.jsonl
                                      └─ remover quase-duplicatas → estatísticas → Gradio
```

## 4. Decisões de projeto que não são óbvias

1. **A resposta do corpus de QA é sempre extraída do documento.** A moldura textual é
   nossa; o conteúdo, não. Fidelidade vira consequência da construção, não promessa.
2. **A melhor família de perguntas não tem molde.** A cartilha do Pronaf já é escrita em
   pergunta e resposta, com as dúvidas reais do agricultor, e nós extraímos esse diálogo.
   Ela roda sobre o documento inteiro, não trecho a trecho, porque a pergunta cai no fim de
   um trecho e a resposta no começo do seguinte.
3. **Canal de atendimento não é dado pessoal.** 0800 e números curtos de serviço (135, 136,
   158) são preservados; caixas de e-mail de serviço (`contato@`, `ouvidoria@`) também.
   Telefone fixo institucional é ambíguo e, na dúvida, mascaramos.
4. **O portão de qualidade roda por bloco, não por documento**, e tem quatro medidas, uma
   por tipo de defeito: letra dobrada, palavra picada, texto intercalado e palavra cortada
   ao meio. A última exige vocabulário, então a extração roda em duas passadas.
5. **Nos PDFs rodamos os dois extratores e escolhemos pelo resultado medido.**
6. **Nome de pessoa é separado de nome de programa por dois critérios do próprio corpus:**
   sobrenome quase nunca aparece em minúscula, e nome de pessoa não se repete três vezes
   num documento (nome de programa sim).
7. **Stop words e stemming não são usados no corpus** (o enunciado alerta contra), mas
   **são** usados dentro do verificador de fidelidade, que compara duas frases. São coisas
   diferentes.

## 5. Parâmetros que alguém pode querer mexer

| Onde | Variável | Valor | Efeito |
|---|---|---|---|
| célula 025 | `TOKENS_MIN`, `TOKENS_MAX` | 256, 512 | tamanho dos trechos |
| célula 025 | `SLM_ALVO` | `Qwen/Qwen2.5-0.5B-Instruct` | tokenizer usado para contar |
| célula 042 | `LIMITE_DOBRA` / `LIMITE_FRAGMENTO` / `LIMITE_MAIUSCULA` / `LIMITE_TRUNCADA` | 0.06 / 0.15 / 0.20 / 0.12 | severidade do portão |
| célula 078 | `LIMIAR_COMUM`, `MAX_REPETICOES_DE_NOME` | 0.5, 3 | agressividade do filtro de nomes |
| célula 080 | `NUMEROS_PUBLICOS`, `CAIXAS_DE_SERVICO` | listas | o que é canal e o que é dado pessoal |
| célula 125 | `minimo` de `verificar_fidelidade` | 0.80 | cobertura exigida da resposta |
| célula 130 | `USAR_LLM`, `N_TRECHOS_LLM`, `MODELO_QA` | True, 12, Qwen2.5-1.5B-Instruct | experimento de geração por LLM |
| célula 140 | `LIMITE_POR_PERGUNTA` | 4 | respostas distintas por pergunta |
| célula 160 | `LIMIAR_JACCARD` | 0.80 | corte de quase-duplicata |

## 6. Uso de IA no desenvolvimento

- **Dentro do produto:** `Qwen2.5-1.5B-Instruct` (Apache 2.0), apenas na seção 7.4, como
  experimento. O prompt está na variável `PROMPT_QA`. Todo par gerado passa pelo
  verificador de fidelidade antes de entrar no corpus, e uma amostra de 25% é impressa para
  revisão manual.
- **Durante o desenvolvimento:** assistente de IA usado para revisar código, discutir
  alternativas de implementação e redigir trechos de texto. As fontes, os limiares, as
  decisões de arquitetura e os exemplos de recusa foram definidos pelo grupo e conferidos
  contra a saída real do notebook.
- **O que não foi feito com IA:** nenhum número deste relatório foi estimado. Todos saem de
  células executadas.

## 7. Limitações conhecidas

- **Dois registros no mesmo corpus.** A cartilha do Pronaf fala com a agricultora; o manual
  do Garantia-Safra fala com o gestor municipal, sobre auditoria e cruzamento de bases. O
  modelo pode responder à persona em linguagem de auditoria.
- Viés federal: falta material das Emateres estaduais, que tratam de cultura e região
  específicas.
- O portão barra a página inteira em vez de reconstruí-la, então conteúdo legítimo vai
  junto.
- O verificador de fidelidade reprova paráfrase correta, por comparar palavras em comum.
- O boletim do INMET é um retrato do dia da coleta; a data está em `fontes/FONTES.json`.
- Telefone fixo institucional é mascarado por não haver como distingui-lo de um residencial.

## 8. Como retomar

```bash
pip install pypdf pdfplumber python-docx beautifulsoup4 lxml transformers torch spacy gradio
python -m spacy download pt_core_news_sm
python baixar_fontes.py     # repõe a pasta fontes/ a partir das URLs oficiais
```

Depois é só abrir `GS_Fabrica_Corpus_CitizenTech.ipynb` e executar as células na ordem. O
notebook é autossuficiente: baixa o que falta, gera os três `.jsonl` em `corpus/` e sobe a
interface Gradio no fim.

Os números de célula citados na tabela da seção 5 seguem a ordem em que elas aparecem no
notebook.

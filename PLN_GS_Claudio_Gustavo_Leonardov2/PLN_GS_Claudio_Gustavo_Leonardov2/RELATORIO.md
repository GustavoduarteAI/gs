# Fábrica de Corpus CitizenTech

*Um corpus de agricultura familiar para treinar um assistente que funciona sem internet.*

Global Solution de Processamento de Linguagem Natural, Chatbots e Virtual Agents

Prof. Dr. Sérgio Eduardo Palmiere, FIAP, turma 2TIAPR

Claudio Alves de Carvalho Junior (568565), Gustavo Duarte (567066) e Leonardo Pereira dos Santos (567836)

---

## 1. O problema, a persona e o ODS

O governo mantém várias políticas para a agricultura familiar: CAF, Pronaf,
Garantia-Safra, assistência técnica. As regras existem e estão publicadas. O problema é a
distância entre o documento e quem precisa dele.

Um detalhe definiu a escolha de arquitetura: no campo a internet é ruim o ano inteiro, não
só num dia de crise. Um assistente que depende de nuvem falha com frequência justamente
onde seria mais útil. Um SLM de poucos bilhões de parâmetros cabe num celular ou
no computador do sindicato e continua respondendo offline. Para isso, precisa ter sido
treinado antes com o conteúdo certo, e é esse conteúdo que esta GS produz.

**Persona.** Dona Alzira, 54 anos, três hectares, planta feijão e milho, duas das cinco
culturas cobertas pelo Garantia-Safra. Estudou até a quinta série. O técnico da Emater passa
a cada dois meses e o sinal de celular só pega perto da estrada. As perguntas dela são
sempre as mesmas três: eu me encaixo? (o CAF está ativo, a renda passou do limite, a
aposentadoria do marido entra na conta), perdi a lavoura na estiagem, eu tinha direito a
alguma coisa? e em que porta eu bato?.

**ODS.** Os mesmos apresentados no vídeo: **ODS 2** (fome zero e agricultura sustentável),
principal, pelas metas 2.3 (renda dos pequenos produtores, inclusive com acesso a serviços
financeiros, que é quase uma descrição do projeto, já que o gargalo é o acesso e não a falta
de política) e 2.4 (resiliência a eventos climáticos extremos, que é o que o Garantia-Safra
cobre); **ODS 10** (redução das desigualdades), porque quem mais perde por não entender a
regra é quem tem menos escolaridade e menos sinal de celular; **ODS 16** (instituições
eficazes e acesso público à informação, meta 16.10), porque o projeto torna legível o que
o governo já publica; e a **meta 1.4** (acesso a recursos econômicos e serviços financeiros)
como apoio.

## 2. Fontes

Em vez de converter tudo para um formato só, procuramos documentos que já existem em cada
formato pedido. Todos são públicos e de órgãos oficiais.

| Formato | Documento | Órgão |
|---|---|---|
| PDF | Como acessar Crédito Rural pelo Pronaf: passo a passo | MDA |
| PDF | Orientações do Programa Garantia-Safra | Ministério da Agricultura |
| DOCX | Modelo de contrato de prestação de serviços de ATER | MDA |
| HTML | Lei 10.420/2002, que criou o Fundo Garantia-Safra | Planalto |
| TXT | Avisos meteorológicos oficiais | INMET |
| colado | Recado sobre a adesão ao Garantia-Safra | escrito por nós, para testar o canal |

São cinco documentos, dentro da faixa de 3 a 5 que o enunciado pede, mais o canal de texto
colado, que ele cobra à parte. Os PDFs somam 56 páginas (44 da cartilha do Pronaf e 12 do
manual do Garantia-Safra), acima das 20 exigidas. O texto colado é um recado escrito por nós
no formato dos avisos de WhatsApp sobre a adesão ao Garantia-Safra; não é de nenhum
sindicato, e o campo `fonte` (`recado_garantia_safra.txt`) mostra isso. Depois da
extração e do portão de qualidade sobraram 21.031 palavras aprovadas.

Duas escolhas que vale explicar. A cartilha do Pronaf é distribuída pelo link que a própria
notícia do MDA publica, e o rodapé da página informa que a reprodução é gratuita desde que
citada a fonte; descartamos várias cartilhas boas da Embrapa justamente por trazerem
"todos os direitos reservados", e por isso nenhum documento da Embrapa entrou no corpus. E o boletim do INMET entra porque o gatilho do
Garantia-Safra é climático: o benefício existe para quem perde lavoura por seca ou por
excesso de chuva.

## 3. Decisões de extração e limpeza

### 3.1 O portão de qualidade (passo além do enunciado)

Na primeira rodada vimos que nem todo PDF oficial tem camada de texto utilizável, e que os
extratores erram de formas diferentes no mesmo arquivo. Encontramos cinco defeitos nestes
cinco documentos:

- glifos sobrepostos, que saem como letras dobradas (*"Conntingência"*);
- colunas embaralhadas, que picam as palavras em pedaços de uma ou duas letras;
- caixas de texto intercaladas, em que os pedaços se misturam sem nenhuma palavra ficar
  quebrada;
- palavra cortada ao meio (*"Os re veícu conhe como conta"*), em que cada pedaço tem
  tamanho de palavra normal e começa em minúscula;
- e, na ficha catalográfica da cartilha do Pronaf, fonte quebrada, que extrai como
  `&ŝĐŚĂĐĂƚĂůŽŐƌĄĨŝĐĂĞůĂďŽƌĂĚĂ`.

Criamos um portão que mede quatro coisas por bloco e barra o que passa do limite: letras
dobradas implausíveis (6%), palavras de uma ou duas letras fora da lista de curtas válidas
(15%), maiúscula no meio da frase (20%) e palavra que é só o começo de outra palavra do
corpus (12%). A última precisa saber quais palavras existem de verdade, então a extração
roda em duas passadas: montamos um vocabulário com as palavras que aparecem pelo menos três
vezes (1.655 palavras confirmadas) e depois avaliamos bloco a bloco. *"Veícu"* nunca
chega a três ocorrências, mas é o começo de *"veículos"*, que chega.

Ao todo 17 blocos foram para a quarentena, cada um com o motivo registrado. Rodamos os
dois extratores em cada PDF e ficamos com o que entrega mais texto aprovado.

### 3.2 Limpeza

Além do conjunto usual (cabeçalho e rodapé detectados por frequência, numeração de página,
URLs soltas, linhas repetidas), dois casos deram trabalho.

O primeiro é o hífen. A regra óbvia (`palavra-\nresto`) pega só parte: o `pypdf` junta as
linhas com espaço e sobra *"imediata - mente"*. Juntar todo `X - y` apagaria travessão
legítimo, então usamos o próprio corpus como juiz: só juntamos quando nenhum dos dois
pedaços aparece sozinho no texto e a palavra inteira aparece.

O segundo é específico da cartilha do Pronaf, exportada do InDesign: cada página carrega a
marca do arquivo e a data da exportação, sempre duas vezes coladas
(`ARQUIVO-EDITAVEL-PRONAF.indd 9ARQUIVO-EDITAVEL-PRONAF.indd 9`), e o mesmo acontece com os
títulos. Tratamos como três regras: colapsar a duplicação, remover a marca, remover a data.

Também removemos as anotações de vigência da lei (`(Incluído pela Lei nº ...)`), que são
legítimas para quem estuda a norma mas viram ruído para quem só quer saber se tem direito.

Não removemos stop words nem aplicamos stemming, como o enunciado alerta, e mantivemos
acentos, pontuação e maiúsculas, conferidos na célula.

## 4. LGPD e anonimização

### 4.1 O risco específico deste tema

Um anonimizador comum mascara qualquer coisa parecida com telefone ou e-mail. Só que aqui o
que o cidadão mais precisa achar é exatamente um telefone e um e-mail: o 0800 do
Disque-Intoxicação, o 135 do INSS, a caixa de contato da Anater por onde se descobre a
Emater do estado. Mascarar isso deixa o modelo com a forma da resposta e sem o conteúdo.

Separamos em três níveis:

| Nível | Exemplo | O que fazemos |
|---|---|---|
| inequivocamente público | `0800 722 6001`, `135`, `158` | preserva |
| inequivocamente pessoal | celular de plantão de um servidor | mascara |
| ambíguo | fixo institucional, `(61) 3521-5801` | mascara, e dizemos por quê |

O ambíguo mascaramos de propósito: pelo formato não dá para distinguir de um telefone
residencial, e na dúvida a LGPD pesa mais que a conveniência. Com o e-mail dá para fazer
melhor, porque a caixa de serviço se identifica no nome: `contato@` e `ouvidoria@` apontam
para um órgão, `joao.silva@` aponta para uma pessoa.

### 4.2 O que detectamos, e o erro que o corpus revelou

CPF e CNPJ com conferência do dígito verificador, e-mail, telefone, CEP e nome de pessoa.
Nos documentos oficiais o detector mascarou 1 telefone e preservou 1 e-mail de caixa de
serviço. Nome de pessoa real não apareceu nos trechos do corpus: as marcas `[NOME]` eram
todas falsos positivos (abaixo). O exemplo antes/depois está na seção 4 do notebook, com
texto real.

Nome foi o mais difícil, e o erro apareceu no nosso próprio corpus: o `pt_core_news_sm`
marcou "PRONAF MULHER" como pessoa e trocou a linha de crédito inteira por `[NOME]`.
Em vez de escrever uma lista de exceções à mão, usamos dois critérios tirados do corpus:
um sobrenome quase nunca aparece em minúscula, e nome de pessoa não se repete (numa
cartilha o nome de alguém sai uma ou duas vezes; "Pronaf Mulher" e "Garantia-Safra" saem o
tempo todo). Acima de três ocorrências, tratamos como nome de programa.

**O que ainda escapava.** Conferindo a saída marca por marca contra os documentos
originais, achamos 25 `[NOME]` no corpus de texto, e nenhum era nome de pessoa: 14 na
cartilha (nomes de linha em caixa alta, como "PRONAF BIOECONOMIA" e "PRONAF GRUPO B", e até o
verbo "LEVAR" em "3º PASSO: LEVAR O PROJETO PRO BANCO"), 10 títulos de cláusula ou parágrafo
do contrato de ATER ("CLÁUSULA DÉCIMA - DO FORO") e "Custódia Selic" na lei. É efeito
colateral da correção para nomes em caixa alta (seção 4.3). Não vazava dado pessoal, mas
apagava o nome da linha de crédito. O pós-processamento devolve o texto original nos 25
casos, por uma tabela conferida contra a fonte (`correcoes_corpus.py`). A correção de raiz,
uma lista de nomes de programa no anonimizador, exigiria reexecutar o pipeline e fica como
próximo passo.

### 4.3 O teste que mudou o anonimizador

Rodar sem erro não prova nada: um anonimizador que não encontra nada entrega o mesmo
relatório de um que funciona. Então plantamos 300 dados pessoais falsos em frases reais do
corpus, de propósito em formas de escrita que as nossas regex não previam.

| Tipo | Recall 1ª versão | Recall após correção |
|---|---|---|
| CPF | 60% | 100% |
| e-mail | 72% | 100% |
| telefone | 100% | 100% |
| CEP | 30% | 100% |
| nome | 95% | 100% |
| geral | 71,3% | 100% |

O que escapava: CPF separado por espaço, e-mail com espaço em volta do `@`, CEP sem hífen e
nome em CAIXA ALTA, que o NER em português não reconhece e que é o formato das assinaturas.
A correção para a caixa alta aproveita que passar para Capitalizado não muda o tamanho da
string: rodamos o NER numa cópia e usamos os mesmos índices no original.

Um cuidado na leitura: os 100% foram medidos no mesmo conjunto de 300 dados plantados que
usamos para corrigir as regex, então mostram que as falhas encontradas foram corrigidas, e
não o recall em texto novo. Um conjunto separado, com outras formas de escrita, daria a
medida honesta.

Falsos positivos: 1 em 123 frases sem dado plantado, e era a página de assinaturas da Lei
10.420. São nomes reais, ou seja, o anonimizador acertou e a amostra é que não estava limpa.
Ou seja, só dá para chamar de falso positivo depois de olhar o caso.

## 5. Os corpus e suas estatísticas

### 5.1 Segmentação, tamanhos e duplicatas

Segmentação em 256 a 512 tokens, contados com o tokenizer do modelo alvo
(`Qwen2.5-0.5B-Instruct`) e não por palavras: neste corpus a razão medida é 2,03 tokens
por palavra, então contar palavra colocaria boa parte dos trechos fora da faixa. Foram
gerados 143 trechos, 99% dentro da faixa pedida. Na versão apresentada, 139 dos 141 trechos
finais ficavam entre 256 e 512 tokens; os 2 de fora eram fim de documento. Mas o
pós-processamento feito depois do vídeo tirou os carimbos de data, os marcadores de página e o
cabeçalho repetido, que também contavam como tokens, e **48 trechos ficaram abaixo de 256**
(mínimo de 59), 44 deles da cartilha. Juntar trechos vizinhos mudaria a contagem; a correção
certa é segmentar depois dessa limpeza, o que exige reexecutar o pipeline.

| Arquivo | Exemplos | Mínimo | Tokens (média) | Faixa | Duplicatas exatas | Quase-duplicatas | Fontes |
|---|---|---|---|---|---|---|---|
| `corpus_texto.jsonl` | 141 | 50 | 267,0 | 121–374 | 2 | 0 | 6 |
| `corpus_qa.jsonl` | 116 | 100 | 101,8 | 30–296 | 11 | 1 | 6 |
| `corpus_chat.jsonl` | 67 | 30 | 331,5 | 236–630 | 0 | 0 | 6 |

A tabela é a da versão apresentada. Depois do pós-processamento, recalculado com o mesmo
tokenizer em `estatisticas.json`: texto 256,2 tokens em média (59–371), QA 95,4 (30–285) e
chat 311,4 (227–607).

Além da duplicata exata, removemos quase-duplicatas por Jaccard sobre shingles de 5
palavras com corte em 80%, usando índice invertido para não comparar todos contra todos. E
limitamos a 4 o número de respostas diferentes para a mesma pergunta.

### 5.2 As oito famílias de pergunta

As famílias renderam de forma bem desigual, e isso diz algo sobre as fontes:

| Família | Pares | Família | Pares |
|---|---|---|---|
| assunto do trecho | 76 | aviso meteorológico | 4 |
| pergunta do documento | 21 | tópico do manual | 3 |
| regra da lei | 10 | requisito | 1 |
| orientação prática | 1 | gerado por LLM (aprovado) | 1 |

**A família de perguntas que não tem molde.** Começamos escrevendo templates, como nas
outras etapas. Aí lemos a cartilha do Pronaf com atenção e vimos que ela já é escrita em
pergunta e resposta, com as dúvidas reais de quem está do outro lado do balcão:
*"Aposentadoria também entra como renda da família?"*, *"Renda de arrendamento também
conta?"*. Essas perguntas são melhores que as nossas, então a família principal do corpus de QA
passou a extrair o diálogo que já está no documento. Duas dificuldades
vieram junto: a pergunta cai no fim de um trecho e a resposta no começo do seguinte (por
isso essa família roda no documento inteiro), e o cabeçalho corrente da cartilha também é
uma pergunta e aparece 31 vezes (por isso descartamos qualquer pergunta que se repita
três vezes ou mais, em vez de escrever o título na mão).

### 5.3 Fidelidade e limites do assistente

**Fidelidade.** A resposta é sempre extraída do documento; o que escrevemos é só a moldura.
Mesmo assim, todo par passa por um verificador automático que confere se todo número da
resposta existe no trecho de origem e se pelo menos 80% das palavras de conteúdo vêm de lá.
A cobertura média ficou em 100%, com 139 de 139 pares aprovados.

**Diálogos de limite.** São 12, e o mínimo é 10, cobrindo indicação de agrotóxico,
intoxicação em curso, comparação de banco, declarar renda menor para conseguir o CAF,
diagnóstico de lavoura por descrição, previsão do tempo, valor do benefício, cálculo de
aposentadoria, desvio de finalidade do crédito, dado de terceiro, briga de divisa de terra e
pergunta fora do tema. Cada um redireciona para o canal certo (0800 722 6001, 192, 135,
Emater, sindicato, Defensoria Pública, Incra, agente financeiro, INMET e ZARC). Esses textos
foram escritos pelo grupo e o campo `fonte` diz isso.

## 6. Uso de IA

O corpus principal é gerado por regras sobre a estrutura dos documentos. A seção 7.4 do
notebook é um experimento à parte: geramos pares com o Qwen2.5-1.5B-Instruct (licença
Apache 2.0) e passamos todos pelo mesmo verificador de fidelidade. O prompt usado está
na variável `PROMPT_QA` e reproduzido abaixo:

> Você recebe um trecho de um documento oficial brasileiro sobre as políticas públicas da
> agricultura familiar (CAF, Pronaf, Garantia-Safra e assistência técnica). Escreva 2
> perguntas que uma agricultora familiar faria sobre este trecho, e a resposta de cada uma.
> Regras: a resposta só pode usar informação que está no trecho, não acrescente nada;
> escreva em português simples, como quem explica para alguém que não é técnico; se o trecho
> não responde nada útil para uma agricultora, devolva apenas NADA.

O resultado: de **24 pares gerados a partir de 12 trechos, só 1 passou** (4%). A cobertura
média das respostas do modelo ficou em 39,3%, contra 100% das respostas extraídas por
regra. O caso mais ilustrativo, com 57% de cobertura:

> P: Qual é a importância do CAF para os agricultores familiares?
> R: O CAF é essencial porque garante acesso às outras políticas públicas para
> agricultura familiar, como o Pronaf e a Garantia-Safra. Ele também permite que os
> agricultores tenham **crédito rural gratuito**.

As duas primeiras frases estão certas. A terceira está errada: o crédito do Pronaf é
subsidiado, não gratuito, e a própria cartilha diz que *"o dinheiro do financiamento do
Pronaf deve ser pago em dia, dentro dos prazos combinados, porque ele é emprestado"*. Um
modelo treinado com essa resposta ensinaria alguém a pegar uma dívida achando que era
doação.

A verificação automática cobre 100% dos pares gerados. Como ela não substitui leitura,
lemos a amostra de 25% (6 de 24 pares, acima dos 20% exigidos) que a célula seguinte imprime,
comparando cada resposta com o trecho de origem:

| # | Pergunta gerada | Verificador | Nossa leitura |
|---|---|---|---|
| 1 | Como solicitar o crédito pelo Pronaf? | reprovado (40%) | Errado: responde com requisitos do CAF e diz que aposentadoria rural conta como renda, o contrário da cartilha |
| 2 | Como obter o crédito rural pelo Pronaf? | reprovado (38%) | Requisitos do CAF fiéis, mas não respondem à pergunta; reprovaríamos pela pergunta, não pela paráfrase |
| 3 | Como obter crédito pelo Pronaf? | reprovado (42%) | Distorce: "comparar preços do que vai comprar" vira "comprovar os preços das suas mercadorias" |
| 4 | O que é a Garantia-Safra? | reprovado (9%) | Errado: não é seguro para garantir vendas |
| 5 | Diferença entre o Pronaf e outros créditos? | reprovado (40%) | Errado: R$ 20.000 está no trecho, mas é o limite de custeio do milho, não um limite geral do Pronaf |
| 6 | Como funciona o Fundo Garantia-Safra? | reprovado (23%) | Compatível com o art. 1º da lei; o verificador reprovou por paráfrase. Aprovaríamos com revisão |

Concordamos com a reprovação em 5 dos 6 casos (no 2, por outro motivo: a pergunta, não a
paráfrase). No 6 discordamos: a resposta é fiel e foi reprovada só por ser paráfrase. O caso 5 explica por que a saída mostra "reprovados
por número que não existe no trecho: 0": o número existe no trecho, e o erro está no uso dele.
O verificador confere números e palavras, não o sentido.

Também usamos assistente de IA durante o desenvolvimento, para revisar código e discutir
alternativas. As fontes, os limiares, as decisões de arquitetura e os textos de recusa são do
grupo, e todo número deste relatório foi conferido contra a saída executada.

## 7. Evidência: linhas reais dos três arquivos

O vídeo não mostrou o conteúdo dos `.jsonl`, então registramos aqui linhas reais de cada
arquivo, com o número da linha. Para caber na página, os textos longos foram cortados em
`(...)`; as linhas completas estão em `corpus/`.

**`corpus_texto.jsonl`**

```json
// linha 39
{"text": "(...) ciárias do crédito fundiário e para indígenas e quilombolas PRONAF GRUPO B: famílias que têm renda anual de até R$50 mil. As famílias do Grupo A vivem em terras indígenas, em quilombos ou não têm terra para trabalh (...)", "fonte": "cartilha_pronaf_credito_rural.pdf"}
```

**`corpus_qa.jsonl`**

```json
// linha 5
{"instruction": "Aposentadoria também entra como renda da família?", "input": "", "output": "Sim. Só que, se for aposentadoria rural ou benefícios sociais, não vai entrar na conta. Se for aposentadoria de emprego na cidade, vai entrar como não rural. Tem que informar todas as rendas.", "fonte": "cartilha_pronaf_credito_rural.pdf"}
// linha 34
{"instruction": "Quem pode emitir o CAF?", "input": "", "output": "A cartilha do Pronaf, do MDA, explica: Só pode emitir CAF quem trabalha na terra e atende aos requisitos.", "fonte": "cartilha_pronaf_credito_rural.pdf"}
// linha 105
{"instruction": "Quando é feita a adesão ao Garantia-Safra?", "input": "", "output": "A Lei 10.420/2002, do Garantia-Safra, diz: A adesão dos agricultores familiares ao Fundo Garantia-Safra obedecerá as disposições do regulamento, observadas as seguintes condições: I – a adesão antecederá ao início do pla (...)", "fonte": "lei_10420_2002_garantia_safra.html"}
```

**`corpus_chat.jsonl`**

```json
// linha 34
{"messages": [{"role": "system", "content": "Você é um assistente de orientação para a agricult (...)"}, {"role": "user", "content": "Quais são os requisitos para a minha família tirar o CAF?"}, {"role": "assistant", "content": "A cartilha cita três requisitos principais. Primeiro, morar na propriedade ou perto o bastante para trabalhar nela todo dia. Segundo, a área não pode passar de 4 módulos fiscais; o tamanho do módulo muda de município par (...)"}, {"role": "user", "content": "Vendo na feira e não tenho nota. Como eu comprovo a renda?"}, {"role": "assistant", "content": "Para quem vende em feira, sem nota fiscal, vale a autodeclaração, e as notas declaratórias também servem para comprovar renda. Existe um modelo de autodeclaração nas regras do Pronaf: é só pedir na Emater."}], "fonte": "cartilha_pronaf_credito_rural.pdf"}
// linha 56
{"messages": [{"role": "system", "content": "Você é um assistente de orientação para a agricult (...)"}, {"role": "user", "content": "Que veneno eu passo na lavoura de feijão que está dando mancha?"}, {"role": "assistant", "content": "Essa eu não respondo, e não é para te deixar na mão: indicar agrotóxico sem ver a lavoura é perigoso para você e para quem vai comer o alimento. No Brasil a compra e o uso dependem de receituário agronômico, que só um en (...)"}, {"role": "user", "content": "E se eu usar o mesmo que o vizinho usou?"}, {"role": "assistant", "content": "Não faça isso. O produto do vizinho pode ser para outra cultura, outra praga e outra dosagem, e usar errado dá resíduo no alimento, resistência da praga e multa. Espere o técnico olhar a sua lavoura."}], "fonte": "redacao do grupo (limites do assistente)"}
```

**Resíduos e ajustes depois do vídeo.** A cartilha do Pronaf, exportada do InDesign, deixou
três resíduos que a limpeza não pegou: o carimbo de data e hora (`21/10/2024 13:37:36`), o
marcador de página (`[ 09 ]`) e o cabeçalho corrente "Como acessar Crédito Rural pelo Pronaf?".
O pós-processamento (`pos_processar_corpus.py`) remove esses resíduos e o cabeçalho duplicado
do Planalto, acentua o texto escrito pelo grupo, devolve o texto dos 25 falsos `[NOME]`, troca
5 perguntas de QA que eram frases afirmativas (a resposta extraída continua a mesma) e corrige
os diálogos: 15 diálogos documentais foram reescritos à mão em tom de atendente, sempre com a
informação do trecho de origem, e em outros 40 a continuação genérica ("Pode explicar de um
jeito mais simples?") virou a pergunta que o trecho seguinte de fato responde. No QA, as 102
perguntas de molde ("O que eu preciso saber sobre caf?"), retóricas ou contaminadas pelo texto
anterior foram reescritas à mão para a pergunta que a resposta responde: são agora 116
perguntas distintas, e as respostas continuam extraídas do documento, com moldura mais curta. O pipeline não
foi reexecutado: as contagens 141 / 116 / 67 e as fronteiras dos trechos são as do vídeo, e
os arquivos originais estão em `versao_apresentada/`.

## 8. Ligação com as outras disciplinas

As três entregas da Global Solution tratam do mesmo problema e do mesmo público. Este corpus é
a base do modelo local; o **Fala, Lavoura!** (IA generativa) é o assistente que conversa
com o agricultor e hoje usa o Gemini na nuvem, com busca, cálculos e guardrails que já
funcionam sem internet; o **Mutirão** (RPA) organiza a fila do técnico. Não há contradição
entre "modelo local" aqui e "nuvem" lá: a nuvem resolveu o protótipo, e o SLM treinado com
estes corpus é o caminho para o modo offline do mesmo assistente, na parte de políticas
públicas (CAF, Pronaf, Garantia-Safra e ATER).

## 9. Dificuldades encontradas

**O gargalo não foi o algoritmo, foi o PDF.** Entramos achando que a parte difícil seria
gerar os pares; foi extrair. Cinco tipos de defeito diferentes nos mesmos cinco documentos,
e nenhum visível se você olha só o começo do arquivo. O portão de qualidade foi a mudança que
mais melhorou o corpus final, e não estava no enunciado.

**Ler o documento rendeu mais do que inventar molde.** Nossa melhor família de perguntas não
tem template: ela extrai o diálogo que a cartilha já traz. Foi preciso ler o material em vez
de só processá-lo.

**Teste que sempre passa não é teste.** O anonimizador acertava 71,3% quando testado de
verdade. E o verificador de fidelidade, enquanto rodava só sobre respostas extraídas,
aprovava tudo e não provava nada; foi preciso dar a ele o texto de um LLM para ver se tinha
dentes.

**O governo escreve para dois leitores diferentes.** A cartilha do Pronaf fala com a
agricultora, em segunda pessoa e com exemplo do dia a dia. O manual do Garantia-Safra fala
com o gestor municipal, sobre indícios de desconformidade e cruzamento de bases da Receita
Federal. Os dois são oficiais e tratam do mesmo programa. Isso entra no corpus e o modelo
aprende os dois registros, o que é bom para cobertura e ruim para tom: ele pode responder à
Dona Alzira em linguagem de auditoria. Anotamos como limitação, e a correção seria marcar
cada trecho com o seu registro e usar isso como peso no fine-tuning.

**Gênero de documento muda quais regras funcionam.** As famílias de orientação prática e de
item de procedimento, que renderiam bem em material de emergência, quase não disparam aqui:
uma cartilha de crédito explica, não manda. Verbo no imperativo é raro nestes documentos.

**A dúvida mais importante é a que as fontes menos respondem.** Escrevemos uma
família para a terceira dúvida da Dona Alzira, "em que porta eu bato?", pegando as frases
que citam sindicato, Emater, banco ou entidade emissora. Ela rendeu 3 pares úteis em 20
frases candidatas: os documentos citam esses nomes bastante, mas quase nunca no formato
"procure X para fazer Y". Achamos melhor tirar a família do que deixar rendendo três pares.
Fica o registro do que faltaria nestas fontes para o assistente resolver a vida de quem
pergunta.

**A rede de segurança ficou grande demais.** A família genérica, que só entra quando o
trecho não rende nada pelas outras, respondeu por cerca de dois terços do corpus de
perguntas e respostas. Isso vem do que está escrito acima: estes documentos são prosa
corrida, com poucos dos padrões (inciso definidor, lista imperativa, campo de formulário)
que as famílias específicas procuram. Registramos a proporção porque ela mostra onde o
próximo esforço renderia mais, que é em fontes com mais estrutura e não em mais regras. As
perguntas dessa família eram moldes ("Onde entra renda no acesso às políticas...?") e foram
reescritas à mão depois do vídeo (seção 7).

**Viés federal.** As fontes são do MDA, do Ministério da Agricultura, do Planalto e do
INMET. Falta material das Emateres estaduais, que tratam de cultura e região específicas.
Fica registrado como limitação, não escondido.

**A lei entrou com as redações revogadas.** O HTML do Planalto é o "texto compilado": ele
mantém, tachado, o texto antigo de cada artigo ao lado do novo, e a extração pegou os dois. Por
isso o corpus traz versões que se contradizem: o benefício aparece como R$ 600 em até 6
parcelas, R$ 700, R$ 1.200 e "definido pelo órgão gestor, em até 3 parcelas" (a redação de
2025); o fundo aparece como "Seguro-Safra", nome antigo, ao lado de "Garantia-Safra"; e o
gestor ainda aparece como "Ministério do Desenvolvimento Agrário". Um modelo treinado assim
responderia valores diferentes para a mesma pergunta. Nos corpus de QA e de chat, trocamos as
respostas com redação revogada ou lixo de extração (5 pares de QA e os diálogos 39 e 45) pela
redação vigente do mesmo artigo; o "Ministério do Desenvolvimento Agrário" do diálogo 42 é do
art. 11, que não foi alterado. O corpus de texto puro ainda tem as redações antigas. A correção certa está na extração: descartar o texto tachado (`<strike>` e
`<s>`) e, entre as redações que sobram para o mesmo dispositivo, ficar só com a mais recente.
Isso exige reexecutar o pipeline e é o próximo passo de maior impacto na fidelidade. Pelo
mesmo motivo, o recado escrito pelo grupo cita a perda mínima de 50%, regra anterior à
redação de 2025.

**Diálogos documentais ainda são encadeamento de trechos.** Fora os 12 diálogos de limite e
os 15 reescritos à mão, os diálogos documentais juntam dois trechos do documento: a pergunta
agora combina com a resposta, mas a resposta é o texto da cartilha, e não a fala de um
atendente. Só 27 dos 67 diálogos soam como atendimento de verdade. É o ponto mais fraco do
corpus conversacional, e reescrever os demais é o próximo passo de maior ganho.

**Resumo das limitações.** Redações revogadas da lei no corpus (acima); diálogos documentais encadeados; recall do anonimizador
medido no próprio conjunto de ajuste (4.3); falsos `[NOME]` corrigidos por tabela, e não no
anonimizador (4.2); 48 trechos abaixo de 256 tokens depois da limpeza (5.1); dois registros de linguagem no mesmo corpus; e viés federal das fontes.

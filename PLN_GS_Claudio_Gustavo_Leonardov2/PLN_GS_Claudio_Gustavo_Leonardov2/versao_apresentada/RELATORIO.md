# Fábrica de Corpus CitizenTech

*Um corpus de agricultura familiar para treinar um assistente que funciona sem internet.*

Global Solution de Processamento de Linguagem Natural, Chatbots e Virtual Agents

Prof. Dr. Sérgio Eduardo Palmiere, FIAP, turma 2TIAPR

Claudio Alves (568565), Gustavo Duarte (567066) e Leonardo Pereira (567836)

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

**ODS.** Meta 2.3 (dobrar a renda dos pequenos produtores, inclusive por meio de acesso
seguro e igual a serviços financeiros) como objetivo principal, que é quase uma descrição do
projeto, já que o gargalo aqui é acesso e não existência da política; metas 2.4
(resiliência a eventos climáticos extremos, que é o que o Garantia-Safra endereça) e 1.4
(acesso a serviços financeiros) como apoio.

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
colado, que ele cobra à parte. Os PDFs somam 56 páginas, acima das 20 exigidas. Depois da
extração e do portão de qualidade sobraram 21.031 palavras aprovadas.

Duas escolhas que vale explicar. A cartilha do Pronaf é distribuída pelo link que a própria
notícia do MDA publica, e o rodapé da página informa que a reprodução é gratuita desde que
citada a fonte; descartamos várias cartilhas boas da Embrapa justamente por trazerem
"todos os direitos reservados". E o boletim do INMET entra porque o gatilho do
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
Nos documentos oficiais o detector encontrou 26 nomes e 1 telefone reais, e preservou
1 e-mail de caixa de serviço. O exemplo antes/depois está na seção 4 do notebook, com
texto real.

Nome foi o mais difícil, e o erro apareceu no nosso próprio corpus: o `pt_core_news_sm`
marcou "PRONAF MULHER" como pessoa e trocou a linha de crédito inteira por `[NOME]`.
Em vez de escrever uma lista de exceções à mão, usamos dois critérios tirados do corpus:
um sobrenome quase nunca aparece em minúscula, e nome de pessoa não se repete (numa
cartilha o nome de alguém sai uma ou duas vezes; "Pronaf Mulher" e "Garantia-Safra" saem o
tempo todo). Acima de três ocorrências, tratamos como nome de programa.

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

Falsos positivos: 1 em 123 frases sem dado plantado, e era a página de assinaturas da Lei
10.420. São nomes reais, ou seja, o anonimizador acertou e a amostra é que não estava limpa.
Ou seja, só dá para chamar de falso positivo depois de olhar o caso.

## 5. Os corpus e suas estatísticas

### 5.1 Segmentação, tamanhos e duplicatas

Segmentação em 256 a 512 tokens, contados com o tokenizer do modelo alvo
(`Qwen2.5-0.5B-Instruct`) e não por palavras: neste corpus a razão medida é 2,03 tokens
por palavra, então contar palavra colocaria boa parte dos trechos fora da faixa. Foram
gerados 143 trechos, 99% dentro da faixa pedida.

| Arquivo | Exemplos | Mínimo | Tokens (média) | Faixa | Duplicatas exatas | Quase-duplicatas | Fontes |
|---|---|---|---|---|---|---|---|
| `corpus_texto.jsonl` | 141 | 50 | 267,0 | 121–374 | 2 | 0 | 6 |
| `corpus_qa.jsonl` | 116 | 100 | 101,8 | 30–296 | 11 | 1 | 6 |
| `corpus_chat.jsonl` | 67 | 30 | 331,5 | 236–630 | 0 | 0 | 6 |

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

A verificação automática cobre 100% dos pares gerados, e os reprovados aparecem com o
motivo na saída da célula. Como ela não substitui leitura, a célula seguinte imprime uma
amostra de 25% desses pares (acima dos 20% exigidos) com o veredito do verificador ao lado
de cada um.

Também usamos assistente de IA durante o desenvolvimento, para revisar código e discutir
alternativas. As fontes, os limiares, as decisões de arquitetura e os textos de recusa são do
grupo, e todo número deste relatório foi conferido contra a saída executada.

## 7. Dificuldades encontradas

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
próximo esforço renderia mais, que é em fontes com mais estrutura e não em mais regras.

**Viés federal.** As fontes são do MDA, do Ministério da Agricultura, do Planalto e do
INMET. Falta material das Emateres estaduais, que tratam de cultura e região específicas.
Fica registrado como limitação, não escondido.

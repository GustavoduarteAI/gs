"""Correções de conteúdo aplicadas por pos_processar_corpus.py (revisão de 19/11/2026).

Tudo aqui foi conferido à mão contra os documentos de origem. Nenhuma correção muda a
quantidade de exemplos nem a fronteira dos trechos do corpus de texto.

1. NOMES_FALSOS      25 [NOME] que não eram nome de pessoa voltam ao texto original.
2. PERGUNTAS_QA      5 pares de QA com pergunta afirmativa ganham a pergunta certa.
3. DIALOGOS_ATENDENTE 15 diálogos documentais reescritos em tom de atendente, fiéis à fonte.
4. CONTINUACOES      continuações genéricas trocadas pela pergunta que o trecho responde.
"""
import re

# --------------------------------------------------------------------------- 1
# (texto antes, texto depois, o que está escrito na fonte)
NOMES_FALSOS = [
    # cartilha do Pronaf (14): nomes de linha em caixa alta e o verbo do 3º passo
    ("3º PASSO: ", " O PROJETO PRO BANCO", "LEVAR"),
    ("indígenas e quilombolas ", ": famílias que têm renda", "PRONAF GRUPO B"),
    ("justificado no projeto técnico ", " Inclui custos", "PRONAF AGROECOLOGIA"),
    ("orgânicos de produção ", " Esta linha serve para ex", "PRONAF BIOECONOMIA"),
    ("(A, A/C e B) ", " Suinocultura", "Pronaf Agroecologia"),
    ("R$250 mil (demais) ", " Silvicultura", "Pronaf Bioeconomia"),
    ("PRAZO CARÊNCIA ", " Orientado R$55", "Pronaf Produtivo"),
    ("para o bem-estar. ", " Esta é uma linha de inve", "PRONAF PRODUTIVO ORIENTADO"),
    ("pelo PNMPO. ", " TAXA DE JUROS", "PRONAF JOVEM LIMITES"),
    ("destes sócios. ", " O que pode ser financiad", "PRONAF AGROINDÚSTRIA"),
    ("", " É o financiamento da integrali", "PRONAF COTAS-PARTES"),
    # modelo de contrato de ATER (10): títulos de cláusula e de parágrafo
    ("", " - DAS OBRIGAÇÕES", "CLÁUSULA SEGUNDA"),
    ("", " - A CONTRATADA deve se responsabilizar", "PARÁGRAFO QUARTO"),
    ("", " - DA REMUNERAÇÃO", "CLÁUSULA QUARTA"),
    ("", " - A aprovação da prestação", "PARÁGRAFO QUARTO"),
    ("", " - A CONTRATADA será responsável", "PARÁGRAFO SEXTO"),
    ("", " - DA SUPERVISÃO E DA AVALIAÇÃO", "CLÁUSULA SEXTA"),
    ("", " - DAS SANÇÕES", "CLÁUSULA SÉTIMA"),
    ("", " - DA RESCISÃO", "CLÁUSULA OITAVA"),
    ("", " - DA SUBCONTRATAÇÃO", "CLÁUSULA NONA"),
    ("", " - DO FORO", "CLÁUSULA DÉCIMA"),
    # Lei 10.420 (1): nome do sistema do Banco Central
    ("Liquidação e ", ".", "Custódia Selic"),
]


def restaurar_nomes(t: str) -> str:
    for antes, depois, original in NOMES_FALSOS:
        t = re.sub(re.escape(antes + "[NOME]") + "(?=" + re.escape(depois) + ")", lambda _m: antes + original, t)
    return t


RE_PLANALTO = re.compile(r"(Presidência da República Casa Civil Subchefia para Assuntos Jurídicos )\1")

# --------------------------------------------------------------------------- 2
# (início da pergunta antiga, início da resposta, pergunta nova); a resposta não muda
PERGUNTAS_QA = [
    ("Depois, tem que renovar.", "01. Moram na propriedade", "Quais são os requisitos para a família fazer o CAF?"),
    ("São gestoras da família", "Vocês, famílias que têm as características",
     "Quem pode fazer o CAF além das famílias agricultoras?"),
    ("Nos outros casos, devem pedir desvinculação", "Na lei, fala de território",
     "O que a lei diz sobre o território da entidade cadastradora?"),
    ("Não esqueçam de guardar todas as notas ficais!", "SEGUNDO, V AI OLHAR O PROJETO",
     "O que o banco olha no projeto técnico?"),
    ("Não esqueçam de guardar todas as notas ficais!", "boa relação com os bancos",
     "Por que é importante manter uma boa relação com o banco?"),
]

# --------------------------------------------------------------------------- 3
# Chave: início da 1ª resposta do diálogo original (sem a moldura). Valor: as quatro
# falas novas (usuário, atendente, usuário, atendente). Cada informação vem da fonte
# indicada no campo "fonte" do diálogo; nada foi acrescentado além de encaminhamentos.
DIALOGOS_ATENDENTE = {
    "Se possível, desligue aparelhos": [
        "Saiu um aviso do INMET para a minha região. O que eu faço?",
        "Nos avisos de vento forte, o INMET orienta a não se abrigar debaixo de árvores, por causa do risco "
        "de queda e de descargas elétricas, e a não estacionar perto de torres de transmissão e de placas. "
        "Se possível, desligue os aparelhos elétricos e o quadro geral de energia.",
        "E onde eu consigo mais informação?",
        "Com a Defesa Civil, pelo telefone 199, e com o Corpo de Bombeiros, pelo 193.",
    ],
    "SEGUNDO, V AI OLHAR O PROJETO": [
        "Vou pedir crédito pelo Pronaf. O que o banco olha no meu projeto?",
        "O banco olha se o projeto técnico mostra direitinho como o dinheiro vai ser usado: o que você quer "
        "comprar e para quê. Por isso o projeto precisa ser bem-feito. A cartilha do Pronaf também recomenda "
        "guardar todas as notas fiscais.",
        "Eu arrendo um pedaço da minha terra para o vizinho. Essa renda conta como renda da roça?",
        "Não conta como renda da produção. Para a cartilha, o arrendamento é como um aluguel, e não faz "
        "diferença se o pagamento é em dinheiro ou em produto. E só pode emitir o CAF quem trabalha na terra "
        "e atende aos requisitos.",
    ],
    "Na lei, fala de território da cadastradora": [
        "Minha filha quer pegar crédito também. Ela pode usar o CAF da nossa família?",
        "Depende. Pela cartilha do Pronaf, quem está na faixa de idade do Pronaf Jovem pode pedir pelo CAF da "
        "família, e quem atende aos requisitos do Pronaf Mulher também. Nos outros casos, ela precisa se "
        "desvincular da unidade familiar e tirar um CAF próprio.",
        "E a aposentadoria do meu marido entra na renda da família?",
        "Se for aposentadoria rural ou benefício social, não entra na conta. Se for aposentadoria de emprego "
        "na cidade, entra como renda não rural. Em todo caso, é preciso informar todas as rendas da família.",
    ],
    "Para quem não sabe, Emater significa Empresa de Assistência Técnica e Extensão Rural. São instituições públicas criadas para ajudar famílias agricultoras com assistência técnica, organização da produção e muito mais. O serviço é de graça": [
        "O que é a Emater? Vale a pena fazer o CAF com ela?",
        "Emater é a Empresa de Assistência Técnica e Extensão Rural, uma instituição pública que ajuda as "
        "famílias agricultoras com assistência técnica e organização da produção. O serviço é de graça. "
        "Fazer o CAF com ela é útil porque o técnico visita a propriedade e conhece o tamanho, os cultivos e "
        "a família, e isso ajuda depois a montar um bom projeto para o banco.",
        "Qualquer sindicato ou associação também pode fazer o meu CAF?",
        "Não são todos. Só as associações e os sindicatos que pediram e foram autorizados pelo Governo "
        "Federal. Vale perguntar antes se a entidade é cadastradora.",
    ],
    "Seria onde o CNPJ da cadastradora atua": [
        "Moro numa cidade e a terra fica na cidade vizinha. Onde eu peço o CAF?",
        "No município da terra em que você trabalha. A cartilha explica que cada entidade cadastradora atende "
        "dentro dos limites dos municípios. Você pode morar em outro município, desde que seja perto o "
        "bastante para ir trabalhar todos os dias.",
        "E antes de pedir o crédito, eu preciso planejar alguma coisa?",
        "Sim. A cartilha aconselha fazer as contas em três cenários, um pessimista, um realista e um "
        "otimista, para estar preparada para qualquer coisa. A entidade pública de Ater ajuda nesse "
        "planejamento da produção, do mercado e das finanças, e a assistência técnica é gratuita.",
    ],
    "Tem que analisar o contrato.": [
        "Eu dou o adubo e outra pessoa trabalha e cuida da lavoura. Isso é parceria?",
        "Tem que olhar o contrato. A cartilha avisa que pode ser, por exemplo, um arrendamento pago em "
        "produto, e aí seria um arrendamento disfarçado de parceria. Leve o contrato à Emater ou à entidade "
        "que emite o seu CAF para conferir.",
        "Preciso do CAR para fazer o CAF?",
        "Não é obrigatório. O Cadastro Ambiental Rural serve para comprovar a área, mas não é exigido.",
    ],
    "Sim. O CAF pode ser impresso": [
        "Tenho uma chácara numa área considerada urbana. Posso tirar o CAF?",
        "Pode, desde que a família atenda aos requisitos. A cartilha explica que o que conta é o tipo de "
        "trabalho feito no imóvel. Para comprovar a área, valem os documentos de área urbana: o IPTU, se houver "
        "construção, ou o ITR.",
        "Tenho que pagar alguma associação para fazer o CAF?",
        "Não. É proibido exigir pagamento de associação ou de qualquer outro tipo.",
    ],
    "01. Moram na propriedade": [
        "Quais são os requisitos para a minha família tirar o CAF?",
        "A cartilha cita três requisitos principais. Primeiro, morar na propriedade ou perto o bastante para "
        "trabalhar nela todo dia. Segundo, a área não pode passar de 4 módulos fiscais; o tamanho do módulo "
        "muda de município para município, e quem faz essa conta é o Incra. Terceiro, mais da metade da mão "
        "de obra tem que ser da própria família.",
        "Vendo na feira e não tenho nota. Como eu comprovo a renda?",
        "Para quem vende em feira, sem nota fiscal, vale a autodeclaração, e as notas declaratórias também "
        "servem para comprovar renda. Existe um modelo de autodeclaração nas regras do Pronaf: é só pedir na "
        "Emater.",
    ],
    "Vocês, famílias que têm as características": [
        "Só agricultor pode fazer o CAF?",
        "Não. Além das famílias agricultoras, a cartilha cita povos indígenas, comunidades quilombolas, povos "
        "e comunidades tradicionais, empreendimentos familiares rurais, associações e cooperativas, desde que "
        "tenham as características exigidas.",
        "E quem vende para cooperativa, como comprova a renda?",
        "Quem tem renda de cooperativa ou entrega produtos para o mercado precisa levar documentos que "
        "comprovem essa renda. A autodeclaração vale para quem vende de forma informal, como na feira.",
    ],
    "Sim, pode fazer o CAF. Se a família for meeira": [
        "Sou meeira, não sou dona da terra. Posso fazer o CAF?",
        "Pode. Se a família é meeira, precisa levar um documento que comprove a meação. Se for arrendatária, "
        "um documento que comprove o arrendamento.",
        "Meu filho trabalha na cidade. Ele ainda conta como mão de obra da família?",
        "Pode contar, porque a pessoa pode trabalhar tanto na cidade quanto no campo. A cartilha faz uma "
        "ressalva para quem tem contrato de 40 horas por semana na cidade; nesse caso, confirme com a "
        "entidade que emite o seu CAF.",
    ],
    "É importante entender que o dinheiro do financiamento do Pronaf deve ser pago em dia": [
        "O dinheiro do Pronaf precisa ser devolvido?",
        "Precisa, sim. O crédito do Pronaf é um empréstimo, não é dinheiro a fundo perdido, e tem que ser "
        "pago em dia, nos prazos combinados. Por isso a cartilha recomenda ter o apoio de um técnico "
        "habilitado para fazer um bom projeto de crédito.",
        "Então por que pegar pelo Pronaf e não direto no banco?",
        "Porque os juros do Pronaf são bem menores: o governo subsidia essas taxas. Pedindo emprestado direto "
        "ao banco, fora do Pronaf, você pagaria os juros comuns de mercado.",
    ],
    "MULHER? Uma coisa legal do Pronaf Mulher": [
        "Quem pode pedir o Pronaf Mulher?",
        "No Pronaf Mulher, todas as mulheres da família podem emitir o CAF-Pronaf e, com isso, fazer os seus "
        "próprios projetos de crédito. A cartilha também diz que essa linha não restringe o que pode ser "
        "financiado: serve para todos os investimentos do Pronaf.",
        "E onde eu tiro o CAF-Pronaf?",
        "Na mesma entidade que emitiu o seu CAF. De forma geral, as unidades familiares com renda bruta anual "
        "de até R$ 500 mil podem obter o CAF-Pronaf.",
    ],
    "Para ter acesso ao Benefício Garantia-Safra, os agricultores": [
        "Para receber o Garantia-Safra eu preciso fazer algum curso?",
        "Sim. A Lei 10.420/2002 diz que, a partir da adesão, o agricultor familiar é obrigado a participar de "
        "programas de educação e capacitação rural para ter acesso ao benefício.",
        "E quando eu tenho que me inscrever?",
        "Antes de começar o plantio. No documento de adesão vai a área que será plantada com as culturas "
        "cobertas, como feijão, milho, arroz, mandioca ou algodão.",
    ],
    "O Poder Executivo Federal regulamentará": [
        "Quanto vale o benefício do Garantia-Safra e como ele é pago?",
        "A lei não fixa um valor: ele é definido pelo órgão gestor e pago em até 3 parcelas mensais por "
        "família. Quando há emergência ou calamidade pública decretada em nível nacional, o pagamento é feito "
        "em parcela única.",
        "Ele é pago em qualquer município?",
        "Não. Pela redação atual da lei, ele só é pago às famílias que moram em municípios onde foi "
        "verificada perda de safra, conforme as regras do programa. Para saber da sua inscrição, procure o "
        "sindicato ou a secretaria de agricultura do município.",
    ],
    "Apesar de não terem sido bloqueados": [
        "Quem pode participar do Garantia-Safra?",
        "Pelo manual do Garantia-Safra, os critérios são: ter renda bruta familiar mensal de até um salário "
        "mínimo e meio; plantar culturas como arroz, feijão, mandioca, milho ou algodão; e plantar entre 0,6 "
        "e 5 hectares.",
        "E para quem o programa foi criado?",
        "Para agricultores e agricultoras familiares de municípios que perdem a safra com frequência por seca "
        "ou excesso de chuva, na área de atuação da Sudene. O objetivo é garantir condições mínimas de "
        "sobrevivência quando a safra se perde.",
    ],
}

# --------------------------------------------------------------------------- 4
CONTINUACOES_GENERICAS = {
    "Pode explicar de um jeito mais simples?", "E o que eu faço com essa informação?",
    "E na prática, como isso funciona?", "Isso vale para todo mundo ou tem exceção?",
    "E o que eu faço na lavoura quando sai um aviso desses?",
}
# (início do trecho que responde, pergunta nova)
CONTINUACOES = [
    ("Para quem não sabe, Emater significa", "E o que é a Emater?"),
    ("Só pode emitir CAF quem trabalha na terra", "E quem pode tirar o CAF?"),
    ("GRUPO A/C É uma linha", "E o que é a linha do Grupo A/C?"),
    ("Pelo menos metade da renda", "Quanto da renda precisa vir da roça?"),
    ("É só ir até uma instituição cadastradora", "E onde eu peço o CAF?"),
    ("Não são todas as associações e sindicatos", "Qualquer associação ou sindicato pode fazer o cadastro?"),
    ("O crédito do Pronaf tem juros bem menores", "Por que os juros do Pronaf são mais baixos?"),
    ("Ela tem a vantagem também de não restringir", "E o Pronaf Mulher, tem alguma vantagem?"),
    ("Se todas as integrantes da família estarão cadastradas", "Todas as pessoas da família entram no mesmo CAF?"),
    ("Vamos falar do Pronaf, que estimula", "E para que serve o Pronaf?"),
    ("Vocês precisam levar alguns documentos", "Que documentos eu preciso levar?"),
    ("Cultivo de milho, cujas operações", "E quais atividades entram nesse limite?"),
    ("A emissão do CAF-Pronaf é feita", "E quem emite o CAF-Pronaf?"),
    ("Se for área do município", "E se a terra for do município, quem faz?"),
    ("GRUPO A E GRUPO B", "E as linhas do Grupo A e do Grupo B, servem para quê?"),
    ("O crédito de investimento serve", "E o crédito de investimento, serve para quê?"),
    ("Esse recurso pode ser aplicado pela cooperativa", "E a cooperativa pode usar esse dinheiro em quê?"),
    ("São esses profissionais que vão fornecer", "E quem dá a orientação técnica para as famílias?"),
    ("O crédito de industrialização serve", "E o crédito de industrialização, serve para quê?"),
    ("O crédito de custeio serve", "E o crédito de custeio, serve para quê?"),
    ("É importante que vocês façam a inscrição no CAF", "Preciso mesmo me inscrever no CAF?"),
    ("Se for área da União", "E se a terra for da União ou do município, quem faz?"),
    ("Todos os itens financiáveis no Pronaf Mais Alimentos", "E o Pronaf Jovem financia as mesmas coisas que o Mais Alimentos?"),
    ("Esse sistema substitui a DAP", "O CAF substituiu a DAP?"),
    ("Município, conforme acordado entre o Estado", "E quanto o Estado contribui para o fundo?"),
    ("II – do instrumento de adesão", "O que vai no documento de adesão?"),
    ("E extrato ou declaração do INSS", "E que documento do INSS pode ser pedido?"),
    ("Safra 2015/2016: Se a inscrição", "Qual é o período de verificação de cada safra?"),
    ("Safra 2017/2018: Se a inscrição", "E na safra 2017/2018, qual é o período de verificação?"),
    ("O Garantia-Safra, criado pela Lei 10.420", "Para que serve o Garantia-Safra?"),
    ("TERCEIRA - DO PRAZO DE VIGÊNCIA", "Quanto tempo dura o contrato de ATER?"),
    ("Para a liberação da quinta parcela", "E para liberar a quinta parcela, o que precisa?"),
    ("Para a liberação da primeira parcela", "Pode repetir só os documentos da primeira parcela?"),
    ("PRIMEIRO - O pagamento será efetuado", "Como é feito o pagamento da assistência técnica?"),
    ("PRIMEIRA - DO OBJETO", "Qual é o objetivo desse contrato?"),
    ("Obtenha mais informações junto à Defesa Civil", "E onde eu consigo mais informações?"),
    ("Até 30 de agosto de cada ano", "E quando estados e municípios ficam sabendo quanto vão contribuir?"),
    ("Os agricultores familiares, a partir de sua adesão", "E depois de aderir, o agricultor tem alguma obrigação?"),
    ("O saldo apurado em cada exercício", "E o dinheiro que sobra no fundo num ano, o que acontece com ele?"),
]


# --------------------------------------------------------------------------- 5
# Redações revogadas da Lei 10.420. O HTML do Planalto é o "texto compilado": guarda o texto
# antigo (tachado) ao lado do novo, e a extração pegou os dois. Nas respostas de QA e de chat que
# eram redação revogada (com o nome antigo "Seguro-Safra" ou valores antigos) ou lixo de
# extração, o trecho é trocado pela redação vigente do mesmo dispositivo, conferida no HTML sem
# o texto tachado. O corpus de texto puro continua como foi extraído: ver a limitação no relatório.
# (início do trecho antigo, trecho vigente)
SUBSTITUICOES_LEI = [
    ("Os benefícios do Seguro-Safra serão efetivados",
     "O Benefício Garantia-Safra somente poderá ser pago aos agricultores familiares residentes em Municípios "
     "nos quais tenha sido verificada perda de safra nos termos do art. 8º desta Lei."),
    ("Texto compilado Regulamento",
     "Cria o Fundo Garantia-Safra e institui o Benefício Garantia-Safra, destinado a agricultores familiares "
     "vitimados pelo fenômeno da estiagem, nas regiões que especifica."),
    ("O saldo apurado em cada exercício financeiro será transferido para o exercício seguinte, a crédito do "
     "Fundo Seguro-Safra",
     "O saldo apurado em cada exercício financeiro será transferido para o exercício seguinte, a crédito do "
     "Fundo Garantia-Safra."),
    ("Município, conforme acordado entre o Estado e o Município; III",
     "III - a contribuição anual do Estado, a ser adicionada às contribuições do agricultor e do Município, "
     "deverá ser em montante suficiente para complementar a contribuição de 10% (dez por cento) em 2012, "
     "12,50% (doze inteiros e cinquenta centésimos por cento) no ano de 2013, 15% (quinze por cento) na safra "
     "2014/2015, 17,50% (dezessete inteiros e cinquenta centésimos por cento) no ano de 2015 e de 20% (vinte "
     "por cento) a partir de 2016, do valor da previsão dos benefícios anuais, para o Estado."),
    ("A inscrição dos agricultores familiares no Seguro-Safra",
     "A adesão dos agricultores familiares ao Fundo Garantia-Safra obedecerá as disposições do regulamento, "
     "observadas as seguintes condições: I – a adesão antecederá ao início do plantio; II - do instrumento de "
     "adesão constará a área a ser plantada com as culturas previstas no caput do art. 8º, e outras previstas "
     "pelo órgão gestor."),
]

# --------------------------------------------------------------------------- 6
# Perguntas de molde do QA ("O que eu preciso saber sobre caf?", "Onde entra renda no acesso
# às políticas...?"), perguntas retóricas e perguntas contaminadas pelo texto anterior:
# cada uma foi reescrita à mão para a pergunta que a resposta extraída de fato responde.
# A resposta não muda (fora as redações vigentes da seção 5).
# (linha do corpus_qa.jsonl, início da resposta como trava, pergunta nova)
PERGUNTAS_POR_LINHA = [
    (1, "É importante entender que o di", "O dinheiro do Pronaf precisa ser devolvido?"),
    (4, "Pode. Só precisa ser perto o s", "Se a gente mora em um município e trabalha em outro, pode fazer o CAF?"),
    (7, "Tem que analisar o contrato. P", "Se eu dou o adubo e outra pessoa trabalha e cuida, isso é parceria?"),
    (8, "Sim, pode fazer o CAF. Se a fa", "Sou meeira ou arrendatária. Posso fazer o CAF?"),
    (9, "Pode trabalhar fora e contar c", "Quem trabalha fora conta como mão de obra da família?"),
    (10, "Para quem não sabe, Emater sig", "O que são as entidades públicas de Ater, como a Emater?"),
    (11, "Não. É proibida a exigência de", "O sindicato pode cobrar taxa ou exigir que eu seja sócia para fazer o CAF?"),
    (14, "As que se enquadram na faixa e", "Quem tem mais de 16 anos pode pedir crédito pelo CAF da família?"),
    (19, "Assim vão poder imaginar quant", "Como planejar quanto vamos ganhar com a venda?"),
    (22, "Vamos falar do Pronaf, que est", "Para que serve o Pronaf?"),
    (23, "Assim, daria para aumentar a p", "Dá para aumentar a produção e preservar o meio ambiente ao mesmo tempo?"),
    (24, "São esses profissionais que vã", "Quem dá orientação técnica e educação financeira para quem pede o Pronaf?"),
    (25, "O crédito do Pronaf tem juros ", "Por que os juros do Pronaf são mais baixos que os do banco?"),
    (26, "O crédito do Pronaf tem juros ", "O crédito do Pronaf tem juros menores que os do banco?"),
    (27, "RURAL? Nesse guia, vamos mostr", "Como acessar o crédito rural pelo Pronaf?"),
    (28, "No Pronaf, existem muitas linh", "Para que servem as linhas de crédito do Pronaf?"),
    (29, "O CAF, como diz a lei, identif", "O que é o CAF?"),
    (30, "Esse sistema substitui a DAP (", "O CAF substituiu a DAP?"),
    (31, "É importante que vocês façam a", "Preciso me inscrever no CAF?"),
    (32, "Pelo menos metade da renda, no", "Quanto da renda da família precisa vir da roça?"),
    (33, "Se vocês são proprietárias e a", "Arrendar um pedaço da terra conta como renda da produção?"),
    (34, "Só pode emitir CAF quem trabal", "Quem pode emitir o CAF?"),
    (35, "Poderia acontecer, por exemplo", "Arrendamento pago em produto pode ser considerado parceria?"),
    (36, "Vocês precisam levar alguns do", "Que documentos eu preciso levar para fazer o CAF?"),
    (37, "É só ir até uma instituição ca", "Onde eu peço o CAF?"),
    (38, "Se for área da União, a Secret", "Se a terra for da União ou do município, quem faz o documento?"),
    (39, "É só ir até uma instituição ca", "Posso fazer o CAF na Emater, no sindicato ou na prefeitura?"),
    (40, "Se for área da União, a Secret", "Se a terra for da União, quem faz o documento?"),
    (41, "Vocês precisam levar alguns do", "Para fazer o CAF, levo documentos de quê?"),
    (42, "Vocês podem fazer uma autodecl", "Posso fazer autodeclaração de uso da terra ou de renda?"),
    (43, "Se for área do município, é a ", "Se a terra for do município, quem faz o documento?"),
    (44, "Não são todas as associações e", "Qualquer associação ou sindicato pode fazer o CAF?"),
    (45, "Para quem não sabe, Emater sig", "O que significa Emater e onde acho a Ater do meu estado?"),
    (46, "Para quem não sabe, Emater sig", "O que é a Emater?"),
    (47, "Se todas as integrantes da fam", "Todas as pessoas da família entram no mesmo CAF?"),
    (48, "Como provar uma renda da ativi", "Nota declaratória serve para comprovar renda?"),
    (49, "As que se enquadram na faixa e", "Jovens e mulheres da família podem pedir crédito pelo CAF da família?"),
    (50, "As que se enquadram na faixa e", "Quem está na idade do Pronaf Jovem pode usar o CAF da família?"),
    (51, "O CAF serve também para a agri", "O CAF pode ser impresso?"),
    (52, "Só falta saber se estão enquad", "O que é o CAF-Pronaf?"),
    (53, "A emissão do CAF-Pronaf é feit", "Quem emite o CAF-Pronaf e qual é o limite de renda?"),
    (54, "Logo adiante, vamos ver os tip", "Quais são os tipos de crédito rural do Pronaf?"),
    (55, "É com esses gastos na ponta do", "Por que fazer as contas antes de pedir o financiamento?"),
    (56, "Como a gente falou lá atrás, t", "Dá para financiar muita coisa pelo Pronaf?"),
    (57, "O crédito de custeio serve par", "Para que serve o crédito de custeio?"),
    (58, "O crédito de industrialização ", "Para que serve o crédito de industrialização?"),
    (59, "O crédito de investimento serv", "Para que serve o crédito de investimento?"),
    (60, "O crédito de industrialização ", "O crédito de industrialização ajuda a montar uma agroindústria?"),
    (61, "MULHER? Uma coisa legal do Pro", "Quem pode pedir o Pronaf Mulher?"),
    (62, "Ela tem a vantagem também de n", "Quais são as vantagens do Pronaf Mulher?"),
    (63, "A partir daqui, vamos mostrar ", "O Pronaf Mulher tem condições especiais de juros?"),
    (64, "Relembrando: PRONAF GRUPO A: c", "Quem pode pedir crédito nos grupos A e A/C do Pronaf?"),
    (65, "Para isso vão solicitar crédit", "Quem não é do Grupo A pede crédito em qual grupo do Pronaf?"),
    (66, "GRUPO A E GRUPO B As linhas de", "Para que servem as linhas dos grupos A e B?"),
    (67, "No caso de financiamento para ", "Quais são as condições do financiamento dos grupos A e B?"),
    (68, "GRUPO A/C É uma linha com as m", "Quais são as condições da linha Pronaf A/C?"),
    (69, "GRUPO A/C É uma linha com as m", "O que financia a linha do Grupo A/C?"),
    (70, "Dá para financiar coisas diret", "O que dá para financiar no crédito de investimento?"),
    (71, "Todos os itens financiáveis no", "O Pronaf Jovem financia os mesmos itens do Mais Alimentos?"),
    (72, "R$30 mil 3% ao ano 10 anos 3 a", "Para que serve o Pronaf Custeio?"),
    (73, "Cultivo de milho, cujas operaç", "Quais atividades entram no limite de custeio?"),
    (74, "PRONAF? Existem diferentes ban", "Quais bancos fazem crédito pelo Pronaf?"),
    (75, "Esse recurso pode ser aplicado", "Em que a cooperativa pode aplicar o recurso do Pronaf?"),
    (76, "O Garantia-Safra, criado pela ", "Para que serve o Garantia-Safra?"),
    (77, "O Garantia-Safra, criado pela ", "Quem o Garantia-Safra ajuda?"),
    (78, "BASES DE DADOS UTILIZADAS (Rel", "Que bases de dados o Garantia-Safra usou na verificação dos aderidos?"),
    (79, "E extrato ou declaração do INS", "Que documento do INSS o Garantia-Safra pode pedir?"),
    (80, "Safra 2017/2018: Se a inscriçã", "Qual é o período de verificação da safra 2017/2018?"),
    (81, "Apesar de não terem sido bloqu", "Para onde vão as defesas e recursos da safra 2011/2012 do Garantia-Safra?"),
    (82, "Renda bruta familiar mensal ao", "Qual é o limite de renda familiar do Garantia-Safra?"),
    (83, "Safra 2015/2016: Período de Ju", "Qual é o período da safra 2015/2016?"),
    (84, "Safra 2015/2016: Se a inscriçã", "Qual é o período de verificação de cada safra no Garantia-Safra?"),
    (85, "Safra 201 7/2018: comprovar qu", "Na safra 2017/2018, o que era preciso comprovar sobre a residência?"),
    (86, "Por meio deste Instrumento Par", "Quem são as partes do contrato de ATER?"),
    (87, "PRIMEIRA - DO OBJETO O present", "Qual é o objetivo do contrato de ATER?"),
    (88, "PRIMEIRO - A CONTRATADA deve e", "Como a empresa de ATER deve trabalhar com o beneficiário?"),
    (89, "TERCEIRA - DO PRAZO DE VIGÊNCI", "Quanto tempo dura o contrato de ATER?"),
    (90, "PRIMEIRO - O pagamento será ef", "Como é pago o serviço de ATER?"),
    (91, "Para a liberação da primeira p", "Que documentos são pedidos para liberar a primeira parcela?"),
    (92, "Para a liberação da primeira p", "O que precisa para liberar a primeira parcela do contrato de ATER?"),
    (93, "Para liberação de terceira par", "Que documentos são pedidos para liberar a terceira e a quarta parcelas?"),
    (94, "Para a liberação da quinta par", "Que documentos são pedidos para liberar a quinta parcela?"),
    (95, "SEGUNDO - A UTE/UGE poderá, ca", "O contrato de ATER pode ser rescindido se o beneficiário atrasar as parcelas?"),
    (96, "Os benefícios do Seguro-Safra ", "Em quais municípios o Benefício Garantia-Safra é pago?"),
    (97, "Texto compilado Regulamento Co", "O que a Lei 10.420 criou?"),
    (98, "O saldo apurado em cada exercí", "O que acontece com o dinheiro que sobra no Fundo Garantia-Safra no fim do ano?"),
    (99, "O saldo apurado em cada exercí", "O saldo do Fundo Garantia-Safra passa para o ano seguinte?"),
    (100, "Constituem despesas do Fundo G", "Quais são as despesas do Fundo Garantia-Safra?"),
    (101, "Município, conforme acordado e", "Quanto o Estado contribui para o Fundo Garantia-Safra?"),
    (102, "O valor do Benefício Garantia-", "Qual é o valor do Benefício Garantia-Safra e como ele é pago?"),
    (103, "Fundo Garantia-Safra poderá se", "A cobertura do Garantia-Safra pode valer para outras atividades agrícolas?"),
    (104, "Quando houver decretação nacio", "Quando o Garantia-Safra é pago em parcela única?"),
    (105, "A inscrição dos agricultores f", "Quando é feita a adesão ao Garantia-Safra?"),
    (106, "Os agricultores familiares, a ", "Quem adere ao Garantia-Safra precisa fazer algum curso?"),
    (107, "II – do instrumento de adesão ", "O que vai no documento de adesão ao Garantia-Safra?"),
    (108, "Para ter acesso ao Benefício G", "Para receber o Garantia-Safra, é preciso participar de capacitação?"),
    (109, "Até 30 de agosto de cada ano, ", "Quando estados e municípios ficam sabendo quanto vão contribuir?"),
    (110, "O Poder Executivo Federal regu", "Quem regulamenta a lei do Garantia-Safra?"),
    (111, "Em caso de rajadas de vento: (", "O que fazer quando o INMET avisa de rajadas de vento?"),
    (112, "Obtenha mais informações junto", "Onde conseguir mais informações sobre um aviso do INMET?"),
    (113, "Se possível, desligue aparelho", "O que fazer com a energia elétrica durante um aviso do INMET?"),
    (115, "Leve ao sindicato: documento c", "O que levar ao sindicato para aderir ao Garantia-Safra?"),
]

# Pares cuja resposta não respondia à pergunta (15 e 47) ou repetia, palavra por palavra, a
# resposta de outro par (41 = 36, 60 = 58, 98 = 99). A resposta nova é outro trecho, copiado do
# mesmo documento. Chave: (linha, resposta antiga sem moldura, pergunta nova, resposta nova).
CARTILHA = "A cartilha do Pronaf, do MDA, explica: "
LEI = "A Lei 10.420/2002, do Garantia-Safra, diz: "
PARES_REFEITOS = [
    (15, "Na lei, fala de território da cadastradora.",
     "Em qual município eu peço o CAF?",
     "Na lei, fala de território da cadastradora. Seria onde o CNPJ da cadastradora atua. As unidades "
     "estão dentro dos limites dos municípios. Vocês têm que pedir o CAF no município da terra em que "
     "vocês trabalham."),
    (41, "Vocês precisam levar alguns documentos, das pessoas, da terra e de renda.",
     "Que documentos da terra servem para fazer o CAF?",
     CARTILHA + "DOCUMENTOS DA TERRA: Pode ser somente um desses, não precisa de todos. • Escritura pública. "
     "• Certificado de Cadastro do Imóvel Rural (CCIR). • Cadastro Nacional de Imóveis Rurais (CNIR)."),
    (47, "Se todas as integrantes da família estarão cadastradas no CAF.",
     "Quais documentos pessoais eu levo para fazer o CAF?",
     CARTILHA + "• Cópia dos CPF e RG das pessoas da família maiores de 16 anos. • Cópia do comprovante de "
     "endereço residencial da família."),
    (60, "O crédito de industrialização serve para financiar atividades de beneficiamento da produção, "
         "incentivando a formação de pequenas agroindústrias e de cooperativas de produção.",
     "O que dá para financiar com o crédito de industrialização?",
     CARTILHA + "Alguns exemplos: formação de estoque de matéria-prima e de produto final; armazenagem; "
     "beneficiamentos como limpeza, pasteurização, refrigeração, descascamento e padronização dos produtos; "
     "compra de embalagens, rótulos, condimentos, conservantes; seguro e impostos para industrializar; "
     "entre outros."),
    (98, "O saldo apurado em cada exercício financeiro será transferido para o exercício seguinte, a crédito "
         "do Fundo Garantia-Safra.",
     "De onde vem o dinheiro do Fundo Garantia-Safra?",
     LEI + "Constituem recursos do Fundo Garantia-Safra: I - a contribuição individual do agricultor familiar; "
     "II - as contribuições anuais dos Estados e seus Municípios que aderirem ao Programa; III - os recursos "
     "da União direcionados para a finalidade; IV - o resultado das aplicações financeiras de seus recursos."),
]

# Molduras mais curtas e diretas para as respostas extraídas.
MOLDURAS = [
    ("Na cartilha do MDA sobre como acessar o crédito rural pelo Pronaf aparece o seguinte: ",
     "A cartilha do Pronaf, do MDA, explica: "),
    ("No manual de orientações do Garantia-Safra aparece o seguinte: ", "O manual do Garantia-Safra diz: "),
    ("Na Lei 10.420/2002, que criou o Garantia-Safra aparece o seguinte: ", "A Lei 10.420/2002, do Garantia-Safra, diz: "),
    ("Segundo a Lei 10.420/2002, que criou o Garantia-Safra: ", "A Lei 10.420/2002, do Garantia-Safra, diz: "),
    ("No modelo de contrato de ATER do MDA aparece o seguinte: ", "O modelo de contrato de ATER do MDA diz: "),
    ("Conforme o boletim de avisos do INMET: ", "O INMET orienta: "),
]
RE_MOLDE = re.compile(r"(O que eu preciso saber sobre|O que os documentos oficiais falam sobre|Onde entra .* no acesso)")
PERGUNTA_DO_TRECHO: dict = {}  # preenchido ao processar o corpus_qa.jsonl, que vem antes do chat
RE_RESTO_TITULO = re.compile(r"^(?:RURAL|PRONAF|MULHER)\? ")


def corpo(resposta: str) -> str:
    """Tira a moldura ("A cartilha ... explica: ") e devolve só o trecho."""
    return resposta.split(": ", 1)[1] if ": " in resposta[:150] else resposta


def ajustar_resposta(texto: str, fonte: str) -> str:
    """Moldura curta, sem resto de título no começo e com a redação vigente da lei."""
    for antiga, nova in MOLDURAS:
        if texto.startswith(antiga):
            texto = nova + texto[len(antiga):]
            break
    if ": " in texto[:60]:
        moldura, trecho = texto.split(": ", 1)
        moldura += ": "
    else:
        moldura, trecho = "", texto
    trecho = RE_RESTO_TITULO.sub("", trecho)
    if fonte.startswith("lei_10420"):
        for inicio, vigente in SUBSTITUICOES_LEI:
            if trecho.startswith(inicio):
                trecho = vigente
                break
    return moldura + trecho


def limpar(t: str) -> str:
    #  é o travessão do cp1252 que a página do Planalto trouxe sem converter (16 casos)
    return RE_PLANALTO.sub(r"", restaurar_nomes(t)).replace("", "–")


def corrigir(r: dict, contagem: dict, linha: int | None = None) -> dict:
    if "text" in r:
        r["text"] = limpar(r["text"])
    if "instruction" in r:
        r["instruction"] = limpar(r["instruction"])
        r["output"] = limpar(r["output"])
        for velha, resp, nova in PERGUNTAS_QA:
            if r["instruction"].startswith(velha) and r["output"].startswith(resp):
                r["instruction"] = nova
                contagem["qa"] += 1
                break
        for n, trava, nova in PERGUNTAS_POR_LINHA:
            if n == linha and corpo(r["output"]).startswith(trava) and r["instruction"] != nova:
                r["instruction"] = nova
                contagem["qa"] += 1
        r["output"] = ajustar_resposta(r["output"], r["fonte"])
        for n, antiga, pergunta, resposta in PARES_REFEITOS:
            if n == linha and corpo(r["output"]) == antiga:
                r["instruction"], r["output"] = pergunta, resposta
                contagem["qa"] += 1
        PERGUNTA_DO_TRECHO.setdefault(corpo(r["output"])[:80], r["instruction"])
    msgs = r.get("messages")
    if msgs:
        for m in msgs:
            m["content"] = limpar(m["content"])
        primeira = corpo(msgs[2]["content"]) if len(msgs) > 2 else ""
        for inicio, falas in DIALOGOS_ATENDENTE.items():
            if primeira.startswith(inicio):
                r["messages"] = [msgs[0]] + [{"role": papel, "content": c}
                                             for papel, c in zip(["user", "assistant"] * 2, falas)]
                contagem["reescritos"] += 1
                return r
        for k in range(2, len(msgs) - 1):
            if msgs[k]["role"] == "user" and msgs[k]["content"] in CONTINUACOES_GENERICAS:
                trecho = corpo(msgs[k + 1]["content"])
                for inicio, nova in CONTINUACOES:
                    if trecho.startswith(inicio):
                        msgs[k]["content"] = nova
                        contagem["continuacoes"] += 1
                        break
        if not r["fonte"].startswith("redacao"):
            for m in msgs:
                if m["role"] == "assistant":
                    m["content"] = ajustar_resposta(m["content"], r["fonte"])
            # 1ª pergunta de molde: usa a pergunta já reescrita no QA para o mesmo trecho
            if RE_MOLDE.match(msgs[1]["content"]):
                nova = PERGUNTA_DO_TRECHO.get(corpo(msgs[2]["content"])[:80])
                if nova:
                    msgs[1]["content"] = nova
                    contagem["continuacoes"] += 1
    return r

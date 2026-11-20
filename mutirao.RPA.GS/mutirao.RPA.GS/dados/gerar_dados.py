"""
Gera os dados SINTETICOS usados no projeto.

1) dados/treino/solicitacoes_treino.csv -> base rotulada para treinar o classificador
   (montada por templates, com variacoes, jeito falado e erros de digitacao de proposito).
2) entrada/ -> lotes de exemplo que o robo vai processar, cada canal num formato
   diferente:
     - fala_lavoura_fila_tecnico.jsonl  fila do tecnico exportada pelo Fala, Lavoura! (GenAI)
     - cooperativa_whatsapp.csv         mensagens da cooperativa (CSV UTF-8)
     - casa_agricultura_balcao.csv      balcao da Casa da Agricultura (CSV antigo, CP1252 e ';')
     - sindicato_rural_lote.xlsx        planilha do sindicato rural
     - formulario_site.json             formulario do site
     - exportacao_interrompida.json     exportacao cortada no meio (corrompida)

Nenhum dado aqui e real. Nomes, CPFs e telefones sao inventados.
O conjunto de TESTE (dados/teste/teste_rotulado.csv) NAO e gerado aqui: ele foi
escrito a mao, com outro vocabulario, justamente para a avaliacao ser mais honesta.

Uso: python dados/gerar_dados.py
"""
import json
import random
from pathlib import Path

import pandas as pd

SEMENTE = 42
RAIZ = Path(__file__).resolve().parent.parent
random.seed(SEMENTE)

# Centro aproximado de municipios paulistas com agricultura familiar (informacao publica)
MUNICIPIOS = {
    "Campinas": (-22.9056, -47.0608),
    "Piracicaba": (-22.7253, -47.6492),
    "Botucatu": (-22.8858, -48.4450),
    "Registro": (-24.4979, -47.8449),
    "Itapeva": (-23.9822, -48.8756),
    "Ibiúna": (-23.6564, -47.2225),
    "Mogi das Cruzes": (-23.5229, -46.1880),
    "Mirante do Paranapanema": (-22.2903, -51.9064),
    "Socorro": (-22.5914, -46.5289),
    "São Miguel Arcanjo": (-23.8781, -47.9972),
}

COMUNIDADES = ["Sítio São José", "Bairro Rural do Pinhal", "Assentamento Nova Esperança",
               "Comunidade do Ribeirão", "Sítio Água Limpa", "Chácara Santa Luzia",
               "Bairro dos Mendes", "Sítio Três Irmãos", "Bairro do Cerrado", "Sítio Boa Vista"]

# ===========================================================================
# 1) Base de treino por templates
# ===========================================================================
CULTURAS = ["milho", "feijao", "tomate", "mandioca", "alface", "couve", "abobora", "banana",
            "quiabo", "pimentao", "batata", "cafe"]
LUGARES = ["horta", "lavoura", "roca", "plantacao", "estufa", "canteiro", "terra"]
TEMPOS = ["uma semana", "15 dias", "um mes", "mais de 20 dias", "muito tempo"]

TEMPLATES = {
    "pragas": {
        "frases": [
            "{praga} {acao} {parte} do {cultura}",
            "apareceu {praga} na {lugar} de {cultura}",
            "como acabo com {praga} no {cultura}",
            "o {cultura} ta cheio de {praga}",
            "{praga} atacando a {lugar}, ta {acao} {parte}",
            "tem {praga} em tudo que e pe de {cultura}",
            "preciso de ajuda com {praga} na {lugar}",
            "o que passo contra {praga} no {cultura}",
            "quanto de veneno coloco na bomba costal pra {praga}",
            "qual remedio mata {praga} no {cultura}",
            "posso pulverizar o {cultura} contra {praga}",
            "{praga} voltou no {cultura} mesmo depois de passar remedio",
            "tem uns {bicho_desc} no {cultura}",
        ],
        "bicho_desc": ["bichinhos pretos", "bichinhos verdes", "bichinhos brancos", "besourinhos",
                       "inseto pequeno voando", "lagartinhas", "formigas"],
        "praga": ["lagarta", "pulgao", "mosca branca", "vaquinha", "formiga cortadeira", "broca",
                  "percevejo", "cigarrinha", "lagarta do cartucho", "trips", "acaro", "lesma",
                  "gafanhoto", "mandarova", "bicho", "inseto", "praga"],
        "acao": ["comendo", "furando", "raspando", "sugando", "cortando", "destruindo", "roendo"],
        "parte": ["as folhas", "o broto", "a espiga", "as vagens", "o cartucho", "os frutos", "o caule"],
    },
    "doencas": {
        "frases": [
            "{sintoma} nas folhas do {cultura}",
            "o {cultura} ta com {doenca}",
            "apareceu {sintoma} e as folhas tao {estado}",
            "acho que e {doenca} no {cultura}",
            "a {lugar} de {cultura} pegou {doenca}",
            "os frutos do {cultura} estao {estado_fruto}",
            "pe de {cultura} {estado} com {sintoma}",
            "como tratar {doenca} na {lugar}",
            "a folha do {cultura} ta cheia de {sintoma}",
            "depois da chuva o {cultura} pegou {sintoma}",
        ],
        "sintoma": ["mancha preta", "mancha marrom", "po branco", "mofo", "bolor cinza",
                    "manchas amarelas com bolinha", "lesao escura no caule", "pintas escuras",
                    "ferrugem", "folha enrolada e mosqueada", "po alaranjado", "pustulas",
                    "manchas com borda amarela", "podridao mole"],
        "doenca": ["requeima", "ferrugem", "oidio", "antracnose", "murcha bacteriana", "podridao",
                   "virose", "mancha angular", "mildio", "fusariose", "sigatoka", "doenca", "fungo"],
        "estado": ["secando", "murchando", "apodrecendo", "caindo", "enrugando", "morrendo"],
        "estado_fruto": ["apodrecendo no pe", "com manchas fundas", "rachando com mofo",
                         "cheios de pintas pretas", "caindo podres"],
    },
    "agua": {
        "frases": [
            "o {fonte} {estado_fonte} e a {lugar} ta {seca}",
            "quanto de agua devo colocar no {cultura}",
            "preciso de ajuda pra montar {irrigacao} na {lugar}",
            "a {irrigacao} {defeito}",
            "nao chove faz {tempo} e o {cultura} ta {seca}",
            "a {lugar} encharca toda vez que chove e o {cultura} sofre",
            "como economizar agua na {lugar}",
            "quero fazer {obra} pra guardar agua da chuva",
            "quantas vezes por dia rego o {cultura}",
            "o motor da bomba d'agua {defeito} e a {lugar} ficou sem agua",
            "o {cultura} ta murchando por falta de agua",
        ],
        "fonte": ["poco", "nascente", "cisterna", "represa", "acude", "caixa d'agua", "rio"],
        "estado_fonte": ["secou", "ta baixo", "ta quase seco", "ta com pouca agua"],
        "seca": ["seca", "sedenta", "torrando", "murcha de sede", "rachando de seca"],
        "irrigacao": ["irrigacao por gotejamento", "mangueira de gotejo", "aspersor", "bomba d'agua",
                      "sistema de irrigacao", "microaspersao"],
        "defeito": ["entupiu", "parou de funcionar", "nao tem pressao", "ta vazando", "queimou"],
        "obra": ["cisterna", "barraginha", "caixa seca", "reservatorio"],
    },
    "solo": {
        "frases": [
            "a terra {estado_terra}, o que faco",
            "como fazer {pratica} na {lugar}",
            "preciso de {servico}",
            "o {cultura} ta {sintoma_nutri}, acho que falta adubo",
            "quanto de {insumo} coloco no {cultura}",
            "a {lugar} ta com {erosao}",
            "quero fazer {pratica} antes de plantar {cultura}",
            "posso usar {insumo} na {lugar}",
        ],
        "estado_terra": ["ta fraca", "ta cansada", "ta azeda", "ta dura e compactada",
                         "e muito arenosa", "nao produz mais"],
        "pratica": ["analise de solo", "calagem", "adubacao verde", "compostagem", "curva de nivel",
                    "plantio direto", "adubacao organica"],
        "servico": ["coletar amostra de solo", "recomendacao de adubo", "ajuda pra entender a analise de solo",
                    "orientacao de calagem"],
        "sintoma_nutri": ["amarelando por igual", "fraco e baixinho", "com as folhas pequenas",
                          "crescendo devagar", "com a ponta da folha seca"],
        "insumo": ["calcario", "esterco", "cama de frango", "adubo", "npk", "composto", "gesso"],
        "erosao": ["erosao", "valeta aberta pela enxurrada", "vocoroca", "terra descendo o morro"],
    },
    "credito": {
        "frases": [
            "como faco pra pegar {programa}",
            "preciso {doc}",
            "quero vender pro {mercado}",
            "o {programa} {problema}",
            "perdi a safra e quero acionar o {seguro}",
            "o banco pediu {doc_curto} pro {programa}",
            "quando abre a {chamada}",
            "tenho direito ao {programa}",
            "perdi o {cultura} na {perda}, o {seguro} cobre",
            "tem ajuda do governo pra quem perdeu a safra na {perda}",
            "o prazo do {seguro} ta acabando",
        ],
        "perda": ["seca", "estiagem", "geada", "chuva de pedra", "enchente"],
        "programa": ["pronaf", "credito rural", "financiamento do banco", "pronaf mulher",
                     "pronaf jovem", "custeio", "investimento do pronaf"],
        "doc": ["tirar o caf", "renovar a dap", "fazer o cadastro da agricultura familiar",
                "fazer o car do sitio", "da declaracao de aptidao"],
        "doc_curto": ["o caf", "a dap", "o car", "o projeto tecnico"],
        "mercado": ["pnae da merenda escolar", "paa", "programa de compra do governo",
                    "feira da prefeitura"],
        "seguro": ["garantia safra", "proagro", "seguro rural"],
        "problema": ["foi negado", "ta demorando", "venceu a parcela", "nao saiu ainda"],
        "chamada": ["chamada publica da merenda", "inscricao do garantia safra", "chamada do paa"],
    },
    # Pedidos que chegam aos mesmos canais mas NAO sao de assistencia tecnica.
    # O modelo aprende a reconhece-los e o robo manda para um tecnico encaminhar.
    "outros": {
        "frases": [
            "a estrada de terra da comunidade {estrada}",
            "a energia {energia} no sitio",
            "o sinal de {sinal} nao chega aqui",
            "quando vai ser a {festa}",
            "preciso de {doc_pessoal}",
            "o postinho de saude {saude}",
            "meu {animal} {problema_animal}",
            "a coleta de lixo nao passa no bairro rural",
            "quero vaga na {vaga}",
            "como faco minha {social}",
        ],
        "estrada": ["virou atoleiro", "ta cheia de buraco", "precisa de patrolamento", "tem uma valeta enorme"],
        "energia": ["vive caindo", "ta fraca", "fica oscilando", "acabou de novo"],
        "sinal": ["tv", "radio", "telefone", "internet"],
        "festa": ["festa junina da escola", "quermesse", "reuniao da associacao", "missa da capela"],
        "doc_pessoal": ["segunda via do rg", "titulo de eleitor", "certidao de nascimento", "carteira de trabalho"],
        "saude": ["ta sem medico", "fechou", "nao tem remedio de pressao", "nao tem vacina"],
        "animal": ["gato", "cachorro", "papagaio"],
        "problema_animal": ["ta doente", "sumiu", "ta mancando", "nao come"],
        "vaga": ["creche", "escola municipal", "turma de alfabetizacao de adultos"],
        "social": ["aposentadoria rural no inss", "inscricao no bolsa familia", "carteirinha do idoso"],
    },
}
ABERTURAS = ["", "", "bom dia, ", "boa tarde seu tecnico, ", "ola, ", "por favor, ",
             "oi dona tecnica, ", "socorro, ", "queria saber, "]
FECHAMENTOS = ["", "", " obrigado", " deus abencoe", " to precisando muito", " ja pedi antes",
               " urgente", " me ajuda"]


def bagunca(texto: str) -> str:
    """Simula erros comuns de digitacao do agricultor (letra faltando, tudo em maiusculo)."""
    if random.random() < 0.25:
        i = random.randrange(len(texto))
        texto = texto[:i] + texto[i + 1:]
    if random.random() < 0.2:
        texto = texto.upper()
    return texto


def frase_treino(cat: str) -> str:
    t = TEMPLATES[cat]
    frase = random.choice(t["frases"])
    campos = {k: random.choice(v) for k, v in t.items() if k != "frases"}
    campos.update(cultura=random.choice(CULTURAS), lugar=random.choice(LUGARES), tempo=random.choice(TEMPOS))
    texto = random.choice(ABERTURAS) + frase.format(**campos) + random.choice(FECHAMENTOS)
    return bagunca(" ".join(texto.split()))


def gerar_treino():
    # Base propositalmente DESBALANCEADA (como na vida real: chega muito mais
    # pedido de praga do que de solo). O modelo usa class_weight="balanced".
    quantidades = {"pragas": 160, "doencas": 120, "agua": 110, "solo": 80, "credito": 70, "outros": 70}
    linhas = []
    for cat, qtd in quantidades.items():
        vistos = set()
        while len(vistos) < qtd:
            texto = frase_treino(cat)
            if texto not in vistos:
                vistos.add(texto)
                linhas.append({"texto": texto, "categoria": cat})
    df = pd.DataFrame(linhas).sample(frac=1, random_state=SEMENTE)
    destino = RAIZ / "dados" / "treino" / "solicitacoes_treino.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(destino, index=False, encoding="utf-8")
    print(f"treino: {len(df)} linhas -> {destino.relative_to(RAIZ)}")


# ===========================================================================
# 2) Lotes de entrada (textos escritos a mao, diferentes dos templates)
# ===========================================================================
NOMES = ["Ana Teste", "Bruno Ficticio", "Carla Exemplo", "Diego Sintetico",
         "Elisa Modelo", "Fabio Demo", "Gabi Simulada", "Heitor Fake",
         "Iara Amostra", "Joao Inventado", "Kelly Prototipo", "Lucas Mock"]

# (texto, cultura)
TEXTOS_COOPERATIVA = [
    ("A lagarta tomou conta do milho, já abri o cartucho e tá cheio de serragem molhada", "milho"),
    ("O poço tá secando e não tenho como molhar a horta, faz 20 dias sem chuva", "hortaliças"),
    ("Meu tomate tá com umas manchas pretas nas folhas e os frutos apodrecendo no pé", "tomate"),
    ("Quero fazer a análise da terra antes de plantar o feijão, como coleto a amostra? "
     "Meu zap é (15) 99876-5432", "feijão"),
    ("Tem pulgão e formiga cortadeira acabando com a couve, as crianças brincam na horta "
     "e não queria usar veneno forte", "couve"),
    ("Como tiro o CAF? O banco disse que sem ele não sai o Pronaf", ""),
    ("Folha do feijão cheia de pozinho alaranjado que sai no dedo", "feijão"),
    ("Terra da roça tá muito azeda, o técnico falou em calcário mas não sei quanto", "mandioca"),
    ("A bomba do gotejo queimou e o pimentão tá murchando no sol", "pimentão"),
    ("Mandarová comendo todas as folhas da mandioca, lavoura inteira pelada", "mandioca"),
]
TEXTOS_BALCAO = [  # computador antigo da Casa da Agricultura: CP1252 com ';'
    ("Feijão amarelando por igual, as folhas de baixo primeiro, acho que falta adubo", "feijão"),
    ("Quero vender alface e mandioca pra merenda da escola, quando abre a chamada pública?", ""),
    ("Broca no pé de banana, o tronco tá cheio de furo e a bananeira tombando", "banana"),
    ("Nascente secou e a família tá sem água pra beber e pros animais", ""),
    ("A enxurrada abriu uma valeta no meio da roça e tá levando a terra embora", "milho"),
    ("Garantia-Safra: perdi o milho na estiagem e o prazo pra avisar vence semana que vem", "milho"),
    ("oi", ""),  # curto demais: deve ser rejeitado pela validacao
]
TEXTOS_SINDICATO = [  # planilha que o sindicato rural manda
    ("Mosca-branca demais no tomate da estufa, as folhas tão ficando amarelas e meladas", "tomate"),
    ("Requeima na batata depois da chuvarada, as folhas escureceram de um dia pro outro", "batata"),
    ("Preciso montar uma cisterna pra guardar água da chuva pra horta", "hortaliças"),
    ("Quero começar a fazer composto com esterco e palhada, qual a receita?", ""),
    ("O Pronaf foi negado e não explicaram o motivo", ""),
    ("A estrada vicinal tá cheia de buraco e o caminhão do leite não passa", ""),  # fora do escopo
    ("Sinal de celular não pega no sítio", ""),  # fora do escopo
]
TEXTOS_SITE = [
    ("Vaquinha e lesma acabando com as mudas de alface, já perdi metade do canteiro", "alface"),
    ("Meu filho de 8 anos passou mal e vomitou depois que eu pulverizei a lavoura do lado de casa!!", "milho"),
    ("Milho com as folhas cheias de pústulas marrons, parece ferrugem, tá se espalhando rápido pela roça", "milho"),
    ("Quanto tempo devo ligar o aspersor no maracujá nesse calorão? CPF 123.456.789-09 para cadastro", "maracujá"),
    ("Quero saber se tenho direito ao Pronaf Mulher pra comprar uma estufa", ""),
]

# Fila do tecnico exportada pelo Fala, Lavoura! (mesmo formato de dados/fila_tecnico.jsonl
# do projeto de GenAI). As quatro primeiras sao casos que a IA generativa encaminhou de
# verdade nos testes do app; as demais completam o lote.
FICHAS_FALA_LAVOURA = [
    {"id": "87a630e1", "quando": "14/11/2026 14:38", "prioridade": "media", "semaforo": "amarelo",
     "municipio": "Campinas, SP", "cultura": "Milho", "dias_apos_plantio": 65,
     "pergunta": "como está o aquecimento?", "o_que_a_foto_mostra": "",
     "motivo_do_encaminhamento": "a base não cobre bem esse assunto"},
    {"id": "5443655f", "quando": "14/11/2026 15:04", "prioridade": "media", "semaforo": "amarelo",
     "municipio": "Campinas, SP", "cultura": "Milho", "dias_apos_plantio": 65,
     "pergunta": "Quanto de veneno eu ponho na bomba pra matar a lagarta?", "o_que_a_foto_mostra": "",
     "motivo_do_encaminhamento": "caso pede avaliação de um técnico"},
    {"id": "70537f0c", "quando": "14/11/2026 15:06", "prioridade": "máxima", "semaforo": "vermelho",
     "municipio": "Campinas, SP", "cultura": "Milho", "dias_apos_plantio": 65,
     "pergunta": "Minha esposa passou veneno e esta tonta e vomitando", "o_que_a_foto_mostra": "",
     "motivo_do_encaminhamento": "Emergência: possível intoxicação por agrotóxico"},
    {"id": "06b88330", "quando": "14/11/2026 15:10", "prioridade": "media", "semaforo": "amarelo",
     "municipio": "Campinas, SP", "cultura": "Milho", "dias_apos_plantio": 65,
     "pergunta": "Como planta quinoa", "o_que_a_foto_mostra": "",
     "motivo_do_encaminhamento": "a base não cobre bem esse assunto; caso pede avaliação de um técnico"},
    {"id": "b91c02d4", "quando": "15/11/2026 07:12", "prioridade": "media", "semaforo": "amarelo",
     "municipio": "Itapeva, SP", "cultura": "Tomate", "dias_apos_plantio": 48,
     "pergunta": "As folhas do tomate estão com manchas escuras depois dessa chuvarada, o que é?",
     "o_que_a_foto_mostra": "folhas com manchas marrom-escuras de borda irregular e área "
                            "esbranquiçada na face de baixo",
     "motivo_do_encaminhamento": "caso pede avaliação de um técnico"},
    {"id": "c3e7a915", "quando": "15/11/2026 09:40", "prioridade": "baixa", "semaforo": "verde",
     "municipio": "Mirante do Paranapanema, SP", "cultura": "Feijão", "dias_apos_plantio": 70,
     "pergunta": "Perdi o feijão todo na seca, tem algum dinheiro do governo que cobre?",
     "o_que_a_foto_mostra": "", "motivo_do_encaminhamento": "a base não cobre bem esse assunto"},
]


def registro(i, prefixo, texto, cultura, canal, municipio=None, data="2026-11-14 09:00"):
    municipio = municipio or random.choice(list(MUNICIPIOS))
    lat, lon = MUNICIPIOS[municipio]
    return {
        "id_solicitacao": f"{prefixo}-{i:04d}",
        "data_hora": data,
        "canal": canal,
        "nome": random.choice(NOMES),
        "municipio": municipio,
        "comunidade": random.choice(COMUNIDADES),
        "cultura": cultura,
        # o sitio fica fora da cidade: espalha os pontos alguns km em volta do centro
        "latitude": round(lat + random.uniform(-0.04, 0.04), 5),
        "longitude": round(lon + random.uniform(-0.04, 0.04), 5),
        "descricao": texto,
    }


def gerar_entrada():
    pasta = RAIZ / "entrada"
    pasta.mkdir(exist_ok=True)

    # (a) Fila do tecnico do Fala, Lavoura! (JSONL). A ultima linha foi cortada no meio.
    with open(pasta / "fala_lavoura_fila_tecnico.jsonl", "w", encoding="utf-8") as f:
        for ficha in FICHAS_FALA_LAVOURA:
            ficha = {**ficha, "resposta_dada_pela_ia": "", "fontes_consultadas": [],
                     "status": "aguardando técnico"}
            f.write(json.dumps(ficha, ensure_ascii=False) + "\n")
        f.write('{"id": "d00f1e55", "quando": "15/11/2026 10:02", "pergunta": "A geada queim')

    # (b) Cooperativa, CSV em UTF-8. Inclui uma linha DUPLICADA e uma sem municipio valido
    coop = [registro(i + 1, "COOP", t, c, "whatsapp_cooperativa", data=f"2026-11-14 {7 + i % 10:02d}:30")
            for i, (t, c) in enumerate(TEXTOS_COOPERATIVA)]
    coop.append(dict(coop[0]))  # duplicata exata (o robo deve ignorar)
    ruim = registro(99, "COOP", "Lagarta no milho de novo, preciso de visita", "milho", "whatsapp_cooperativa")
    ruim["municipio"], ruim["latitude"], ruim["longitude"] = "Cidade Inexistente", "abc", ""
    coop.append(ruim)
    pd.DataFrame(coop).to_csv(pasta / "cooperativa_whatsapp.csv", index=False, encoding="utf-8")

    # (c) Balcao da Casa da Agricultura: CSV com ';' e encoding CP1252. Tem data no futuro.
    balcao = [registro(i + 1, "BAL", t, c, "balcao") for i, (t, c) in enumerate(TEXTOS_BALCAO)]
    balcao[1]["data_hora"] = "2031-01-01 10:00"  # data invalida (futuro)
    pd.DataFrame(balcao).to_csv(pasta / "casa_agricultura_balcao.csv", index=False, sep=";", encoding="cp1252")

    # (d) Planilha do sindicato rural (Excel)
    sind = [registro(i + 1, "SIN", t, c, "sindicato_rural") for i, (t, c) in enumerate(TEXTOS_SINDICATO)]
    pd.DataFrame(sind).to_excel(pasta / "sindicato_rural_lote.xlsx", index=False)

    # (e) Formulario do site, exportado em JSON
    site = [registro(i + 1, "WEB", t, c, "site") for i, (t, c) in enumerate(TEXTOS_SITE)]
    with open(pasta / "formulario_site.json", "w", encoding="utf-8") as f:
        json.dump(site, f, ensure_ascii=False, indent=2)

    # (f) Arquivo corrompido (exportacao interrompida no meio)
    with open(pasta / "exportacao_interrompida.json", "w", encoding="utf-8") as f:
        f.write('[{"id_solicitacao": "ERR-0001", "descricao": "Lagarta no ')

    total = len(FICHAS_FALA_LAVOURA) + len(coop) + len(balcao) + len(sind) + len(site)
    print(f"entrada: 6 arquivos, {total} registros (+1 linha quebrada no JSONL e 1 arquivo corrompido) -> entrada/")


if __name__ == "__main__":
    gerar_treino()
    gerar_entrada()

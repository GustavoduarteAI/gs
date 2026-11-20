"""
TEMA: RPA + IA/ML (classificador de texto com PLN + clusterizacao)

1) Classificador: le o pedido do agricultor e diz o assunto
   (pragas, doencas, agua, solo ou credito) com uma CONFIANCA.
   - Existe uma sexta classe, "outros", treinada com pedidos que NAO sao de
     assistencia tecnica (estrada, energia, documento pessoal, festa...). Ela
     nunca vai para o sistema de ATER: o robo manda para um tecnico encaminhar.
   - Dicionario da Roca (o mesmo do Fala, Lavoura!): antes de vetorizar, expressoes
     populares ganham o termo tecnico ao lado ("bicho comendo a folha" -> "lagarta
     praga"; "dinheiro do banco" -> "pronaf credito rural"). E expansao de texto,
     uma tecnica classica de PLN.
   - TF-IDF de palavras (pega "boca de lobo") + TF-IDF de pedacos de letras
     (aguenta erro de digitacao e escrita falada, tipo "praga" x "pragua").
   - Regressao Logistica com class_weight="balanced", porque a base e
     desbalanceada (chega muito mais pedido de praga do que de solo).
   - Se a confianca ficar abaixo do limiar, o robo NAO decide: manda para um tecnico.

2) KMeans: agrupa os pedidos pela localizacao para achar "focos regionais"
   (muitos pedidos parecidos perto um do outro, por exemplo um surto de lagarta),
   o que ajuda a Casa da Agricultura a planejar visitas coletivas e dias de campo.
"""
import json
import re

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import FeatureUnion, Pipeline

from src.config import ARQ_DICIONARIO, ARQ_MODELO, ARQ_TREINO, LIMIAR_CONFIANCA, MODELO_EXTERNO
from src.logs import obter_logger
from src.validacao import normalizar

log = obter_logger("modelo")

CATEGORIAS = ["pragas", "doencas", "agua", "solo", "credito"]  # assuntos da ATER
FORA = "outros"  # pedido que nao e de assistencia tecnica


def _carregar_dicionario() -> dict[str, str]:
    try:
        dados = json.loads(ARQ_DICIONARIO.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erro:
        log.warning("Dicionario da Roca indisponivel (%s): classificando sem ele", erro)
        return {}
    return {normalizar(k): normalizar(v) for k, v in dados.items() if not k.startswith("_")}


DICIONARIO = _carregar_dicionario()
# uma regex so com todas as expressoes (as mais longas primeiro)
_RE_DICIONARIO = (re.compile(r"\b(" + "|".join(re.escape(k) for k in sorted(DICIONARIO, key=len, reverse=True))
                             + r")") if DICIONARIO else None)


def expandir(texto: str) -> str:
    """Normaliza e acrescenta os termos tecnicos das expressoes populares encontradas."""
    t = normalizar(texto)
    if _RE_DICIONARIO is None:
        return t
    extras = [DICIONARIO[m] for m in dict.fromkeys(_RE_DICIONARIO.findall(t))]
    return f"{t} {' '.join(extras)}".strip()


def criar_pipeline(usar_dicionario: bool = True) -> Pipeline:
    preparar = expandir if usar_dicionario else normalizar
    vetorizador = FeatureUnion([
        ("palavras", TfidfVectorizer(preprocessor=preparar, ngram_range=(1, 2), min_df=1)),
        ("letras", TfidfVectorizer(preprocessor=preparar, analyzer="char_wb",
                                   ngram_range=(3, 5), min_df=2, sublinear_tf=True)),
    ])
    classificador = LogisticRegression(class_weight="balanced", max_iter=2000, C=4.0)
    return Pipeline([("tfidf", vetorizador), ("clf", classificador)])


def treinar(salvar=True) -> Pipeline:
    if not ARQ_TREINO.exists():
        raise FileNotFoundError(
            f"Base de treino nao encontrada em {ARQ_TREINO}. Rode: python dados/gerar_dados.py")
    df = pd.read_csv(ARQ_TREINO, encoding="utf-8").dropna()
    log.info("Treinando com %d exemplos. Distribuicao: %s",
             len(df), df["categoria"].value_counts().to_dict())

    pipeline = criar_pipeline()
    # validacao cruzada so como sanidade (base sintetica, vai dar alto mesmo)
    f1 = cross_val_score(pipeline, df["texto"], df["categoria"], cv=5, scoring="f1_macro")
    log.info("F1 macro na validacao cruzada (base de treino sintetica): %.3f", f1.mean())

    pipeline.fit(df["texto"], df["categoria"])
    if salvar:
        joblib.dump(pipeline, ARQ_MODELO)
        log.info("Modelo salvo em %s", ARQ_MODELO.name)
    return pipeline


def _carregar_externo():
    """Modelo de outra disciplina: so e aceito se tiver predict_proba e as mesmas categorias."""
    try:
        externo = joblib.load(MODELO_EXTERNO)
        if not hasattr(externo, "predict_proba") or not set(externo.classes_) <= set(CATEGORIAS + [FORA]):
            raise ValueError(f"o modelo precisa de predict_proba e categorias dentro de {CATEGORIAS + [FORA]}")
        log.info("Usando modelo externo: %s", MODELO_EXTERNO)
        return externo
    except Exception as erro:
        log.error("Modelo externo invalido (%s). Usando o modelo proprio.", erro)
        return None


def carregar() -> Pipeline:
    """Carrega o modelo salvo; se nao existir ou estiver quebrado, treina de novo."""
    if MODELO_EXTERNO and (externo := _carregar_externo()) is not None:
        return externo
    if ARQ_MODELO.exists():
        try:
            return joblib.load(ARQ_MODELO)
        except Exception as erro:
            log.warning("Modelo salvo ilegivel (%s). Vou treinar de novo.", erro)
    return treinar()


def classificar(modelo: Pipeline, textos: list[str], limiar=LIMIAR_CONFIANCA) -> list[dict]:
    probabilidades = modelo.predict_proba(textos)
    classes = modelo.classes_
    resultado = []
    for linha in probabilidades:
        ordem = np.argsort(linha)[::-1]
        melhor, segunda = ordem[0], ordem[1]
        confianca = float(linha[melhor])
        resultado.append({
            "categoria": classes[melhor],
            "confianca": round(confianca, 3),
            "segunda_opcao": f"{classes[segunda]} ({linha[segunda]:.0%})",
            "precisa_revisao": confianca < limiar or classes[melhor] == FORA,
        })
    return resultado


def palavras_mais_importantes(modelo: Pipeline, n=6) -> dict:
    """Mostra quais palavras mais pesam em cada categoria (ajuda a explicar o modelo)."""
    if not hasattr(modelo, "named_steps") or "tfidf" not in modelo.named_steps:
        return {}  # modelo externo com outra estrutura
    vetor_palavras = modelo.named_steps["tfidf"].transformer_list[0][1]
    nomes = vetor_palavras.get_feature_names_out()
    coef = modelo.named_steps["clf"].coef_[:, :len(nomes)]
    return {cat: [nomes[i] for i in np.argsort(coef[k])[::-1][:n]]
            for k, cat in enumerate(modelo.classes_)}


def pontos_criticos(df: pd.DataFrame, max_grupos=5) -> pd.DataFrame:
    """KMeans nas coordenadas. Devolve um resumo por foco (centro, qtd, assunto e culturas)."""
    if len(df) < 4:
        return pd.DataFrame()
    k = min(max_grupos, max(2, len(df) // 4))
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    df = df.copy()
    df["grupo"] = km.fit_predict(df[["latitude", "longitude"]].astype(float))
    resumo = (df.groupby("grupo")
                .agg(qtd_pedidos=("id_solicitacao", "count"),
                     municipios=("municipio", lambda s: ", ".join(sorted(set(s)))),
                     assunto_mais_comum=("categoria", lambda s: s.mode().iat[0]),
                     culturas=("cultura", lambda s: ", ".join(sorted({c for c in s if c})) or "-"),
                     prioridade_alta=("prioridade", lambda s: int((s == "ALTA").sum())))
                .reset_index())
    resumo["centro_lat"] = km.cluster_centers_[resumo["grupo"], 0].round(4)
    resumo["centro_lon"] = km.cluster_centers_[resumo["grupo"], 1].round(4)
    resumo["mapa"] = ("https://www.openstreetmap.org/?mlat=" + resumo["centro_lat"].astype(str)
                      + "&mlon=" + resumo["centro_lon"].astype(str) + "#map=11/"
                      + resumo["centro_lat"].astype(str) + "/" + resumo["centro_lon"].astype(str))
    return resumo.sort_values("qtd_pedidos", ascending=False)

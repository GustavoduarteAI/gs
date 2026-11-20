"""
TEMA: Regras inteligentes + integracao com API publica + integracao com a GenAI

A prioridade NAO e decidida por uma caixa-preta. Ela soma pontos explicaveis:
  - peso base do assunto (que veio do modelo de ML);
  - palavras de RISCO no texto (intoxicacao, crianca perto da aplicacao, veneno
    na agua, fogo, lavoura inteira se perdendo) => ALTA direto;
  - sinal do Fala, Lavoura! (GenAI): ficha com semaforo vermelho => +2, e
    emergencia apontada pela IA => ALTA direto;
  - reincidencia ("ja pedi", "ninguem veio") => +1. Frases como "faz 20 dias" NAO
    contam: no campo elas quase sempre falam da seca, nao de um pedido antigo;
  - prazo correndo em pedido de credito (Garantia-Safra, chamada publica) => +1;
  - PREVISAO DO TEMPO dos proximos 3 dias no municipio (API Open-Meteo):
      geada (minima <= 3 C) em pedido de lavoura => +2;
      calor sem chuva em pedido de agua => +2 (sem chuva, mas sem calor => +1);
      chuva acumulada alta em pedido de doenca => +2 (umidade favorece fungo).
Cada ponto vira uma frase na coluna "justificativa", para o tecnico entender o porque.

A chamada da API tem timeout, retry com espera e um cache em disco. Se a API
cair, o robo usa a ultima previsao conhecida ou segue sem o criterio de clima,
mas nunca para.
"""
import re
import time

import requests

from src.config import (CALOR_SECA_C, CHUVA_FUNGO_MM, CHUVA_SECA_MM, CLIMA_API_URL, GEADA_C,
                        TIMEOUT_SEGUNDOS)
from src.logs import obter_logger
from src.resiliencia import RegistroJSON, com_retry, resumir_erro
from src.validacao import MUNICIPIOS, chave_municipio, normalizar

log = obter_logger("prioridade")

PESO_CATEGORIA = {"pragas": 2, "doencas": 2, "agua": 2, "solo": 1, "credito": 1}
EQUIPE = {
    "pragas": "Casa da Agricultura - Fitossanidade (pragas)",
    "doencas": "Casa da Agricultura - Fitossanidade (doenças)",
    "agua": "Casa da Agricultura - Água e Irrigação",
    "solo": "Casa da Agricultura - Solos e Adubação",
    "credito": "Escritório Local - Crédito e Políticas Públicas",
}
PRAZO_DIAS = {"ALTA": 2, "MÉDIA": 7, "BAIXA": 15}
LAVOURA = {"pragas", "doencas", "agua", "solo"}  # assuntos em que a geada importa

# padroes de risco (texto ja normalizado: minusculo e sem acento)
RISCO_INTOXICACAO = r"intoxic|envenen|\btont[oa]\b|vomit|passou mal|desmai|tontura|veneno (no olho|na pele|na boca)"
RISCOS = {
    "possível intoxicação por agrotóxico": RISCO_INTOXICACAO,
    "pessoas vulneráveis expostas": r"\bcrianc|gestante|gravida|\bidos[oa]|\bescola\b|\bnenem",
    "veneno perto de água": (r"(poco|nascente|corrego|cisterna|caixa d.?agua|agua de beber|\brio\b)"
                             r".{0,40}(veneno|agrotoxico|embalage|contamin)"
                             r"|(veneno|agrotoxico|embalage).{0,40}(poco|nascente|corrego|cisterna|\brio\b)"),
    "fogo": r"\bfogo\b|queimada|incendio|pegou fogo",
    "risco de perder a lavoura inteira": (r"(lavoura|roca|plantacao|horta|safra|pe de \w+) (inteira|toda)"
                                         r"|perd(er|endo|i) tudo|morrendo tud|alastr|tomou conta|espalh\w* rapido"),
    "família sem água para beber": (r"sem agua (pra|para) (beber|casa|a familia|os animais|a criacao)"
                                    r"|agua de balde|(pra|para) beber"),
}
REINCIDENCIA = (r"ja pedi|ja liguei|ja reclamei|ja mandei|de novo|outra vez"
                r"|ninguem (veio|apareceu|respondeu)|esperando o tecnico")
PRAZO_CORRENDO = r"\bprazo|\bvenc(e|endo|imento)|ultimo dia|termina (amanha|essa semana|semana que vem)|chamada publica"

_cache_disco = None
_cache_execucao = {}
# "disjuntor": depois de 2 falhas seguidas, para de chamar a API nesta execucao
# (nao adianta esperar o retry 10 vezes se o servico claramente caiu)
_disjuntor = {"falhas_seguidas": 0, "aberto": False}


def reiniciar_cache_execucao():
    _cache_execucao.clear()
    _disjuntor.update(falhas_seguidas=0, aberto=False)


class RespostaInvalida(Exception):
    pass


@com_retry(excecoes=(requests.RequestException, RespostaInvalida))
def _consultar_api(lat, lon) -> dict:
    params = {"latitude": lat, "longitude": lon,
              "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
              "forecast_days": 3, "timezone": "America/Sao_Paulo"}
    resposta = requests.get(CLIMA_API_URL, params=params, timeout=TIMEOUT_SEGUNDOS)
    resposta.raise_for_status()
    diario = resposta.json().get("daily", {})
    chuva, tmax, tmin = (diario.get("precipitation_sum"), diario.get("temperature_2m_max"),
                         diario.get("temperature_2m_min"))
    if not all(isinstance(v, list) and v for v in (chuva, tmax, tmin)):
        raise RespostaInvalida("API respondeu sem a previsao diaria")
    return {"chuva_3d_mm": round(sum(v or 0 for v in chuva), 1),
            "tmax_c": max(v for v in tmax if v is not None),
            "tmin_c": min(v for v in tmin if v is not None)}


def previsao(municipio: str):
    """Previsao dos proximos 3 dias para o CENTRO do municipio (nunca o sitio do agricultor)."""
    global _cache_disco
    if _cache_disco is None:
        _cache_disco = RegistroJSON("cache_clima")
    if municipio in _cache_execucao:
        return _cache_execucao[municipio]

    centro = MUNICIPIOS.get(chave_municipio(municipio))
    if not centro:
        return None
    lat, lon = round(centro[1], 2), round(centro[2], 2)
    try:
        if _disjuntor["aberto"]:
            raise RespostaInvalida("disjuntor aberto, API ignorada nesta execucao")
        prev = _consultar_api(lat, lon)
        _cache_disco.definir(municipio, {**prev, "quando": time.time()})
        _disjuntor["falhas_seguidas"] = 0
    except Exception as erro:
        if not _disjuntor["aberto"]:
            _disjuntor["falhas_seguidas"] += 1
            if _disjuntor["falhas_seguidas"] >= 2:
                _disjuntor["aberto"] = True
                log.error("API de clima falhou 2 vezes seguidas: disjuntor aberto nesta execucao")
        guardado = _cache_disco.get(municipio)
        if guardado and time.time() - guardado["quando"] < 12 * 3600:
            prev = {k: guardado[k] for k in ("chuva_3d_mm", "tmax_c", "tmin_c")}
            fonte = "cache (API fora do ar)"
        else:
            prev, fonte = None, "indisponivel"
        log.warning("Clima de %s: %s. Usando %s.", municipio, resumir_erro(erro, 60), fonte)
    _cache_execucao[municipio] = prev
    return prev


def riscos_no_texto(descricao: str, motivo_ia: str = "") -> list[str]:
    texto = normalizar(descricao)
    achados = [nome for nome, padrao in RISCOS.items() if re.search(padrao, texto)]
    if "emergencia" in normalizar(motivo_ia):
        achados.append("emergência apontada pelo Fala, Lavoura!")
    return achados


def detectar_risco(descricao: str, motivo_ia: str = "") -> bool:
    """So a parte de risco, sem depender da API (usada na revisao humana e na avaliacao)."""
    return bool(riscos_no_texto(descricao, motivo_ia))


def emergencia_de_saude(descricao: str, motivo_ia: str = "") -> bool:
    """Intoxicacao: a resposta ao agricultor leva os telefones de emergencia, sem esperar o tecnico."""
    return bool(re.search(RISCO_INTOXICACAO, normalizar(descricao))) or "intoxic" in normalizar(motivo_ia)


def _criterio_clima(categoria, prev, motivos) -> int:
    if prev is None:
        motivos.append("previsão do tempo indisponível (critério ignorado)")
        return 0
    pontos = 0
    chuva, tmax, tmin = prev["chuva_3d_mm"], prev["tmax_c"], prev["tmin_c"]
    if categoria in LAVOURA and tmin <= GEADA_C:
        pontos += 2
        motivos.append(f"risco de geada: mínima de {tmin} °C nos próximos 3 dias (+2)")
    if categoria == "agua":
        if chuva < CHUVA_SECA_MM and tmax >= CALOR_SECA_C:
            pontos += 2
            motivos.append(f"calor sem chuva: {chuva} mm em 3 dias e máxima de {tmax} °C (+2)")
        elif chuva < CHUVA_SECA_MM:
            pontos += 1
            motivos.append(f"sem chuva útil prevista: {chuva} mm em 3 dias (+1)")
        else:
            motivos.append(f"chuva prevista: {chuva} mm em 3 dias")
    if categoria == "doencas":
        if chuva >= CHUVA_FUNGO_MM:
            pontos += 2
            motivos.append(f"chuva favorece doença de fungo: {chuva} mm em 3 dias (+2)")
        else:
            motivos.append(f"pouca chuva prevista: {chuva} mm em 3 dias")
    return pontos


def avaliar(categoria: str, descricao: str, municipio: str, semaforo_ia: str = "",
            motivo_ia: str = "") -> dict:
    texto = normalizar(descricao)
    pontos = PESO_CATEGORIA.get(categoria, 1)
    motivos = [f"assunto {categoria} (peso {pontos})"]

    riscos = riscos_no_texto(descricao, motivo_ia)
    if riscos:
        motivos.append("RISCO: " + ", ".join(riscos))

    if normalizar(semaforo_ia) == "vermelho":
        pontos += 2
        motivos.append("Fala, Lavoura! marcou a ficha com semáforo vermelho (+2)")

    if re.search(REINCIDENCIA, texto):
        pontos += 1
        motivos.append("pedido antigo ou repetido (+1)")

    if categoria == "credito" and re.search(PRAZO_CORRENDO, texto):
        pontos += 1
        motivos.append("prazo de programa ou documento correndo (+1)")

    prev = None
    if categoria in LAVOURA:
        prev = previsao(municipio)
        pontos += _criterio_clima(categoria, prev, motivos)

    if riscos or pontos >= 4:
        nivel = "ALTA"
    elif pontos >= 2:
        nivel = "MÉDIA"
    else:
        nivel = "BAIXA"

    return {
        "prioridade": nivel,
        "pontuacao": pontos,
        "urgente": bool(riscos),
        "emergencia_saude": emergencia_de_saude(descricao, motivo_ia),
        "chuva_3d_mm": prev["chuva_3d_mm"] if prev else None,
        "tmin_c": prev["tmin_c"] if prev else None,
        "tmax_c": prev["tmax_c"] if prev else None,
        "equipe_responsavel": EQUIPE.get(categoria, "Triagem manual"),
        "prazo_dias": PRAZO_DIAS[nivel],
        "justificativa": "; ".join(motivos),
    }

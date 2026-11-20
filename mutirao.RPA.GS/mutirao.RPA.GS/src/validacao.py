"""
TEMA: Qualidade de dados (GIGO: Garbage In, Garbage Out) + protecao de dados

Antes de qualquer IA, o robo confere se o pedido faz sentido. Dado ruim
nao segue no fluxo: vai para a aba "Rejeitadas" com o motivo e uma mensagem
pedindo para o agricultor completar.

Tambem e aqui que os dados pessoais saem de cena (LGPD):
  - o nome vira um pseudonimo (hash), e o nome original nao vai para nenhuma saida;
  - CPF, telefone e e-mail digitados no meio do texto sao mascarados ANTES
    de o texto chegar no modelo, no sistema de ATER ou no relatorio.
"""
import hashlib
import os
import re
import unicodedata
from datetime import datetime, timedelta

from src.logs import obter_logger

log = obter_logger("validacao")

# Centro aproximado dos municipios atendidos (dado publico). Usado para validar
# e para consultar o clima: a API nunca recebe a localizacao do sitio.
MUNICIPIOS = {
    "campinas": ("Campinas", -22.9056, -47.0608),
    "piracicaba": ("Piracicaba", -22.7253, -47.6492),
    "botucatu": ("Botucatu", -22.8858, -48.4450),
    "registro": ("Registro", -24.4979, -47.8449),
    "itapeva": ("Itapeva", -23.9822, -48.8756),
    "ibiuna": ("Ibiúna", -23.6564, -47.2225),
    "mogi das cruzes": ("Mogi das Cruzes", -23.5229, -46.1880),
    "mirante do paranapanema": ("Mirante do Paranapanema", -22.2903, -51.9064),
    "socorro": ("Socorro", -22.5914, -46.5289),
    "sao miguel arcanjo": ("São Miguel Arcanjo", -23.8781, -47.9972),
}
# retangulo que cobre o estado de Sao Paulo (aproximado)
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = -25.40, -19.70, -53.20, -44.10
MIN_CARACTERES = 15
MIN_PALAVRAS = 3
# o Fala, Lavoura! grava "14/11/2026 15:04"; os outros canais usam ISO
FORMATOS_DATA = ("%d/%m/%Y %H:%M", "%d/%m/%Y")

RE_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
RE_TELEFONE = re.compile(r"(\(?\d{2}\)?\s?)?9?\d{4}-?\d{4}\b")
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def normalizar(texto: str) -> str:
    """minusculo e sem acento: 'Ibiúna' -> 'ibiuna'"""
    sem_acento = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def chave_municipio(texto: str) -> str:
    """'Campinas, SP' / 'Campinas (São Paulo)' / 'campinas-sp' -> 'campinas'"""
    t = normalizar(texto)
    t = re.split(r"[,(/]| - ", t)[0]
    t = re.sub(r"[- ]sp$", "", t.strip())
    return t.strip()


def mascarar_dados_pessoais(texto: str) -> tuple[str, list[str]]:
    encontrados = []
    for regex, rotulo in ((RE_EMAIL, "[EMAIL]"), (RE_CPF, "[CPF]"), (RE_TELEFONE, "[TELEFONE]")):
        if regex.search(texto):
            encontrados.append(rotulo.strip("[]").lower())
            texto = regex.sub(rotulo, texto)
    return texto, encontrados


def pseudonimo(nome: str) -> str:
    # o "sal" fica no .env: sem ele nao da para refazer o hash a partir de uma lista de nomes
    sal = os.getenv("PSEUDONIMO_SAL", "troque-este-sal")
    return "agr_" + hashlib.sha256((sal + normalizar(nome)).encode()).hexdigest()[:10]


def _vazio(valor) -> bool:
    return valor is None or str(valor).strip() in ("", "nan", "None")


def _coordenada(valor):
    try:
        return float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return None


def ler_data(valor) -> datetime:
    texto = str(valor).strip()
    try:
        return datetime.fromisoformat(texto)
    except ValueError:
        pass
    for formato in FORMATOS_DATA:
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    raise ValueError(f"data invalida: {texto}")


def validar(registro: dict) -> tuple[dict | None, list[str]]:
    """
    Devolve (registro_limpo, []) se estiver ok, ou (None, [motivos]) se nao.
    O registro limpo ja vem anonimizado.
    """
    motivos = []

    if _vazio(registro.get("id_solicitacao")):
        motivos.append("sem identificador")

    descricao = "" if _vazio(registro.get("descricao")) else " ".join(str(registro["descricao"]).split())
    if len(descricao) < MIN_CARACTERES or len(descricao.split()) < MIN_PALAVRAS:
        motivos.append("descrição muito curta para entender o problema")

    data = None
    try:
        data = ler_data(registro.get("data_hora"))
        if data > datetime.now() + timedelta(days=1):
            motivos.append("data no futuro")
    except ValueError:
        motivos.append("data inválida")

    # localizacao: aceita municipio conhecido OU coordenada dentro do estado de SP
    municipio = MUNICIPIOS.get(chave_municipio(registro.get("municipio")))
    lat, lon = _coordenada(registro.get("latitude")), _coordenada(registro.get("longitude"))
    coord_ok = lat is not None and lon is not None and LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX
    if not municipio and not coord_ok:
        motivos.append("localização não identificada (município e coordenadas inválidos)")
    if municipio and not coord_ok:  # usa o centro do municipio
        lat, lon = municipio[1], municipio[2]

    if motivos:
        return None, motivos

    descricao_segura, achados = mascarar_dados_pessoais(descricao)
    if achados:
        log.info("%s: dados pessoais mascarados no texto (%s)",
                 registro["id_solicitacao"], ", ".join(achados))

    limpo = {
        "id_solicitacao": str(registro["id_solicitacao"]).strip(),
        "data_hora": data.strftime("%Y-%m-%d %H:%M"),
        "canal": registro.get("canal") or "desconhecido",
        "agricultor": pseudonimo(registro.get("nome") or ""),
        "municipio": municipio[0] if municipio else "Não informado",
        "comunidade": "" if _vazio(registro.get("comunidade")) else str(registro["comunidade"]),
        "cultura": "" if _vazio(registro.get("cultura")) else str(registro["cultura"]).strip().capitalize(),
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        "descricao": descricao_segura,
        "dados_pessoais_mascarados": ", ".join(achados),
        "arquivo_origem": registro.get("arquivo_origem", ""),
        # sinais da triagem feita pela IA generativa (so existem nas fichas do Fala, Lavoura!)
        "semaforo_ia": "" if _vazio(registro.get("semaforo_ia")) else str(registro["semaforo_ia"]),
        "motivo_ia": "" if _vazio(registro.get("motivo_ia")) else str(registro["motivo_ia"]),
    }
    return limpo, []

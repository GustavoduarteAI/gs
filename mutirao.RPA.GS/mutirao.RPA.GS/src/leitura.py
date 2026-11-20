"""
TEMA: Arquivos e I/O

Le os pedidos de assistencia tecnica que chegam na pasta entrada/ em varios formatos.
Cada canal do campo manda de um jeito, entao o robo precisa:
  - descobrir o ENCODING sozinho (o computador antigo da Casa da Agricultura grava
    em CP1252, o resto em UTF-8);
  - descobrir o separador do CSV (',' ou ';');
  - ler em PEDACOS (chunking) para nao estourar a RAM se vier um arquivo gigante;
  - ler a fila do Fala, Lavoura! (JSONL) LINHA A LINHA: uma linha quebrada e
    pulada sem perder as outras;
  - ler so as colunas que interessam e tudo como texto (dtype=str);
  - mandar para QUARENTENA o arquivo que nao der para ler, sem parar o resto.
"""
import csv
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.config import PASTA_QUARENTENA, TAMANHO_LOTE
from src.logs import obter_logger

log = obter_logger("leitura")

try:
    from charset_normalizer import from_path
except ImportError:  # biblioteca quebrada ou ausente: usamos o plano B mais abaixo
    from_path = None

COLUNAS = ["id_solicitacao", "data_hora", "canal", "nome", "municipio", "comunidade",
           "cultura", "latitude", "longitude", "descricao", "semaforo_ia", "motivo_ia"]
EXTENSOES = {".csv", ".json", ".xlsx", ".jsonl"}


class ArquivoInvalido(Exception):
    """Arquivo que existe mas nao da para usar (corrompido, sem colunas, vazio)."""


def hash_arquivo(caminho: Path) -> str:
    """SHA-256 lendo em blocos de 64 KB (nao carrega o arquivo inteiro na memoria)."""
    sha = hashlib.sha256()
    with open(caminho, "rb") as f:
        while bloco := f.read(65536):
            sha.update(bloco)
    return sha.hexdigest()[:16]


def _encoding_por_tentativa(caminho: Path) -> str:
    """Plano B: tenta decodificar como UTF-8; se der UnicodeDecodeError, e CP1252."""
    with open(caminho, "rb") as f:
        amostra = f.read(1 << 20)
    try:
        amostra.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "cp1252"


def detectar_encoding(caminho: Path) -> str:
    if from_path is None:
        return _encoding_por_tentativa(caminho)
    resultado = from_path(caminho).best()
    if resultado is None:
        return _encoding_por_tentativa(caminho)
    encoding = resultado.encoding
    # charset_normalizer as vezes devolve parentes do cp1252; padronizamos
    if encoding.lower() in {"windows-1252", "cp1252", "latin_1", "iso8859_1", "cp1250"}:
        encoding = "cp1252"
    return encoding


def _detectar_separador(caminho: Path, encoding: str) -> str:
    with open(caminho, encoding=encoding, newline="") as f:
        amostra = f.read(4096)
    try:
        return csv.Sniffer().sniff(amostra, delimiters=",;|\t").delimiter
    except csv.Error:
        return ","


def _ler_csv(caminho: Path):
    encoding = detectar_encoding(caminho)
    sep = _detectar_separador(caminho, encoding)
    log.info("%s: encoding=%s, separador='%s'", caminho.name, encoding, sep)
    # chunksize devolve um iterador: le TAMANHO_LOTE linhas por vez
    pedacos = pd.read_csv(caminho, sep=sep, encoding=encoding, dtype=str,
                          usecols=lambda c: c in COLUNAS, chunksize=TAMANHO_LOTE)
    for pedaco in pedacos:
        yield from pedaco.to_dict("records")


def _ler_excel(caminho: Path):
    try:
        df = pd.read_excel(caminho, dtype=str, engine="calamine")  # motor rapido (Rust)
    except Exception as erro:  # sem calamine instalado, cai para o openpyxl
        log.warning("calamine indisponivel (%s), usando openpyxl", erro)
        df = pd.read_excel(caminho, dtype=str, engine="openpyxl")
    df = df[[c for c in df.columns if c in COLUNAS]]
    yield from df.to_dict("records")


def _ler_json(caminho: Path):
    with open(caminho, encoding=detectar_encoding(caminho)) as f:
        dados = json.load(f)
    if isinstance(dados, dict):  # aceita {"pedidos": [...]} ou uma lista direta
        dados = dados.get("pedidos", [dados])
    for item in dados:
        yield {c: (None if item.get(c) is None else str(item.get(c))) for c in COLUNAS}


def ficha_fala_lavoura(ficha: dict) -> dict:
    """
    Traduz uma ficha da fila do tecnico do Fala, Lavoura! (projeto de GenAI) para
    o formato do robo. A ficha ja vem anonimizada (sem nome, CPF ou telefone) e
    traz a triagem da IA generativa: o semaforo do Fiscal da Roca e o motivo.
    """
    descricao = str(ficha.get("pergunta") or "").strip()
    foto = str(ficha.get("o_que_a_foto_mostra") or "").strip()
    if foto:
        descricao = f"{descricao} Foto: {foto}".strip()
    return {
        "id_solicitacao": f"FL-{ficha['id']}" if ficha.get("id") else None,
        "data_hora": ficha.get("quando"),
        "canal": "fala_lavoura",
        "nome": None,
        "municipio": ficha.get("municipio"),
        "comunidade": None,
        "cultura": ficha.get("cultura"),
        "latitude": None,
        "longitude": None,
        "descricao": descricao,
        "semaforo_ia": ficha.get("semaforo"),
        "motivo_ia": ficha.get("motivo_do_encaminhamento"),
    }


def _ler_jsonl(caminho: Path):
    """Uma ficha por linha. Linha quebrada e registrada no log e pulada."""
    with open(caminho, encoding=detectar_encoding(caminho)) as f:
        for numero, linha in enumerate(f, start=1):
            if not linha.strip():
                continue
            try:
                ficha = json.loads(linha)
            except json.JSONDecodeError as erro:
                log.warning("%s linha %d ilegivel (%s): pulada", caminho.name, numero, erro.msg)
                continue
            yield ficha_fala_lavoura(ficha)


LEITORES = {".csv": _ler_csv, ".xlsx": _ler_excel, ".json": _ler_json, ".jsonl": _ler_jsonl}


def ler_arquivo(caminho: Path) -> list[dict]:
    """Le um arquivo inteiro e devolve a lista de registros, marcando a origem."""
    if not caminho.exists():
        raise FileNotFoundError(caminho)
    leitor = LEITORES.get(caminho.suffix.lower())
    if leitor is None:
        raise ArquivoInvalido(f"extensao {caminho.suffix} nao suportada")
    try:
        registros = list(leitor(caminho))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError,
            pd.errors.ParserError, KeyError) as erro:
        raise ArquivoInvalido(f"{type(erro).__name__}: {erro}") from erro
    if not registros:
        raise ArquivoInvalido("arquivo sem registros")
    if "descricao" not in registros[0]:
        raise ArquivoInvalido("coluna 'descricao' nao encontrada")
    for r in registros:
        r["arquivo_origem"] = caminho.name
    return registros


def mandar_para_quarentena(caminho: Path, motivo: str):
    """Copia o arquivo problematico + um .motivo.txt explicando o que houve."""
    destino = PASTA_QUARENTENA / f"{datetime.now():%Y%m%d_%H%M%S}_{caminho.name}"
    try:
        shutil.copy2(caminho, destino)
        # modo "x": cria exclusivo, nunca sobrescreve um motivo anterior
        with open(destino.with_name(destino.name + ".motivo.txt"), "x", encoding="utf-8") as f:
            f.write(f"Arquivo: {caminho.name}\nMotivo: {motivo}\n")
    except (OSError, FileExistsError) as erro:
        log.error("Nao consegui copiar %s para a quarentena: %s", caminho.name, erro)
    log.error("QUARENTENA: %s (%s)", caminho.name, motivo)


def listar_arquivos(pasta: Path) -> list[Path]:
    return sorted(p for p in pasta.iterdir()
                  if p.is_file() and p.suffix.lower() in EXTENSOES and not p.name.startswith("~$"))

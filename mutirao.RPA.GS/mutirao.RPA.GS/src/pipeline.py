"""
Orquestrador: o PROCESSO do robo, dividido em TAREFAS ligadas por RELACOES
(cada tarefa so roda com a saida da anterior):

  T1 Ler arquivos  >  T2 Tirar duplicadas  >  T3 Validar (GIGO + LGPD)
        |                                            |
   (quarentena)                                 (rejeitadas)
                                                     v
  T6 Registrar no portal  <  T5 Priorizar  <  T4 Classificar (ML)
        |        (Selenium)     (regras+clima)       |
   (pendentes)                                (revisao humana)
        v
  T7 Responder agricultor + retorno ao Fala, Lavoura!  >  T8 Focos (KMeans)  >  T9 Relatorios

Os parenteses sao os CAMINHOS SEGUROS: o que o robo nao resolve vai para uma
fila especifica com o motivo, e o resto continua.
"""
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import psutil

from src import leitura, modelo, prioridade, relatorio, validacao
from src.config import ARQ_RETORNO_FALA_LAVOURA, PASTA_ENTRADA
from src.logs import obter_logger
from src.resiliencia import RegistroJSON
from src.rpa_portal import CredenciaisInvalidas, PortalIndisponivel, RoboPortal, portal_no_ar

log = obter_logger("pipeline")

NOME_CATEGORIA = {"pragas": "praga na lavoura", "doencas": "doença na lavoura",
                  "agua": "água e irrigação", "solo": "solo e adubação",
                  "credito": "crédito e programas do governo"}
EMERGENCIA = ("Se alguém passou mal com veneno, não espere: afaste a pessoa da área, lave a pele com "
              "bastante água e ligue para o SAMU (192) ou o Disque-Intoxicação (0800 722 6001). ")


def assinatura_registro(r: dict) -> str:
    """Resumo do conteudo do pedido: muda se o agricultor corrigir algum dado."""
    campos = ("descricao", "data_hora", "municipio", "latitude", "longitude")
    texto = "|".join(str(r.get(c) or "").strip() for c in campos)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]


def mensagem_agricultor(s: dict, status: str) -> str:
    """Mensagem curta e em linguagem simples, pronta para WhatsApp ou para virar audio."""
    alerta = EMERGENCIA if s.get("emergencia_saude") else ""
    if status == "registrada":
        cultura = (f" ({s['cultura'].lower()})" if s.get("cultura") and s["categoria"] != "credito" else "")
        return (f"{alerta}Olá! Seu pedido sobre {NOME_CATEGORIA[s['categoria']]}{cultura} em {s['municipio']} "
                f"foi registrado na Casa da Agricultura com o número {s['protocolo']}. "
                f"Quem vai cuidar: {s['equipe_responsavel']}. "
                f"O técnico deve falar com você em até {s['prazo_dias']} dias.")
    if status == "pendente":
        return (f"{alerta}Olá! Recebemos seu pedido {s['id_solicitacao']}. O sistema da Casa da Agricultura "
                f"está fora do ar agora, mas o registro vai ser feito sozinho assim que ele voltar.")
    if status == "revisao_humana":
        return (f"{alerta}Olá! Recebemos seu pedido {s['id_solicitacao']}. Um técnico vai ler com atenção "
                f"e responder em até 1 dia útil.")
    return (f"Olá! Não conseguimos registrar o pedido {s['id_solicitacao']} porque: {s['motivos']}. "
            f"Mande de novo contando o que está acontecendo, em qual lavoura e em qual cidade.")


def retorno_fala_lavoura(resumo: dict):
    """
    Devolve ao Fala, Lavoura! (GenAI) a situacao de cada ficha que veio da fila do
    tecnico: assim o app pode avisar o agricultor que o caso virou protocolo.
    Uma linha JSON por ficha (o mesmo formato JSONL da fila).
    """
    linhas = []
    for status, lista in (("registrada", resumo["registradas"]), ("revisao_humana", resumo["revisao_humana"]),
                          ("pendente", resumo["pendentes"]), ("rejeitada", resumo["rejeitadas"])):
        for s in lista:
            if not str(s.get("id_solicitacao", "")).startswith("FL-"):
                continue
            linhas.append({"id_ficha": s["id_solicitacao"][3:], "status": status,
                           "protocolo": s.get("protocolo"), "prioridade": s.get("prioridade"),
                           "assunto": s.get("categoria"), "equipe": s.get("equipe_responsavel"),
                           "prazo_dias": s.get("prazo_dias"), "mensagem": s.get("mensagem_agricultor"),
                           "atualizado_em": datetime.now().isoformat(timespec="seconds")})
    if not linhas:
        return 0
    try:
        with open(ARQ_RETORNO_FALA_LAVOURA, "a", encoding="utf-8") as f:  # modo "a": so acrescenta
            for linha in linhas:
                f.write(json.dumps(linha, ensure_ascii=False) + "\n")
    except OSError as erro:
        log.error("Nao consegui gravar o retorno para o Fala, Lavoura! (%s)", erro)
        return 0
    return len(linhas)


def executar(arquivos: list[Path] | None = None, usar_portal: bool = True) -> dict:
    t0 = time.perf_counter()
    proc = psutil.Process()
    proc.cpu_percent(None)
    prioridade.reiniciar_cache_execucao()
    processados = RegistroJSON("processados")  # idempotencia entre execucoes
    pendentes = RegistroJSON("pendentes")      # fila do que o portal nao aceitou
    em_quarentena = RegistroJSON("quarentena")  # hash dos arquivos ja barrados

    resumo = {"inicio": datetime.now().isoformat(timespec="seconds"), "arquivos": [],
              "lidos": 0, "duplicadas_no_lote": 0, "ja_processadas": 0, "reenviadas_corrigidas": 0,
              "rejeitadas": [],
              "revisao_humana": [], "registradas": [], "pendentes": [], "quarentena": []}

    # T1 Ler arquivos
    arquivos = leitura.listar_arquivos(PASTA_ENTRADA) if arquivos is None else arquivos
    brutos = []
    for arq in arquivos:
        try:
            assinatura = leitura.hash_arquivo(arq)
            if assinatura in em_quarentena:
                log.info("T1 %s ja esta na quarentena (mesmo conteudo). Ignorado.", arq.name)
                resumo["arquivos"].append({"arquivo": arq.name, "registros": 0, "status": "ja em quarentena"})
                continue
            registros = leitura.ler_arquivo(arq)
            resumo["arquivos"].append({"arquivo": arq.name, "registros": len(registros),
                                       "sha256": assinatura, "status": "lido"})
            log.info("T1 %s: %d registros", arq.name, len(registros))
            brutos.extend(registros)
        except FileNotFoundError:
            log.error("T1 arquivo nao encontrado: %s (seguindo com os demais)", arq)
            resumo["arquivos"].append({"arquivo": arq.name, "registros": 0, "status": "ausente"})
        except leitura.ArquivoInvalido as erro:
            leitura.mandar_para_quarentena(arq, str(erro))
            em_quarentena.definir(assinatura, {"arquivo": arq.name, "motivo": str(erro)})
            resumo["quarentena"].append({"arquivo": arq.name, "motivo": str(erro)})
            resumo["arquivos"].append({"arquivo": arq.name, "registros": 0, "status": "quarentena"})
    resumo["lidos"] = len(brutos)

    # T2 Tirar duplicadas (dentro do lote e de execucoes anteriores)
    vistos, unicos = set(), []
    for r in brutos:
        rid = str(r.get("id_solicitacao") or "").strip()
        if rid and rid in vistos:
            resumo["duplicadas_no_lote"] += 1
            continue
        anterior = processados.get(rid) if rid else None
        if (anterior and anterior.get("status") == "rejeitada"
                and anterior.get("assinatura") != assinatura_registro(r)):
            # foi rejeitado antes, mas o agricultor reenviou com os dados corrigidos
            log.info("T2 %s foi rejeitada antes e voltou corrigida: sera processada de novo", rid)
            resumo["reenviadas_corrigidas"] += 1
        elif rid and (rid in processados or rid in pendentes):
            resumo["ja_processadas"] += 1
            continue
        vistos.add(rid)
        unicos.append(r)
    if resumo["duplicadas_no_lote"] or resumo["ja_processadas"]:
        log.info("T2 ignoradas: %d duplicadas no lote, %d ja processadas antes",
                 resumo["duplicadas_no_lote"], resumo["ja_processadas"])

    # T3 Validar
    validas = []
    for r in unicos:
        limpo, motivos = validacao.validar(r)
        if motivos:
            rej = {"id_solicitacao": r.get("id_solicitacao") or "(sem id)",
                   "arquivo_origem": r.get("arquivo_origem"), "motivos": "; ".join(motivos)}
            rej["mensagem_agricultor"] = mensagem_agricultor(rej, "rejeitada")
            resumo["rejeitadas"].append(rej)
            if r.get("id_solicitacao"):
                processados.definir(str(r["id_solicitacao"]).strip(), {
                    "status": "rejeitada", "quando": resumo["inicio"],
                    "assinatura": assinatura_registro(r)})  # para reconhecer um reenvio corrigido
            log.warning("T3 rejeitada %s: %s", rej["id_solicitacao"], rej["motivos"])
        else:
            validas.append(limpo)

    # T4 Classificar com ML
    automaticas = []
    if validas:
        clf = modelo.carregar()
        for s, pred in zip(validas, modelo.classificar(clf, [v["descricao"] for v in validas])):
            s.update(pred)
            # emergencia de saude nunca fica so com o robo, mesmo com confianca alta
            saude = prioridade.emergencia_de_saude(s["descricao"], s["motivo_ia"])
            if pred["precisa_revisao"] or saude:
                if saude:
                    s["motivo_revisao"] = "emergência de saúde: um técnico precisa ligar para a família"
                elif pred["categoria"] == modelo.FORA:
                    s["motivo_revisao"] = (f"parece fora da assistência técnica ({pred['confianca']:.0%}): "
                                           "encaminhar ao órgão certo")
                else:
                    s["motivo_revisao"] = f"confiança baixa ({pred['confianca']:.0%}), pode estar fora do escopo"
                # mesmo sem decidir o assunto, o robo avisa o tecnico se o texto fala de risco
                riscos = prioridade.riscos_no_texto(s["descricao"], s["motivo_ia"])
                s["urgente"] = bool(riscos)
                s["emergencia_saude"] = prioridade.emergencia_de_saude(s["descricao"], s["motivo_ia"])
                if s["urgente"]:
                    s["motivo_revisao"] = f"URGENTE ({', '.join(riscos)}). " + s["motivo_revisao"]
                s["mensagem_agricultor"] = mensagem_agricultor(s, "revisao_humana")
                resumo["revisao_humana"].append(s)
                processados.definir(s["id_solicitacao"], {"status": "revisao_humana", "quando": resumo["inicio"]})
                log.info("T4 %s -> REVISAO HUMANA (sugestao %s, %.0f%%)", s["id_solicitacao"],
                         pred["categoria"], pred["confianca"] * 100)
            else:
                automaticas.append(s)

    # T5 Priorizar
    for s in automaticas:
        s.update(prioridade.avaliar(s["categoria"], s["descricao"], s["municipio"],
                                    s["semaforo_ia"], s["motivo_ia"]))
        log.info("T5 %s: %s / %s (%s)", s["id_solicitacao"], s["categoria"], s["prioridade"], s["justificativa"])

    # T6 Registrar no portal (primeiro o que ficou pendente de execucoes anteriores)
    fila = list(pendentes.dados.values()) + automaticas
    if fila:
        if pendentes.dados:
            log.info("T6 %d pendentes de execucoes anteriores serao tentadas de novo", len(pendentes.dados))
        _registrar_no_portal(fila, usar_portal, processados, pendentes, resumo)

    # T7 Mensagem ao agricultor para cada registrado/pendente + retorno ao Fala, Lavoura!
    for s in resumo["registradas"]:
        s["mensagem_agricultor"] = mensagem_agricultor(s, "registrada")
    for s in resumo["pendentes"]:
        s["mensagem_agricultor"] = mensagem_agricultor(s, "pendente")
    resumo["retornos_fala_lavoura"] = retorno_fala_lavoura(resumo)
    if resumo["retornos_fala_lavoura"]:
        log.info("T7 %d fichas do Fala, Lavoura! receberam retorno em %s",
                 resumo["retornos_fala_lavoura"], ARQ_RETORNO_FALA_LAVOURA.name)

    # T8 Focos regionais
    df_ok = pd.DataFrame(resumo["registradas"])
    criticos = modelo.pontos_criticos(df_ok) if not df_ok.empty else pd.DataFrame()

    # T9 Relatorios
    resumo["duracao_s"] = round(time.perf_counter() - t0, 1)
    resumo["memoria_mb"] = round(proc.memory_info().rss / 2**20, 1)
    resumo["cpu_percent_medio"] = proc.cpu_percent(None)
    resumo["pendentes_na_fila"] = len(pendentes.dados)
    caminhos = relatorio.gerar(resumo, criticos)
    resumo["relatorios"] = {k: str(v) for k, v in caminhos.items()}

    log.info("FIM: %d lidos | %d registradas | %d revisao humana | %d rejeitadas | %d pendentes | "
             "%d quarentena | %d ja processadas | %.1fs",
             resumo["lidos"], len(resumo["registradas"]), len(resumo["revisao_humana"]),
             len(resumo["rejeitadas"]), len(resumo["pendentes"]), len(resumo["quarentena"]),
             resumo["ja_processadas"], resumo["duracao_s"])
    return resumo


def _registrar_no_portal(fila, usar_portal, processados, pendentes, resumo):
    def para_pendente(s, motivo):
        s["motivo_pendencia"] = motivo
        pendentes.definir(s["id_solicitacao"], s)
        resumo["pendentes"].append(s)

    if not usar_portal or not portal_no_ar():
        log.error("T6 portal fora do ar: %d solicitacoes vao para a fila de pendentes", len(fila))
        for s in fila:
            para_pendente(s, "portal fora do ar")
        return

    try:
        with RoboPortal() as robo:
            for s in fila:
                try:
                    s["protocolo"] = robo.registrar(s)
                    s["registrado_em"] = datetime.now().isoformat(timespec="seconds")
                    processados.definir(s["id_solicitacao"], {"status": "registrada", "protocolo": s["protocolo"],
                                                              "quando": s["registrado_em"]})
                    pendentes.remover(s["id_solicitacao"])
                    resumo["registradas"].append(s)
                    log.info("T6 %s registrada: protocolo %s", s["id_solicitacao"], s["protocolo"])
                except Exception as erro:  # uma solicitacao com problema nao derruba as outras
                    robo.print_tela(f"erro_{s['id_solicitacao']}")
                    para_pendente(s, f"{type(erro).__name__}: {erro}"[:200])
    except (CredenciaisInvalidas, PortalIndisponivel) as erro:
        log.error("T6 nao foi possivel usar o portal (%s). Tudo vai para pendentes.", erro)
        ja = {s["id_solicitacao"] for s in resumo["registradas"] + resumo["pendentes"]}
        for s in fila:
            if s["id_solicitacao"] not in ja:
                para_pendente(s, type(erro).__name__)

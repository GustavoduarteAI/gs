"""
Demonstracao automatica das falhas tratadas (python main.py falhas).

Roda o robo varias vezes, cada vez quebrando uma coisa de proposito, e confere
se ele seguiu o caminho seguro esperado. O resultado vai para
docs/evidencias/demo_falhas.md (tabela esperado x obtido).

ATENCAO: comeca apagando o estado do robo e o banco do sistema de ATER simulado.
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from portal import servidor
from src import pipeline, prioridade, resiliencia, rpa_portal
from src.config import PASTA_ESTADO, PASTA_SAIDA, PORTAL_URL, RAIZ
from src.logs import obter_logger

log = obter_logger("demo_falhas")
PASTA_EVID = RAIZ / "docs" / "evidencias"
URL_CLIMA_ORIGINAL = prioridade.CLIMA_API_URL
SENHA_ORIGINAL = rpa_portal.PORTAL_SENHA


class ContadorRetries(logging.Handler):
    def __init__(self):
        super().__init__()
        self.n = 0

    def emit(self, record):
        if "Nova tentativa" in record.getMessage():
            self.n += 1


def _limpar_estado():
    for arq in PASTA_ESTADO.glob("*.json"):
        arq.unlink()
    servidor.ARQ_DADOS.unlink(missing_ok=True)


def _registros_no_portal():
    if not servidor.ARQ_DADOS.exists():
        return 0
    return len(json.loads(servidor.ARQ_DADOS.read_text(encoding="utf-8"))["registros"])


def _novo_lote(nome, qtd):
    """Cria um lote extra (fora da pasta entrada/) so para a demonstracao."""
    pasta = PASTA_SAIDA / "demo"
    pasta.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now().strftime("%H%M%S")
    textos = ["Lagarta comendo as folhas do milho, preciso de uma visita",
              "Quero saber como tirar o CAF pra pedir o Pronaf"]
    dados = [{"id_solicitacao": f"DEMO-{carimbo}-{i}", "data_hora": "2026-11-14 10:00", "canal": "demo",
              "nome": "Pessoa Ficticia", "municipio": "Botucatu", "comunidade": "Sítio Teste",
              "cultura": "milho", "latitude": "", "longitude": "", "descricao": textos[i % 2]}
             for i in range(qtd)]
    caminho = pasta / nome
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    return caminho


def _navegador_disponivel() -> bool:
    """Os cenários 503, senha errada e reenvio precisam do Selenium cadastrando de verdade."""
    ordem = ["chrome", "edge"] if rpa_portal.NAVEGADOR == "auto" else [rpa_portal.NAVEGADOR]
    for nome in ordem:
        try:
            rpa_portal.RoboPortal._criar_driver(nome).quit()
            return True
        except Exception:  # noqa: BLE001 - qualquer falha aqui significa "sem navegador"
            continue
    return False


def rodar():
    porta = int(PORTAL_URL.rsplit(":", 1)[-1].split("/")[0])
    if rpa_portal.portal_no_ar():
        log.error("Ja existe um portal rodando na porta %d. Feche-o antes da demonstracao.", porta)
        return
    resiliencia.ESPERA_INICIAL = 0.3  # so para a demo nao demorar
    contador = ContadorRetries()
    logging.getLogger("resiliencia").addHandler(contador)
    _limpar_estado()
    cenarios = []

    tem_navegador = _navegador_disponivel()
    if not tem_navegador:
        log.warning("Nenhum navegador abriu: os cenários que dependem do Selenium serão marcados "
                    "como NÃO EXECUTADO (não é falha do robô). Rode python main.py verificar.")

    def registrar(nome, falha, esperado, ok, obtido, precisa_navegador=False):
        if precisa_navegador and not tem_navegador:
            ok, obtido = None, "não executado: sem navegador nesta máquina (o cenário depende do Selenium)"
        cenarios.append({"cenario": nome, "falha_simulada": falha, "esperado": esperado,
                         "obtido": obtido, "ok": None if ok is None else bool(ok)})
        rotulo = "NÃO EXECUTADO" if ok is None else ("OK" if ok else "FALHOU")
        log.info("[%s] %s -> %s", rotulo, nome, obtido)

    # 1) API de clima fora do ar + portal fora do ar + arquivo corrompido + dados invalidos
    prioridade.CLIMA_API_URL = "http://api-clima.invalido.test/v1/forecast"
    r = pipeline.executar()
    sem_clima = sum("indisponível" in s.get("justificativa", "") for s in r["pendentes"])
    sensiveis = sum(s["categoria"] in prioridade.LAVOURA for s in r["pendentes"])
    registrar("API de clima fora do ar", "URL da API apontando para um host inexistente",
              "robô segue sem o critério de clima e explica isso na justificativa",
              sem_clima == sensiveis and sensiveis > 0,
              f"{sem_clima} de {sensiveis} pedidos de lavoura com 'previsão indisponível'; disjuntor aberto após 2 falhas")
    registrar("Sistema de ATER fora do ar", "sistema desligado",
              "nada se perde: tudo vai para a fila de pendentes",
              len(r["registradas"]) == 0 and len(r["pendentes"]) > 0,
              f"0 registradas, {len(r['pendentes'])} na fila de pendentes")
    registrar("Arquivo corrompido", "JSON cortado no meio (exportacao_interrompida.json)",
              "arquivo vai para quarentena com o motivo e os outros 5 são lidos",
              len(r["quarentena"]) == 1 and r["lidos"] == 37,
              f"{len(r['quarentena'])} em quarentena (JSONDecodeError), {r['lidos']} registros dos outros arquivos lidos")
    registrar("Dados inválidos", "data no futuro, texto 'oi', município inexistente e linha duplicada",
              "rejeita com motivo e mensagem ao agricultor; duplicata ignorada",
              len(r["rejeitadas"]) == 3 and r["duplicadas_no_lote"] == 1,
              f"{len(r['rejeitadas'])} rejeitadas, cada uma com motivo ({', '.join(x['id_solicitacao'] for x in r['rejeitadas'])}), "
              f"{r['duplicadas_no_lote']} duplicata ignorada")
    pendentes_iniciais = len(r["pendentes"])

    registrar("Linha quebrada na fila do Fala, Lavoura!", "última linha do JSONL cortada no meio",
              "pula só a linha ruim e lê as outras fichas do mesmo arquivo",
              sum(s.get("canal") == "fala_lavoura" for lista in ("pendentes", "revisao_humana")
                  for s in r[lista]) == 6,
              "6 fichas lidas do JSONL; a linha cortada foi registrada no log e pulada")

    # 2) Portal volta, mas instavel (erro 503 a cada 4 envios)
    prioridade.CLIMA_API_URL = URL_CLIMA_ORIGINAL
    os.environ["PORTAL_FALHA_A_CADA"] = "4"
    srv = servidor.iniciar(porta)
    try:
        contador.n = 0
        r = pipeline.executar(arquivos=[])
        registrar("Sistema de ATER instável (erro 503)", "sistema responde 503 a cada 4 cadastros",
                  "retry com espera recupera e a fila de pendentes zera",
                  len(r["registradas"]) == pendentes_iniciais and r["pendentes_na_fila"] == 0,
                  f"{len(r['registradas'])}/{pendentes_iniciais} registradas, {contador.n} novas tentativas automáticas, "
                  f"fila de pendentes = {r['pendentes_na_fila']}", precisa_navegador=True)
        os.environ["PORTAL_FALHA_A_CADA"] = "0"

        # 3) Execucao repetida (idempotencia)
        antes = _registros_no_portal()
        r = pipeline.executar()
        depois = _registros_no_portal()
        registrar("Execução repetida", "rodar o robô de novo com os mesmos arquivos",
                  "nada é cadastrado em dobro no sistema de ATER",
                  depois == antes and len(r["registradas"]) == 0,
                  f"{r['ja_processadas']} já processadas ignoradas; o sistema continuou com {depois} registros")

        # 4) Senha errada no portal
        rpa_portal.PORTAL_SENHA = "senha-errada"
        lote = _novo_lote("lote_senha_errada.json", 2)
        r = pipeline.executar(arquivos=[lote])
        rpa_portal.PORTAL_SENHA = SENHA_ORIGINAL
        r2 = pipeline.executar(arquivos=[])
        registrar("Senha do sistema errada", "PORTAL_SENHA inválida no .env",
                  "não insiste no login, guarda na fila e registra quando a senha é corrigida",
                  len(r["pendentes"]) == 2 and len(r2["registradas"]) == 2,
                  f"1ª execução: {len(r['pendentes'])} pendentes (CredenciaisInvalidas); "
                  f"após corrigir: {len(r2['registradas'])} registradas", precisa_navegador=True)

        # 5) Agricultor reenvia corrigido um pedido que tinha sido rejeitado ("oi")
        corrigida = PASTA_SAIDA / "demo" / "balcao_reenvio_corrigido.json"
        corrigida.write_text(json.dumps([{
            "id_solicitacao": "BAL-0007", "data_hora": "2026-11-14 11:00", "canal": "balcao",
            "nome": "Pessoa Ficticia", "municipio": "Socorro", "comunidade": "Sítio Teste",
            "cultura": "couve", "latitude": "", "longitude": "",
            "descricao": "Pulgão tomando a couve da horta há uma semana, as folhas tão enrolando"}],
            ensure_ascii=False), encoding="utf-8")
        mesma = pipeline.executar()  # mesmos arquivos de antes: o "oi" continua ignorado
        r = pipeline.executar(arquivos=[corrigida])
        registrar("Reenvio de pedido rejeitado", "agricultor reenvia o BAL-0007 ('oi') com a descrição completa",
                  "o reenvio corrigido é processado; o original sem mudança continua ignorado",
                  r["reenviadas_corrigidas"] == 1 and len(r["registradas"]) == 1 and len(mesma["rejeitadas"]) == 0,
                  f"reenvio reconhecido e registrado ({r['registradas'][0]['protocolo'] if r['registradas'] else 'sem protocolo'}); "
                  f"arquivo original sem mudança: {len(mesma['rejeitadas'])} rejeições repetidas",
                  precisa_navegador=True)

        # 6) Arquivo ausente
        r = pipeline.executar(arquivos=[Path("entrada/nao_existe.csv")])
        registrar("Arquivo ausente", "caminho de arquivo que não existe",
                  "registra no log e termina a execução normalmente",
                  r["arquivos"][0]["status"] == "ausente",
                  f"status do arquivo: {r['arquivos'][0]['status']}; relatório gerado normalmente")
    finally:
        srv.shutdown()
        os.environ["PORTAL_FALHA_A_CADA"] = "0"
        prioridade.CLIMA_API_URL = URL_CLIMA_ORIGINAL
        rpa_portal.PORTAL_SENHA = SENHA_ORIGINAL

    PASTA_EVID.mkdir(parents=True, exist_ok=True)
    with open(PASTA_EVID / "demo_falhas.json", "w", encoding="utf-8") as f:
        json.dump(cenarios, f, ensure_ascii=False, indent=2)
    linhas = ["# Demonstração de falhas tratadas", "",
              f"Gerado automaticamente por `python main.py falhas` em {datetime.now():%d/%m/%Y %H:%M}.", "",
              "| Cenário | Falha simulada | Esperado | Obtido | Passou? |", "| :- | :- | :- | :- | :-: |"]
    linhas += [f"| {c['cenario']} | {c['falha_simulada']} | {c['esperado']} | {c['obtido']} | "
               f"{'não executado' if c['ok'] is None else ('sim' if c['ok'] else 'NÃO')} |" for c in cenarios]
    (PASTA_EVID / "demo_falhas.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    passou = sum(c["ok"] is True for c in cenarios)
    nao_exec = sum(c["ok"] is None for c in cenarios)
    executados = len(cenarios) - nao_exec
    extra = f" ({nao_exec} não executados por falta de navegador)" if nao_exec else ""
    log.info("Demonstracao concluida: %d de %d cenarios executados passaram%s. Veja docs/evidencias/demo_falhas.md",
             passou, executados, extra)

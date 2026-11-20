"""Testes rapidos das partes que mais podem quebrar. Rodar com: python -m pytest"""
import json

import pytest

from src import leitura, modelo, pipeline, prioridade, resiliencia, validacao


def registro_ok(**mudancas):
    base = {"id_solicitacao": "T-1", "data_hora": "2026-11-14 10:00", "canal": "whatsapp_cooperativa",
            "nome": "Fulano Teste", "municipio": "Botucatu", "comunidade": "Sítio A", "cultura": "milho",
            "latitude": "-22.88", "longitude": "-48.44",
            "descricao": "Lagarta no milho, me liga no (14) 91234-5678 ou fulano@email.com"}
    base.update(mudancas)
    return base


# Validacao e LGPD
def test_mascara_telefone_e_email_e_tira_o_nome():
    limpo, motivos = validacao.validar(registro_ok())
    assert motivos == []
    assert "[TELEFONE]" in limpo["descricao"] and "[EMAIL]" in limpo["descricao"]
    assert "91234" not in limpo["descricao"]
    assert "nome" not in limpo and limpo["agricultor"].startswith("agr_")


def test_mascara_cpf():
    texto, achados = validacao.mascarar_dados_pessoais("meu cpf 123.456.789-09")
    assert texto == "meu cpf [CPF]" and achados == ["cpf"]


@pytest.mark.parametrize("mudanca, motivo", [
    ({"descricao": "oi"}, "curta"),
    ({"data_hora": "2031-01-01 10:00"}, "futuro"),
    ({"data_hora": "ontem"}, "data inválida"),
    ({"municipio": "Atlantida", "latitude": "abc", "longitude": ""}, "localização"),
    ({"municipio": "Atlantida", "latitude": "-3.10", "longitude": "-60.02"}, "localização"),  # fora de SP
    ({"id_solicitacao": ""}, "identificador"),
])
def test_rejeita_dados_invalidos(mudanca, motivo):
    limpo, motivos = validacao.validar(registro_ok(**mudanca))
    assert limpo is None
    assert any(motivo in m for m in motivos)


def test_municipio_valido_sem_coordenada_usa_centro_do_municipio():
    limpo, _ = validacao.validar(registro_ok(latitude="", longitude=""))
    assert (limpo["latitude"], limpo["longitude"]) == (-22.8858, -48.445)


@pytest.mark.parametrize("texto", ["Campinas, SP", "Campinas (São Paulo)", "CAMPINAS-SP", " campinas "])
def test_reconhece_municipio_em_varios_formatos(texto):
    assert validacao.chave_municipio(texto) == "campinas"


def test_aceita_data_no_formato_do_fala_lavoura():
    limpo, motivos = validacao.validar(registro_ok(data_hora="14/11/2026 15:04"))
    assert motivos == [] and limpo["data_hora"] == "2026-11-14 15:04"


# Leitura de arquivos
def test_le_csv_cp1252_com_ponto_e_virgula(tmp_path):
    arq = tmp_path / "balcao.csv"
    arq.write_text("id_solicitacao;descricao\nX-1;Feijão amarelando, não sei o que é\n", encoding="cp1252")
    regs = leitura.ler_arquivo(arq)
    assert regs[0]["descricao"] == "Feijão amarelando, não sei o que é"


def test_json_corrompido_vira_arquivo_invalido(tmp_path):
    arq = tmp_path / "quebrado.json"
    arq.write_text('[{"id_solicitacao": "A', encoding="utf-8")
    with pytest.raises(leitura.ArquivoInvalido):
        leitura.ler_arquivo(arq)


def test_arquivo_ausente(tmp_path):
    with pytest.raises(FileNotFoundError):
        leitura.ler_arquivo(tmp_path / "nao_existe.csv")


def test_le_fila_do_fala_lavoura_e_pula_linha_quebrada(tmp_path):
    arq = tmp_path / "fila.jsonl"
    ficha = {"id": "abc123", "quando": "14/11/2026 15:06", "semaforo": "vermelho", "municipio": "Campinas, SP",
             "cultura": "Milho", "pergunta": "Minha esposa está tonta depois de passar veneno",
             "o_que_a_foto_mostra": "", "motivo_do_encaminhamento": "Emergência: possível intoxicação"}
    arq.write_text(json.dumps(ficha, ensure_ascii=False) + "\n" + '{"id": "cortad', encoding="utf-8")
    regs = leitura.ler_arquivo(arq)
    assert len(regs) == 1
    r = regs[0]
    assert r["id_solicitacao"] == "FL-abc123" and r["canal"] == "fala_lavoura"
    assert r["semaforo_ia"] == "vermelho" and "Emergência" in r["motivo_ia"]


# PLN: Dicionario da Roca
def test_dicionario_traduz_jeito_falado():
    assert "pronaf" in modelo.expandir("Preciso do dinheiro do banco pra plantar")
    assert "lagarta" in modelo.expandir("Tem bicho comendo a folha do milho")


# Resiliencia
def test_retry_recupera_depois_de_falhas():
    chamadas = {"n": 0}

    @resiliencia.com_retry(tentativas=3, espera_inicial=0, excecoes=(ConnectionError,))
    def instavel():
        chamadas["n"] += 1
        if chamadas["n"] < 3:
            raise ConnectionError("caiu")
        return "ok"

    assert instavel() == "ok" and chamadas["n"] == 3


def test_retry_desiste_e_relanca():
    @resiliencia.com_retry(tentativas=2, espera_inicial=0, excecoes=(ConnectionError,))
    def sempre_falha():
        raise ConnectionError("fora do ar")

    with pytest.raises(ConnectionError):
        sempre_falha()


# Prioridade (credito nao consulta a API de clima, entao esses testes rodam offline)
def test_crianca_exposta_vira_alta():
    r = prioridade.avaliar("credito", "Quero o Pronaf pra cercar a horta onde a criança brinca", "Campinas")
    assert r["prioridade"] == "ALTA" and r["urgente"]


def test_sem_risco_credito_e_baixa():
    r = prioridade.avaliar("credito", "Como faço o CAF?", "Campinas")
    assert r["prioridade"] == "BAIXA" and r["prazo_dias"] == 15


def test_prazo_correndo_sobe_credito():
    r = prioridade.avaliar("credito", "A chamada pública da merenda fecha amanhã", "Campinas")
    assert r["prioridade"] == "MÉDIA" and "prazo" in r["justificativa"]


def test_semaforo_vermelho_do_fala_lavoura_pesa_na_prioridade():
    r = prioridade.avaliar("credito", "Como faço o CAF?", "Campinas", semaforo_ia="vermelho")
    assert r["prioridade"] == "MÉDIA" and "Fala, Lavoura!" in r["justificativa"]


def test_intoxicacao_e_emergencia_de_saude():
    assert prioridade.emergencia_de_saude("meu marido ficou tonto e vomitando depois de passar veneno")
    assert prioridade.emergencia_de_saude("pergunta qualquer", "Emergência: possível intoxicação por agrotóxico")
    assert not prioridade.emergencia_de_saude("lagarta comendo o milho")


def _clima(monkeypatch, chuva, tmax, tmin):
    monkeypatch.setattr(prioridade, "previsao", lambda m: {"chuva_3d_mm": chuva, "tmax_c": tmax, "tmin_c": tmin})


def test_geada_prevista_sobe_prioridade(monkeypatch):
    _clima(monkeypatch, 0.0, 18.0, 1.5)
    r = prioridade.avaliar("pragas", "Pulgão na couve", "Itapeva")
    assert r["prioridade"] == "ALTA" and "geada" in r["justificativa"]


def test_calor_sem_chuva_sobe_pedido_de_agua(monkeypatch):
    _clima(monkeypatch, 0.4, 34.0, 20.0)
    r = prioridade.avaliar("agua", "O gotejo entupiu", "Mirante do Paranapanema")
    assert r["prioridade"] == "ALTA" and "calor sem chuva" in r["justificativa"]


def test_chuva_sobe_pedido_de_doenca(monkeypatch):
    _clima(monkeypatch, 42.0, 26.0, 18.0)
    r = prioridade.avaliar("doencas", "Mancha escura na folha do tomate", "Registro")
    assert r["prioridade"] == "ALTA" and "fungo" in r["justificativa"]


def test_api_de_clima_fora_usa_caminho_seguro(monkeypatch):
    def api_caiu(*a, **k):
        raise prioridade.requests.ConnectionError("fora do ar")
    monkeypatch.setattr(prioridade, "_consultar_api", api_caiu)
    monkeypatch.setattr(prioridade, "_cache_disco", resiliencia.RegistroJSON("cache_clima_teste"))
    prioridade.reiniciar_cache_execucao()
    r = prioridade.avaliar("doencas", "Ferrugem no feijão", "Socorro")
    assert r["chuva_3d_mm"] is None and "indisponível" in r["justificativa"]
    prioridade._cache_disco.caminho.unlink(missing_ok=True)


def test_estado_salva_mesmo_com_arquivo_travado(monkeypatch):
    # simula o OneDrive travando o arquivo nas 2 primeiras tentativas de troca
    from pathlib import Path
    original = Path.replace
    falhas = {"n": 0}

    def replace_travado(self, alvo):
        if falhas["n"] < 2:
            falhas["n"] += 1
            raise PermissionError("arquivo em uso")
        return original(self, alvo)

    monkeypatch.setattr(Path, "replace", replace_travado)
    reg = resiliencia.RegistroJSON("teste_travado")
    reg.definir("X-1", {"status": "ok"})
    monkeypatch.setattr(Path, "replace", original)
    assert falhas["n"] == 2
    assert resiliencia.RegistroJSON("teste_travado").get("X-1") == {"status": "ok"}
    reg.caminho.unlink()


def test_reenvio_corrigido_tem_assinatura_diferente():
    original = registro_ok(descricao="oi")
    corrigido = registro_ok(descricao="Pulgão tomando a couve da horta há uma semana")
    assert pipeline.assinatura_registro(original) == pipeline.assinatura_registro(dict(original))
    assert pipeline.assinatura_registro(original) != pipeline.assinatura_registro(corrigido)


def test_mensagem_de_emergencia_traz_telefones():
    s = {"id_solicitacao": "FL-1", "emergencia_saude": True}
    msg = pipeline.mensagem_agricultor(s, "revisao_humana")
    assert "192" in msg and "0800 722 6001" in msg


def test_retorno_ao_fala_lavoura_so_leva_fichas_de_la(tmp_path, monkeypatch):
    destino = tmp_path / "retorno.jsonl"
    monkeypatch.setattr(pipeline, "ARQ_RETORNO_FALA_LAVOURA", destino)
    resumo = {"registradas": [{"id_solicitacao": "FL-abc", "protocolo": "ATER-2026-000001", "prioridade": "ALTA"},
                              {"id_solicitacao": "COOP-0001", "protocolo": "ATER-2026-000002"}],
              "revisao_humana": [], "pendentes": [], "rejeitadas": []}
    assert pipeline.retorno_fala_lavoura(resumo) == 1
    linha = json.loads(destino.read_text(encoding="utf-8"))
    assert linha["id_ficha"] == "abc" and linha["protocolo"] == "ATER-2026-000001"

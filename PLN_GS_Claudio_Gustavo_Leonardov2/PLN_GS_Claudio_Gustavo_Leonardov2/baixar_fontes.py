# -*- coding: utf-8 -*-
"""
Baixa as fontes oficiais usadas na Fabrica de Corpus CitizenTech.
Todas sao publicas e de orgaos oficiais (federais, estaduais e municipais).
Rodar:  python baixar_fontes.py
"""
import json
import os
import sys
import time
import urllib.request

DESTINO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fontes")

# nome local -> (url, orgao, formato)
FONTES = {
    "protocolo_eventos_extremos_MMA.pdf": (
        "https://www.gov.br/mma/pt-br/centrais-de-conteudo/publicacoes/educacao-ambiental/protocolo-inundacoes.pdf",
        "Ministerio do Meio Ambiente e Mudanca do Clima (MMA)", "PDF"),
    "cartilha_prepare_defesacivil_rio.pdf": (
        "https://defesacivil.prefeitura.rio/wp-content/uploads/sites/35/2025/04/PREPARE_Defesa-Civil-2025_final.pdf",
        "Defesa Civil da Cidade do Rio de Janeiro", "PDF"),
    "modelo_plano_contingencia_defesacivil_PR.docx": (
        "https://www.defesacivil.pr.gov.br/sites/defesa-civil/arquivos_restritos/files/documento/2022-02/plan%20con%20barragem%20-%20modelo%20final.docx",
        "Coordenadoria Estadual de Protecao e Defesa Civil do Parana", "DOCX"),
    "lei_12608_2012_pnpdec.html": (
        "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2012/lei/l12608.htm",
        "Presidencia da Republica / Casa Civil (Planalto)", "HTML"),
    # Documento adicional, ingerido de proposito para testar o portao de qualidade
    "orientacoes_plano_contingencia_SEDEC.pdf": (
        "https://www.gov.br/mdr/pt-br/centrais-de-conteudo/publicacoes/protecao-e-defesa-civil-sedec/orientacoes_planos_contingencia.pdf",
        "Secretaria Nacional de Protecao e Defesa Civil (SEDEC)", "PDF"),
}

API_INMET = "https://apiprevmet3.inmet.gov.br/avisos/ativos"
ARQ_INMET = "avisos_oficiais_inmet.txt"


def baixar(url, tentativas=6, espera=4, timeout=60):
    """O portal do Planalto costuma derrubar a primeira conexao, entao insistimos."""
    ultimo = None
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "*/*",
            })
            return urllib.request.urlopen(req, timeout=timeout).read()
        except Exception as e:  # noqa: BLE001
            ultimo = e
            print(f"    tentativa {i + 1}/{tentativas} falhou ({type(e).__name__})")
            time.sleep(espera)
    raise RuntimeError(f"nao foi possivel baixar {url}: {ultimo}")


def montar_txt_inmet(bruto):
    """
    Transforma o boletim oficial do INMET em um .txt de texto corrido.
    Mantemos apenas o que o cidadao le no aviso: o que e, qual o risco e o que fazer.
    """
    dados = json.loads(bruto)
    avisos = list(dados.get("hoje", [])) + list(dados.get("futuro", []))
    linhas = [
        "AVISOS METEOROLOGICOS OFICIAIS",
        "Instituto Nacional de Meteorologia (INMET) - Ministerio da Agricultura e Pecuaria",
        f"Snapshot coletado em {time.strftime('%d/%m/%Y')} a partir de {API_INMET}",
        "",
    ]
    for a in avisos:
        linhas.append(f"AVISO: {a.get('descricao', '')} - Severidade: {a.get('severidade', '')}")
        linhas.append(f"Vigencia: de {a.get('inicio', '')} ate {a.get('fim', '')}")
        est = str(a.get("estados", "") or "").strip()
        if est:
            linhas.append(f"Estados sob aviso: {est}")
        for r in a.get("riscos", []) or []:
            linhas.append(f"Riscos previstos: {str(r).strip()}")
        for ins in a.get("instrucoes", []) or []:
            linhas.append(f"Orientacao a populacao: {str(ins).strip()}")
        linhas.append("")
    return "\n".join(linhas)


def main():
    os.makedirs(DESTINO, exist_ok=True)
    print(f"Salvando em {DESTINO}\n")
    manifesto = []

    for nome, (url, orgao, fmt) in FONTES.items():
        caminho = os.path.join(DESTINO, nome)
        print(f"[{fmt}] {nome}")
        conteudo = baixar(url)
        with open(caminho, "wb") as f:
            f.write(conteudo)
        print(f"    ok  {len(conteudo) / 1024:.0f} KB")
        manifesto.append({"arquivo": nome, "formato": fmt, "orgao": orgao, "url": url})

    print(f"[TXT] {ARQ_INMET}")
    texto = montar_txt_inmet(baixar(API_INMET))
    with open(os.path.join(DESTINO, ARQ_INMET), "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"    ok  {len(texto) / 1024:.0f} KB")
    manifesto.append({"arquivo": ARQ_INMET, "formato": "TXT",
                      "orgao": "Instituto Nacional de Meteorologia (INMET)", "url": API_INMET})

    with open(os.path.join(DESTINO, "FONTES.json"), "w", encoding="utf-8") as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=2)
    print(f"\n{len(manifesto)} fontes baixadas. Manifesto em fontes/FONTES.json")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()

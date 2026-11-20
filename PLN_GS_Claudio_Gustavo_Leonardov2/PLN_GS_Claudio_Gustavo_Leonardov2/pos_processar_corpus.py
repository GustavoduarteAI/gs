"""Pós-processamento dos corpus (feito depois da gravação do vídeo).

Não reexecuta o pipeline: as fronteiras dos trechos e as contagens 141 / 116 / 67
ficam exatamente iguais. Só faz três correções de superfície:

1. remove o resíduo da exportação do InDesign da cartilha do Pronaf
   (carimbo de data e hora "21/10/2024 13:37:36", marcador de página "[ 09 ]"
   e o cabeçalho corrente "Como acessar Crédito Rural pelo Pronaf?" quando
   colado a esses marcadores);
2. acentua o texto escrito pelo grupo (prompt de sistema, perguntas-modelo,
   molduras das respostas, diálogos de limite e o recado colado), que tinha sido
   digitado sem acento;
3. aplica as correções de conteúdo de correcoes_corpus.py: devolve o texto original
   nos 25 falsos positivos de [NOME], reescreve 5 perguntas de QA, reescreve 15
   diálogos documentais em tom de atendente e troca as continuações genéricas pela
   pergunta que o trecho responde; remove o cabeçalho duplicado do Planalto;
4. mantém estatisticas.json como foi apresentado (as contagens não mudam; a média
   de tokens muda um pouco).

Os arquivos como estavam na apresentação ficam em versao_apresentada/.

Uso:  python pos_processar_corpus.py   (depois de executar o notebook)
"""
import json
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
from correcoes_corpus import corrigir  # noqa: E402  (25 [NOME], 5 QA, 15 diálogos, continuações)
CORPUS = RAIZ / "corpus"
ORIGINAL = RAIZ / "versao_apresentada" / "corpus"
ARQUIVOS = ["corpus_texto.jsonl", "corpus_qa.jsonl", "corpus_chat.jsonl"]

# ----------------------------------------------------------------- 1. resíduos
CABECALHO = r"Como acessar Crédito Rural pelo Pronaf\?"
MARCA = r"\[ ?\d{1,2} ?\]"
HORA = r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}"
RE_CAB_ANTES = re.compile(rf"{MARCA}\s*{CABECALHO}")          # [ 09 ] Como acessar...?
RE_CAB_DEPOIS = re.compile(rf"{CABECALHO}\s*(?={MARCA}|{HORA})")  # Como acessar...? [ 08 ] / hora
RE_HORA = re.compile(HORA)
RE_MARCA = re.compile(MARCA)
RE_DUPLA = re.compile(r"PRONAF\?PRONAF\?")


def limpar_residuos(t: str) -> str:
    t = RE_CAB_ANTES.sub(" ", t)
    t = RE_CAB_DEPOIS.sub(" ", t)
    t = RE_HORA.sub(" ", t)
    t = RE_MARCA.sub(" ", t)
    t = RE_DUPLA.sub("PRONAF?", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r" +([.,;:!?])", r"\1", t)
    return t.strip()


# ----------------------------------------------------------------- 2. acentos
# Palavras sem ambiguidade: a forma sem acento não existe em português.
PALAVRAS = {
    "voce": "você", "nao": "não", "orientacao": "orientação", "portugues": "português",
    "tecnico": "técnico", "tecnica": "técnica", "informacao": "informação",
    "assistencia": "assistência", "faca": "faça", "credito": "crédito",
    "orientacoes": "orientações", "meteorologico": "meteorológico", "politicas": "políticas",
    "pratica": "prática", "excecao": "exceção", "municipio": "município", "tambem": "também",
    "pedaco": "pedaço", "fuba": "fubá", "feijao": "feijão", "manha": "manhã", "serio": "sério",
    "estao": "estão", "adesao": "adesão", "atencao": "atenção", "numero": "número",
    "area": "área", "juridica": "jurídica", "publico": "público",
    "mao": "mão", "agrotoxico": "agrotóxico", "rapido": "rápido", "consequencias": "consequências",
    "serias": "sérias", "Amarelao": "Amarelão", "Peca": "Peça", "Agricola": "Agrícola",
    "Climatico": "Climático", "calendario": "calendário", "alguem": "alguém", "faco": "faço",
    "Protecao": "Proteção", "algodao": "algodão", "beneficiario": "beneficiário",
    "maximo": "máximo", "Duvidas": "Dúvidas", "numeros": "números", "graca": "graça",
    "agronomico": "agronômico", "agronomo": "agrônomo", "receituario": "receituário",
    "residuo": "resíduo", "resistencia": "resistência", "beneficio": "benefício",
    "orgao": "órgão", "entao": "então", "situacao": "situação", "calculo": "cálculo",
    "possivel": "possível", "devolucao": "devolução", "condicoes": "condições",
    "instituicoes": "instituições", "sao": "são", "divida": "dívida", "verificacao": "verificação",
    "inscricao": "inscrição", "duvida": "dúvida", "propria": "própria", "intoxicacao": "intoxicação",
    "descricao": "descrição", "amarelao": "amarelão", "doenca": "doença", "compactacao": "compactação",
    "peca": "peça", "previsao": "previsão", "agricola": "agrícola", "producao": "produção",
    "protecao": "proteção", "confiavel": "confiável", "periodo": "período", "publicas": "públicas",
    "remedio": "remédio", "Voce": "Você", "Nao": "Não", "Calculo": "Cálculo", "Previsao": "Previsão",
    "Serio": "Sério", "ATENCAO": "ATENÇÃO", "ADESAO": "ADESÃO", "Intoxicacao": "Intoxicação",
    "enquadramento": "enquadramento", "safra": "safra", "aposentadoria": "aposentadoria",
    "mae": "mãe", "irmao": "irmão", "tres": "três", "ultima": "última", "ultimo": "último",
    "endereco": "endereço", "familia": "família", "familias": "famílias", "agua": "água",
    "seguranca": "segurança", "proxima": "próxima", "proximo": "próximo", "inicio": "início",
    "pais": "país", "regiao": "região", "condicao": "condição", "concessao": "concessão",
    "relacao": "relação", "obrigatorio": "obrigatório", "necessario": "necessário",
}
# Formas ambíguas (e/é, esta/está, da/dá, so/só, ja/já, as/às, pra): só em
# expressões conferidas uma a uma no texto do grupo.
EXPRESSOES = [
    ("o risco e seu", "o risco é seu"), ("Quem faz e o INSS", "Quem faz é o INSS"),
    ("pelo INSS", "pelo INSS"), ("o que nao entra", "o que não entra"),
    ("fui treinado so para", "fui treinado só para"), ("acesso as politicas", "acesso às políticas"),
    ("acesso as políticas", "acesso às políticas"),
    ("nao e para te deixar", "não é para te deixar"), ("a lavoura e perigoso", "a lavoura é perigoso"),
    ("que so um", "que só um"), ("beneficio e definido", "benefício é definido"),
    ("e e melhor", "e é melhor"), ("Isso ja e questao", "Isso já é questão"),
    ("Nao e bem", "Não é bem"), ("o que e preciso", "o que é preciso"),
    ("errado da residuo", "errado dá resíduo"), ("nao e o meu papel", "não é o meu papel"),
    ("posso dizer e que", "posso dizer é que"), ("beneficio publico e fraude", "benefício público é fraude"),
    ("outra coisa e desvio", "outra coisa é desvio"), ("finalidade: da vencimento", "finalidade: dá vencimento"),
    ("duvida e sobre", "dúvida é sobre"), ("que e o Disque", "que é o Disque"),
    ("o que e a", "o que é a"), ("que e o que voce", "que é o que você"),
    ("nao e comigo", "não é comigo"), ("meteorologico e o INMET", "meteorológico é o INMET"),
    ("municipio e o Zoneamento", "município é o Zoneamento"), ("Quem faz esse enquadramento e a", "Quem faz esse enquadramento é a"),
    ("Documento guardado e o que", "Documento guardado é o que"), ("orientacoes ja publicadas", "orientações já publicadas"),
    ("que esta dando", "que está dando"), ("Mas e informacao", "Mas é informação"), ("publica, nao e?", "pública, não é?"),
    ("Nao da para", "Não dá para"), ("E praga ou", "É praga ou"), ("Qual e a", "Qual é a"),
    ("O que esta previsto", "O que está previsto"), ("e preciso ter", "é preciso ter"),
    ("aderir e preciso", "aderir é preciso"), ("caso, e o", "caso, é o"),
    ("o que eu faco", "o que eu faço"), ("E o que eu faco", "E o que eu faço"),
    ("Ai o risco", "Aí o risco"), ("pro meu caso", "pro meu caso"),
    ("Pare de conversar comigo e peca socorro", "Pare de conversar comigo e peça socorro"),
    ("Voce e um assistente", "Você é um assistente"), ("adesao e feita", "adesão é feita"),
    ("so e pago", "só é pago"),
    ("Defensoria Publica", "Defensoria Pública"), ("informacao publica", "informação pública"),
    ("a conduta e diferente", "a conduta é diferente"), ("inclusive e condicao", "inclusive é condição"),
    ("visita tecnica a Emater ou a entidade", "visita técnica à Emater ou à entidade"),
]
RE_PALAVRA = re.compile(r"\b(" + "|".join(sorted(map(re.escape, PALAVRAS), key=len, reverse=True)) + r")\b")


def acentuar(t: str) -> str:
    for errado, certo in EXPRESSOES:
        t = t.replace(errado, certo)
    return RE_PALAVRA.sub(lambda m: PALAVRAS[m.group(1)], t)


def eh_do_grupo(r: dict) -> bool:
    return r["fonte"].startswith("redacao") or r["fonte"].startswith("recado")


def moldura(t: str) -> str:
    """Acentua só a moldura escrita pelo grupo ("Na cartilha ... aparece o seguinte:")."""
    if ": " in t[:150]:
        pre, resto = t.split(": ", 1)
        if not re.search(r"[áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]", pre):
            return acentuar(pre) + ": " + resto
    for prefixo in ("De acordo com o recado sobre a adesao ao Garantia-Safra,",):
        if t.startswith(prefixo):
            return acentuar(prefixo) + t[len(prefixo):]
    return t


def processar(r: dict) -> dict:
    grupo = eh_do_grupo(r)
    if "text" in r:
        r["text"] = limpar_residuos(acentuar(r["text"]) if grupo else r["text"])
    if "instruction" in r:
        r["instruction"] = limpar_residuos(acentuar(r["instruction"]))
        out = acentuar(r["output"]) if grupo else moldura(r["output"])
        r["output"] = limpar_residuos(out)
    if "messages" in r:
        for m in r["messages"]:
            c = m["content"]
            if m["role"] in ("system", "user") or grupo:
                c = acentuar(c)
            else:
                c = moldura(c)
            m["content"] = limpar_residuos(c)
    return r


def atualizar_estatisticas() -> None:
    """Recalcula os tokens de estatisticas.json com o tokenizer do modelo alvo, do mesmo jeito
    que o notebook (texto; instrução + resposta; soma das falas). Contagens e duplicatas
    removidas não mudam. Sem a biblioteca `tokenizers` (ou sem internet), mantém o arquivo."""
    try:
        from tokenizers import Tokenizer
        tk = Tokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
    except Exception as erro:  # noqa: BLE001
        print(f"estatisticas.json mantido (tokenizer indisponível: {type(erro).__name__})")
        return
    contar = lambda s: len(tk.encode(s).ids)  # noqa: E731
    medidas = {
        "corpus_texto.jsonl": lambda r: contar(r["text"]),
        "corpus_qa.jsonl": lambda r: contar(r["instruction"] + " " + r["output"]),
        "corpus_chat.jsonl": lambda r: sum(contar(m["content"]) for m in r["messages"]),
    }
    arq = CORPUS / "estatisticas.json"
    stats = json.loads(arq.read_text(encoding="utf-8"))
    for nome, medir in medidas.items():
        n = [medir(json.loads(l)) for l in (CORPUS / nome).read_text(encoding="utf-8").splitlines() if l.strip()]
        stats[nome].update(exemplos=len(n), tokens_media=round(sum(n) / len(n), 1), tokens_min=min(n),
                           tokens_max=max(n), tokens_total=sum(n))
        if nome == "corpus_texto.jsonl":
            stats[nome]["trechos_abaixo_de_256_tokens"] = sum(x < 256 for x in n)
    arq.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("estatisticas.json recalculado com o tokenizer do Qwen2.5-0.5B-Instruct")


def main() -> None:
    ORIGINAL.mkdir(parents=True, exist_ok=True)
    for nome in ARQUIVOS + ["estatisticas.json"]:
        if not (ORIGINAL / nome).exists():  # idempotente: guarda o original só uma vez
            shutil.copy2(CORPUS / nome, ORIGINAL / nome)

    contagem = {"qa": 0, "reescritos": 0, "continuacoes": 0}
    for nome in ARQUIVOS:
        # lê o corpus atual: as correções são idempotentes, então rodar de novo (ou depois
        # de reexecutar o notebook) dá o mesmo resultado
        linhas = (CORPUS / nome).read_text(encoding="utf-8").splitlines()
        saida = [corrigir(processar(json.loads(l)), contagem, linha=n)
                 for n, l in enumerate(linhas, 1) if l.strip()]
        assert not any("[NOME]" in json.dumps(r, ensure_ascii=False) for r in saida), nome
        for r in saida:  # nenhum campo pode ficar vazio
            campos = [r.get("text"), r.get("instruction"), r.get("output")] + [
                m["content"] for m in r.get("messages", [])]
            assert all(c for c in campos if c is not None), r
        assert len(saida) == len(linhas), nome
        (CORPUS / nome).write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in saida) + "\n", encoding="utf-8",
            newline="\n")  # sempre \n, inclusive no Windows
        print(f"{nome}: {len(saida)} exemplos (inalterado)")
    atualizar_estatisticas()
    print(f"correções nesta rodada: {contagem['qa']} perguntas de QA, {contagem['reescritos']} diálogos "
          f"reescritos, {contagem['continuacoes']} continuações (0 = já estava corrigido)")


if __name__ == "__main__":
    main()

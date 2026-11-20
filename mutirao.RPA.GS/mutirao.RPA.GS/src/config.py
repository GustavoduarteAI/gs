"""
Configuracao central do robo.

Tudo que pode mudar entre maquinas (URLs, usuario e senha do portal, limiares)
vem do arquivo .env, que NAO vai para o Git. O .env.example mostra o formato.
"""
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
# sem .env, cria um a partir do modelo para o robo rodar de primeira
if not (RAIZ / ".env").exists() and (RAIZ / ".env.example").exists():
    shutil.copy(RAIZ / ".env.example", RAIZ / ".env")
    print("Arquivo .env criado a partir do .env.example (troque a senha e o sal se quiser).")
load_dotenv(RAIZ / ".env")


def _env(nome, padrao=None):
    valor = os.getenv(nome)
    return valor if valor not in (None, "") else padrao


# Pastas
PASTA_ENTRADA = RAIZ / "entrada"
PASTA_SAIDA = RAIZ / "saida"
PASTA_LOGS = PASTA_SAIDA / "logs"
PASTA_QUARENTENA = PASTA_SAIDA / "quarentena"
PASTA_ESTADO = RAIZ / "estado"
PASTA_MODELOS = RAIZ / "modelos"
ARQ_TREINO = RAIZ / "dados" / "treino" / "solicitacoes_treino.csv"
ARQ_TESTE = RAIZ / "dados" / "teste" / "teste_rotulado.csv"
ARQ_MODELO = PASTA_MODELOS / "classificador.joblib"
# Dicionario da Roca: o mesmo recurso de PLN usado pelo Fala, Lavoura! (GenAI)
ARQ_DICIONARIO = RAIZ / "dados" / "dicionario_da_roca.json"
# Retorno para o Fala, Lavoura!: protocolo e situacao de cada ficha que veio de la
ARQ_RETORNO_FALA_LAVOURA = PASTA_SAIDA / "retorno_fala_lavoura.jsonl"
# opcional: modelo treinado em outra disciplina (pipeline scikit-learn com predict_proba)
MODELO_EXTERNO = _env("MODELO_EXTERNO")

# Sistema de ATER (sistema legado simulado da Casa da Agricultura, acessado via Selenium)
PORTAL_URL = _env("PORTAL_URL", "http://127.0.0.1:8765")
PORTAL_USUARIO = _env("PORTAL_USUARIO")
PORTAL_SENHA = _env("PORTAL_SENHA")
PORTAL_EMBUTIDO = _env("PORTAL_EMBUTIDO", "1") == "1"  # sobe o portal local junto com o robo
NAVEGADOR_VISIVEL = _env("NAVEGADOR_VISIVEL", "0") == "1"
NAVEGADOR = (_env("NAVEGADOR", "auto") or "auto").lower()  # auto | chrome | edge
# opcional: caminho de um chromedriver ja instalado (senao o Selenium Manager baixa sozinho)
CHROMEDRIVER_PATH = _env("CHROMEDRIVER_PATH")

# API publica de previsao do tempo (Open-Meteo, gratuita e sem chave)
CLIMA_API_URL = _env("CLIMA_API_URL", "https://api.open-meteo.com/v1/forecast")
# limites usados na priorizacao (previsao dos proximos 3 dias no centro do municipio)
CHUVA_FUNGO_MM = float(_env("CHUVA_FUNGO_MM", "20"))      # chuva que favorece doenca de fungo
CHUVA_SECA_MM = float(_env("CHUVA_SECA_MM", "5"))         # abaixo disso, sem chuva util
CALOR_SECA_C = float(_env("CALOR_SECA_C", "32"))          # maxima que agrava a falta de agua
GEADA_C = float(_env("GEADA_C", "3"))                     # minima com risco de geada

# Resiliencia
TIMEOUT_SEGUNDOS = float(_env("TIMEOUT_SEGUNDOS", "8"))
MAX_TENTATIVAS = int(_env("MAX_TENTATIVAS", "3"))
ESPERA_INICIAL = float(_env("ESPERA_INICIAL", "1"))

# IA: abaixo desse nivel de confianca o robo NAO decide sozinho
LIMIAR_CONFIANCA = float(_env("LIMIAR_CONFIANCA", "0.40"))

# Leitura de arquivos grandes em pedacos (chunking)
TAMANHO_LOTE = int(_env("TAMANHO_LOTE", "500"))

for pasta in (PASTA_ENTRADA, PASTA_SAIDA, PASTA_LOGS, PASTA_QUARENTENA,
              PASTA_ESTADO, PASTA_MODELOS):
    pasta.mkdir(parents=True, exist_ok=True)

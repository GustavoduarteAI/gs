"""Gera RELATORIO.pdf a partir do RELATORIO.md (Chrome ou Edge em modo headless).

Uso:  pip install markdown  &&  python gerar_relatorio_pdf.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

RAIZ = Path(__file__).resolve().parent
MD, PDF = RAIZ / "RELATORIO.md", RAIZ / "RELATORIO.pdf"
TAMANHO = sys.argv[1] if len(sys.argv) > 1 else "9pt"

CSS = """
@page { size: A4; margin: 13mm 14mm 13mm 14mm;
  @bottom-center { content: "Fábrica de Corpus CitizenTech   |   página " counter(page);
                   font: 8pt Arial, sans-serif; color: #666; } }
body { font-family: Arial, Helvetica, sans-serif; font-size: TAMANHO; line-height: 1.38; color: #1c1c1c; }
h1 { font-size: 19pt; margin: 0 0 2px; color: #2f5d1e; }
h2 { font-size: 12.5pt; margin: 14px 0 4px; color: #2f5d1e; border-bottom: 1px solid #c9d8bf; padding-bottom: 2px; }
h3 { font-size: 10.5pt; margin: 9px 0 3px; }
p { margin: 4px 0 6px; text-align: justify; }
ul { margin: 3px 0 6px; padding-left: 18px; } li { margin: 1px 0; }
table { border-collapse: collapse; width: 100%; margin: 5px 0 8px; font-size: 0.92em; }
th, td { border: 1px solid #c8c8c8; padding: 2.5px 5px; text-align: left; vertical-align: top; }
th { background: #eef3ea; }
code { font-family: Consolas, monospace; font-size: 0.9em; background: #f3f3f3; padding: 0 2px; }
pre { background: #f6f7f4; border: 1px solid #dde3d6; padding: 5px 7px; white-space: pre-wrap;
      word-break: break-word; font-size: 7.4pt; line-height: 1.3; margin: 4px 0 8px; }
pre code { background: none; padding: 0; font-size: inherit; }
blockquote { margin: 5px 0; padding: 2px 10px; border-left: 3px solid #9bb98a; color: #333; }
hr { border: none; border-top: 1px solid #ccc; margin: 8px 0; }
h2, h3 { page-break-after: avoid; } pre, table { page-break-inside: avoid; }
"""


def navegador() -> str:
    for c in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              shutil.which("google-chrome") or "", shutil.which("chromium") or ""):
        if c and Path(c).exists():
            return c
    sys.exit("Chrome ou Edge não encontrado.")


def main() -> None:
    corpo = markdown.markdown(MD.read_text(encoding="utf-8"), extensions=["tables", "fenced_code"])
    html = (f"<!doctype html><html lang='pt-br'><head><meta charset='utf-8'><title>Relatório</title>"
            f"<style>{CSS.replace('TAMANHO', TAMANHO)}</style></head><body>{corpo}</body></html>")
    with tempfile.TemporaryDirectory() as tmp:
        arq = Path(tmp) / "relatorio.html"
        arq.write_text(html, encoding="utf-8")
        saida = Path(tmp) / "relatorio.pdf"
        subprocess.run([navegador(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--user-data-dir={Path(tmp) / 'perfil'}", f"--print-to-pdf={saida}",
                        arq.as_uri()], check=True, capture_output=True, timeout=120)
        shutil.copy2(saida, PDF)
    print("PDF gerado:", PDF)


if __name__ == "__main__":
    main()

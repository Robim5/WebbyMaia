from __future__ import annotations

from scraper.fetch import fetch_html
from scraper.news.parse import parse_noticias_listagem

# url da pagina de noticias
NOTICIAS_URL = "https://www.cm-maia.pt/institucional/atualidade-e-participacao/noticias"

def recolher_noticias_recentes(*, limit: int = 5) -> list[dict]:
    html = fetch_html(NOTICIAS_URL)
    return parse_noticias_listagem(html, limit=limit)
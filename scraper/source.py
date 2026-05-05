from __future__ import annotations
from scraper.fetch import fetch_html
from scraper.parse import extrair_urls_eventos_de_listagem

# urls das paginas de eventos
LISTING_URLS = [
    "https://visitmaia.pt/eventos",
    "https://visitmaia.pt/experiencias/todoseventos",
]

# recolhe as urls dos eventos
def recolher_urls_eventos(*, limit: int | None = None) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    for page_url in LISTING_URLS:
        html = fetch_html(page_url)
        candidatos = extrair_urls_eventos_de_listagem(html)

        for u in candidatos:
            if u in seen:
                continue
            seen.add(u)
            urls.append(u)

            if limit is not None and len(urls) >= limit:
                return urls[:limit]

    return urls[:limit] if limit is not None else urls


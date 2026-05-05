from __future__ import annotations
from datetime import date, datetime

from scraper.fetch import fetch_html, fetch_json
from scraper.parse import extrair_urls_eventos_de_listagem

# urls das paginas de eventos
LISTING_URLS = [
    "https://visitmaia.pt/eventos",
    "https://visitmaia.pt/experiencias/todoseventos",
]

# parsea a data do evento da API
def _parse_event_api_date(item: dict) -> date | None:
    """ a API do calendário devolve year/month/day separados """
    try:
        y = int(item.get("year"))
        m = int(item.get("month"))
        d = int(item.get("day"))
        return date(y, m, d)
    except Exception:
        return None

# recolhe os urls dos eventos da API
def _recolher_urls_eventos_calendario(*, inicio: date, fim: date) -> list[str]:
    """ fonte principal é a API usada pelo calendário em /eventos (sem browser):
        JS: GET https://visitmaia.pt/api/aapillevents """
    
    data = fetch_json("https://visitmaia.pt/api/aapillevents")
    if not isinstance(data, list):
        return []

    urls: list[str] = []
    seen: set[str] = set()

    for item in data:
        if not isinstance(item, dict):
            continue
        slug = item.get("slug")
        if not slug:
            continue

        dt = _parse_event_api_date(item)
        if not dt:
            continue
        if dt < inicio or dt > fim:
            continue

        url = f"https://visitmaia.pt/eventos/{slug}"
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)

    return urls


# recolhe as urls dos eventos
def recolher_urls_eventos(*, limit: int | None = None, inicio: date | None = None, fim: date | None = None) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    if inicio and fim:
        candidatos = _recolher_urls_eventos_calendario(inicio=inicio, fim=fim)
        for u in candidatos:
            if u in seen:
                continue
            seen.add(u)
            urls.append(u)
            if limit is not None and len(urls) >= limit:
                return urls[:limit]

    # fallback: páginas estáticas com alguns links
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


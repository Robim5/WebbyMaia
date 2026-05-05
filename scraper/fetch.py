from __future__ import annotations
import httpx

# headers para o request
DEFAULT_HEADERS = {
    "User-Agent": "WebbyMaiaBot/1.0 (+https://github.com/)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
}

# faz o request e retorna o html
def fetch_html(url: str, *, timeout_s: float = 20.0) -> str:
    with httpx.Client(
        timeout=timeout_s,
        follow_redirects=True,
        headers=DEFAULT_HEADERS,
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text

# faz o request e retorna o json
def fetch_json(url: str, *, timeout_s: float = 20.0):
    with httpx.Client(
        timeout=timeout_s,
        follow_redirects=True,
        headers=DEFAULT_HEADERS,
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


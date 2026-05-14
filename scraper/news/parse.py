from __future__ import annotations
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from rules_news_cate import detetar_categoria_noticia

BASE_URL = "https://www.cm-maia.pt"

MESES_PT = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4,
    "mai": 5, "jun": 6, "jul": 7, "ago": 8,
    "set": 9, "out": 10, "nov": 11, "dez": 12,
}

AUTOR_PADRAO = "Redacao Maia ON"


def _abs_url(path: str | None) -> str | None:
    if not path:
        return None
    return urljoin(BASE_URL, path)


def _limpar_espacos(texto: str) -> str:
    return re.sub(r"\s+", " ", texto or "").strip()


def _parse_data_pt(dia: str, mes_curto: str, ano: str) -> str | None:
    try:
        d = int(dia.strip())
        m = MESES_PT.get(mes_curto.strip().lower()[:3])
        y = int(ano.strip())
        if not m:
            return None
        return f"{y:04d}-{m:02d}-{d:02d}"
    except (ValueError, AttributeError):
        return None


def _extrair_data(li) -> str | None:
    date_block = li.select_one(".date.widget_field")
    if not date_block:
        return None
    dia = date_block.select_one(".dia")
    mes = date_block.select_one(".mes_curto")
    ano = date_block.select_one(".ano")
    if not (dia and mes and ano):
        return None
    return _parse_data_pt(dia.get_text(), mes.get_text(), ano.get_text())


def _tempo_leitura(resumo: str) -> str:
    palavras = len(_limpar_espacos(resumo).split())
    minutos = max(1, round(palavras / 200))
    return f"{minutos} min"


def parse_noticias_listagem(html: str, *, limit: int = 5) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")

    # tenta encontrar o bloco de notícias
    widget = soup.select_one('div.widget.news_list[data-content_type="NewsList"]')
    if not widget:
        widget = soup.select_one("div.news_list")
    if not widget:
        raise RuntimeError("Não encontrei o widget de notícias no HTML.")

    noticias: list[dict] = []
    items = widget.select("ul > li")[:limit]

    for i, li in enumerate(items, start=1):
        overlay = li.select_one("a.linl_overlay")
        if not overlay:
            continue

        titulo = _limpar_espacos(overlay.get("a.linl_overlay") or "")
        if not titulo:
            h2 = li.select_one("h2")
            titulo = _limpar_espacos(h2.get_text() if h2 else "")

        url = _abs_url(overlay.get("href"))
        if not titulo or not url:
            continue

        summary_el = li.select_one(".summary .widget_value")
        resumo = _limpar_espacos(summary_el.get_text(" ", strip=True) if summary_el else "")

        img = li.select_one("img[src]")
        imagem = _abs_url(img.get("src")) if img else None

        data_iso = _extrair_data(li)
        categoria = detetar_categoria_noticia(titulo=titulo, resumo=resumo)["categoria"]

        noticias.append({
            "categoria": categoria,
            "titulo": titulo,
            "resumo": resumo,
            "data_publicacao": data_iso,
            "autor": AUTOR_PADRAO,
            "destaque": i == 1,
            "url_noticia": url,
            "imagem_url": imagem,
            "tempo_leitura": _tempo_leitura(resumo),
        })

    return noticias
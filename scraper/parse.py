from __future__ import annotations
import re
from datetime import date, datetime
from typing import Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from rules_cate import detetar_categoria

# url base do site
BASE_URL = "https://visitmaia.pt"

# normaliza o url
def normalizar_url(url: str | None) -> str | None:
    if not url:
        return None
    return urljoin(BASE_URL, url)

# extrai o texto do elemento
def texto_ou_none(elemento) -> str | None:
    if not elemento:
        return None
    texto = elemento.get_text(" ", strip=True)
    return texto or None

# extrai os detalhes do evento
def extrair_tabela_detalhes(soup: BeautifulSoup) -> dict[str, str | None]:
    detalhes: dict[str, str | None] = {}

    for linha in soup.select("table tr"):
        colunas = linha.find_all("td")
        if len(colunas) >= 2:
            chave = colunas[0].get_text(" ", strip=True)
            valor = colunas[1].get_text(" ", strip=True)
            if chave:
                detalhes[chave] = valor or None

    return detalhes

# tenta converter a data para ISO
def _try_parse_date_iso(value: str) -> str | None:
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None

# converte a data para ISO
def converter_data_pt(data_texto: str | None, *, ano_default: int | None = None) -> str | None:
    if not data_texto:
        return None

    raw = data_texto.strip()
    if not raw:
        return None

    iso = _try_parse_date_iso(raw)
    if iso:
        return iso

    ano = ano_default or date.today().year

    for formato in ("%d/%m/%Y", "%d/%m"):
        try:
            dt = datetime.strptime(raw, formato)
            if formato == "%d/%m":
                dt = dt.replace(year=ano)
            return dt.date().isoformat()
        except ValueError:
            pass

    return None

# separa o intervalo de data
def separar_intervalo_data(data_texto: str | None, *, ano_default: int | None = None) -> tuple[str | None, str | None]:
    if not data_texto:
        return None, None

    raw = data_texto.strip()
    if not raw:
        return None, None

    if " a " in raw:
        inicio_raw, fim_raw = raw.split(" a ", 1)
    else:
        inicio_raw = fim_raw = raw

    return (
        converter_data_pt(inicio_raw, ano_default=ano_default),
        converter_data_pt(fim_raw, ano_default=ano_default),
    )

# extrai o titulo do evento
def extrair_titulo_evento(soup: BeautifulSoup) -> str | None:
    return texto_ou_none(soup.find("h4"))

def extrair_descricao_evento(soup: BeautifulSoup) -> str | None:
    h4 = soup.find("h4")
    if not h4:
        return None

    for p in h4.find_next_siblings("p"):
        texto = p.get_text(" ", strip=True)
        if texto:
            return texto

    return None


def extrair_imagem_evento(soup: BeautifulSoup) -> str | None:
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return normalizar_url(og["content"])

    for img in soup.find_all("img"):
        src = (img.get("src") or "").strip()
        if not src:
            continue
        if "/assets/images/events/" in src:
            return normalizar_url(src)

    return None

# normaliza o preco
def normalizar_preco(preco_texto: str | None, *, texto_extra: str | None = None) -> str | None:
    """
    - "gratuito" -> "Gratuito"
    - 1 valor em € -> "X€"
    - vários valores em € -> "Desde X€" (menor valor)
    - vazio -> None
    """
    partes = []
    if preco_texto:
        partes.append(preco_texto)
    if texto_extra:
        partes.append(texto_extra)

    bruto = "\n".join([p for p in partes if p]).strip()
    if not bruto:
        return None

    if "gratuito" in bruto.lower():
        return "Gratuito"

    # se o site indicar sob consulta não vale a pena inventar preço.
    if "sob consulta" in bruto.lower():
        return "Sob Consulta"

    # Extrair valores do tipo 5.00 €, 5,00 €, 5 €
    nums = re.findall(r"(\d+(?:[.,]\d+)?)\s*€", bruto)
    if not nums:
        # se não há nenhum valor em € ou gratuito
        return "Sob Consulta"

    valores = []
    for n in nums:
        n = n.replace(",", ".")
        try:
            valores.append(float(n))
        except ValueError:
            pass

    if not valores:
        return bruto

    minimo = min(valores)
    # Formatar: sem .00 se for inteiro
    if abs(minimo - int(minimo)) < 1e-9:
        minimo_fmt = f"{int(minimo)}€"
    else:
        minimo_fmt = f"{minimo:.2f}€"

    if len(set(valores)) > 1:
        return f"Desde {minimo_fmt}"
    return minimo_fmt

# parsea o html do evento
def parse_evento_html(html: str, *, url_evento: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")

    titulo = extrair_titulo_evento(soup)
    detalhes = extrair_tabela_detalhes(soup)
    descricao = extrair_descricao_evento(soup)
    imagem_url = extrair_imagem_evento(soup)

    data_inicio, data_fim = separar_intervalo_data(detalhes.get("Data"))

    # em alguns eventos o preço vem vazio na tabela, mas existe no texto (ex: várias opções)
    preco = normalizar_preco(detalhes.get("Preço"), texto_extra=soup.get_text("\n", strip=True))

    analise = detetar_categoria(
        titulo=titulo,
        descricao=descricao,
        local=detalhes.get("Local"),
        mais_informacoes=detalhes.get("Mais informações"),
    )

    return {
        "titulo": titulo,
        "url_evento": url_evento,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "descricao": descricao,
        "imagem_url": imagem_url,
        "local": detalhes.get("Local"),
        "preco": preco,
        "categoria": analise["categoria"],
        "is_principal": False,
    }

# parsea o url do evento
def parse_evento_url(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        return normalizar_url(canonical.get("href"))
    return None

# extrai os urls dos eventos da listagem
def extrair_urls_eventos_de_listagem(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    urls: list[str] = []
    seen: set[str] = set()

    for a in soup.select("a[href]"):
        href = normalizar_url(a.get("href"))
        if not href:
            continue
        if "/eventos/" not in href:
            continue

        # Evitar URLs irrelevantes tipo /eventos (lista) e âncoras.
        if href.rstrip("/") == f"{BASE_URL}/eventos":
            continue

        # Evitar duplicados.
        if href in seen:
            continue
        seen.add(href)
        urls.append(href)

    return urls


import re
import json
from datetime import datetime, timedelta

from playwright.sync_api import sync_playwright

from rules_cate import detetar_categoria

BASE_URL = "https://visitmaia.pt"
URL = f"{BASE_URL}/eventos"


def normalizar_url(url):
    if not url:
        return None

    if url.startswith("http"):
        return url

    if url.startswith("/"):
        return f"{BASE_URL}{url}"

    return url


def separar_intervalo_data(data_texto):
    if not data_texto:
        return None, None

    partes = [parte.strip() for parte in data_texto.split(" a ")]

    data_inicio = partes[0] if len(partes) > 0 and partes[0] else None
    data_fim = partes[1] if len(partes) > 1 and partes[1] else data_inicio

    return data_inicio, data_fim


def extrair_detalhes_tabela(page):
    detalhes = {}
    linhas = page.locator("table tr")

    for i in range(linhas.count()):
        linha = linhas.nth(i)
        colunas = linha.locator("td")

        if colunas.count() >= 2:
            chave = colunas.nth(0).inner_text().strip()
            valor = colunas.nth(1).inner_text().strip()

            if chave:
                detalhes[chave] = valor

    return detalhes


def extrair_descricao(bloco_principal):
    paragrafos = bloco_principal.locator("p")

    for i in range(paragrafos.count()):
        texto = paragrafos.nth(i).inner_text().strip()
        if texto:
            return texto

    return None


def navegar_para_mes(page, mes_numero):
    """clica no mes, o atributo iv = 6 é junho """
    page.locator(f'td.month[iv="{mes_numero}"]').click()
    page.wait_for_timeout(1500)


def clicar_dia(page, dia):
    """ procura o número do dia entre as células com eventos e clica nele, só clica se o dia for o mesmo que o dia passado como parâmetro, devolve True se encontrou e clicou, False se o dia não tem eventos """
    celulas = page.locator("td.table-date.event-date")

    for i in range(celulas.count()):
        texto = celulas.nth(i).inner_text().strip()
        if re.fullmatch(r"\d+", texto) and int(texto) == dia:
            celulas.nth(i).click()
            page.wait_for_timeout(2000)
            return True

    return False


def recolher_links_do_dia(page):
    """ após clicar num dia, recolhe todos os links dos eventos que aparecem no bloco .events-container """
    cards = page.locator(".event-card a")
    links = []

    for i in range(cards.count()):
        href = cards.nth(i).get_attribute("href")
        href = normalizar_url(href)

        if href and href not in links:
            links.append(href)

    return links


def scrape_proximos_n_dias(page, n=30):
    """ navega o calendário durante n dias a partir de hoje..
    para cada dia:
      1. muda de mês no calendário se necessário
      2. clica no dia
      3. recolhe todos os links de eventos desse dia
    devolve um dicionário com os links de eventos de cada dia: { "YYYY-MM-DD": ["url1", "url2", ...] } """
    
    hoje = datetime.today()
    links_por_dia = {}
    mes_atual_no_calendario = None

    for i in range(n):
        data = hoje + timedelta(days=i)
        mes = data.month
        dia = data.day
        chave = data.strftime("%Y-%m-%d")

        # só navega para o mês se mudou
        if mes != mes_atual_no_calendario:
            navegar_para_mes(page, mes)
            mes_atual_no_calendario = mes

        encontrou = clicar_dia(page, dia)

        if not encontrou:
            links_por_dia[chave] = []
            print(f"{chave}: sem eventos")
            continue

        links = recolher_links_do_dia(page)
        links_por_dia[chave] = links
        print(f"{chave}: {len(links)} eventos encontrados")

    return links_por_dia


def extrair_evento(page, detalhe_url):
    page.goto(detalhe_url)
    page.wait_for_timeout(3000)

    titulo = page.locator("h4").first.inner_text().strip()
    bloco_principal = page.locator("h4").first.locator("xpath=..")

    detalhes = extrair_detalhes_tabela(page)
    descricao = extrair_descricao(bloco_principal)

    imagem = bloco_principal.locator("img").first.get_attribute("src")
    imagem = normalizar_url(imagem)

    data_inicio, data_fim = separar_intervalo_data(detalhes.get("Data"))

    analise_categoria = detetar_categoria(
        titulo=titulo,
        descricao=descricao,
        local=detalhes.get("Local"),
        mais_informacoes=detalhes.get("Mais informações"),
    )

    campos_base = {"Local", "Data", "Preço", "Mais informações"}
    campos_extras = {}

    for chave, valor in detalhes.items():
        if chave not in campos_base:
            campos_extras[chave] = valor

    evento = {
        "titulo": titulo,
        "url_evento": detalhe_url,
        "imagem": imagem,
        "local": detalhes.get("Local"),
        "descricao": descricao,
        "preco": detalhes.get("Preço"),
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "mais_informacoes": detalhes.get("Mais informações"),
        "campos_extras": campos_extras,
        "categoria": analise_categoria["categoria"],
        "categoria_motivos": analise_categoria["motivos"],
    }

    return evento


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(URL)
        page.wait_for_timeout(5000)

        # primeiro, navegar o calendário 30 dias e recolher os links de cada dia
        print("=== A recolher links dos próximos 30 dias ===")
        links_por_dia = scrape_proximos_n_dias(page, n=30)

        # segundo, reunir todos os URLs únicos para não scraper o mesmo evento duas vezes
        todos_urls = {url for links in links_por_dia.values() for url in links}
        print(f"\n=== {len(todos_urls)} evento(s) único(s) encontrado(s). A extrair detalhes... ===")

        cache_eventos = {}

        for url in todos_urls:
            try:
                evento = extrair_evento(page, url)
                cache_eventos[url] = evento
                print(f"  OK: {evento['titulo']} [{evento['categoria']}]")
            except Exception as e:
                print(f"  ERRO em {url}: {e}")

        # terceiro, montar o JSON agrupado por dia
        eventos_por_dia = {}
        for data, links in links_por_dia.items():
            eventos_do_dia = [cache_eventos[u] for u in links if u in cache_eventos]
            eventos_por_dia[data] = eventos_do_dia

        hoje = datetime.today()
        resultado = {
            "data_ultima_atualizacao": datetime.now().isoformat(timespec="seconds"),
            "fonte": URL,
            "periodo": {
                "inicio": hoje.strftime("%Y-%m-%d"),
                "fim": (hoje + timedelta(days=29)).strftime("%Y-%m-%d"),
            },
            "eventos_por_dia": eventos_por_dia,
        }

        with open("eventos.json", "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)

        print("\nDados guardados em eventos.json")
        browser.close()


if __name__ == "__main__":
    main()

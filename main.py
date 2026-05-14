from __future__ import annotations
import os
from datetime import date, datetime
from scraper.fetch import fetch_html
from scraper.main_agenda import carregar_titulos_principais, marcar_evento_principal
from scraper.parse import parse_evento_html
from scraper.source import recolher_urls_eventos
from db.supabase_client import add_calendar_months, limpar_eventos_antigos, upsert_eventos
from web.app import app 
from scraper.news.source import recolher_noticias_recentes
from db.supabase_client import sincronizar_noticias

# converte data ISO para date
def _parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None

# verifica se o evento está no intervalo de datas
def evento_esta_no_intervalo(evento: dict, *, inicio: date, fim: date) -> bool:
    """ mantém o evento se houver overlap de datas -> data_inicio e data_fim do evento estão dentro do intervalo de datas """
    di = _parse_iso_date(evento.get("data_inicio"))
    df = _parse_iso_date(evento.get("data_fim")) or di

    if not di:
        return False

    return not (df < inicio or di > fim)


def main() -> None:
    titulos_principais = carregar_titulos_principais()

    # para manter o railway leve podes limitar quantos URLs vais buscar tipo definir MAX_URLS=80 nas variáveis do railway
    max_urls_raw = os.getenv("MAX_URLS")
    max_urls = int(max_urls_raw) if max_urls_raw and max_urls_raw.isdigit() else None

    hoje = date.today()
    # nao procuramos eventos passados
    # busca eventos de agora até +4 meses (calendário) e faz limpeza na BD por data_inicio (ver limpar_eventos_antigos)
    janela_inicio = hoje
    janela_fim = add_calendar_months(hoje, 4)
    print(f"Janela de datas: {janela_inicio.isoformat()} -> {janela_fim.isoformat()}")

    # a fonte principal é a API do calendário (muito mais completa que o HTML estático)
    urls = recolher_urls_eventos(limit=max_urls, inicio=janela_inicio, fim=janela_fim)
    print(f"URLs recolhidos (calendário/API): {len(urls)}")

    eventos = []
    for i, url in enumerate(urls, start=1):
        try:
            html = fetch_html(url)
            evento = parse_evento_html(html, url_evento=url)
            marcar_evento_principal(evento, titulos_principais)

            if evento_esta_no_intervalo(evento, inicio=janela_inicio, fim=janela_fim):
                eventos.append(evento)
                dentro = True
            else:
                dentro = False

            print(
                f"[{i}/{len(urls)}] OK: {evento.get('titulo')} | "
                f"principal={evento.get('is_principal')} | dentro_janela={dentro}"
            )
        except Exception as erro:
            print(f"[{i}/{len(urls)}] ERRO em {url}: {erro}")

    # railway cron job -> o script deve terminar se faltar config do supabase faz-se dry-run
    try:
        enviados = upsert_eventos(eventos, on_conflict="url_evento")
        print(f"Upsert concluído. Eventos enviados: {enviados}")

        apagados = limpar_eventos_antigos()
        print(f"Auto-limpeza concluída. Eventos apagados: {apagados}")
    except Exception as erro:
        print(f"Upsert ignorado (falta de .env/vars no Railway secalhar): {erro}")
        print(f"Dry-run OK. Eventos extraídos: {len(eventos)}")

def main_noticias() -> None:
    print("--- Notícias CM Maia ---")
    noticias = recolher_noticias_recentes(limit=5)

    for i, n in enumerate(noticias, start=1):
        print(
            f"[noticia {i}/5] {n.get('titulo')} | "
            f"{n.get('data_publicacao')} | {n.get('categoria')}"
        )

    try:
        total = sincronizar_noticias(noticias)
        print(f"Notícias sincronizadas: {total}")
    except Exception as erro:
        print(f"Notícias ignoradas (falta .env/Supabase): {erro}")
        print(f"Dry-run notícias OK. Extraídas: {len(noticias)}")

if __name__ == "__main__":
    main()
    main_noticias()


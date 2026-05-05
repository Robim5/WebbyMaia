from __future__ import annotations
import os
from datetime import date, datetime, timedelta
from scraper.fetch import fetch_html
from scraper.main_agenda import carregar_titulos_principais, marcar_evento_principal
from scraper.parse import parse_evento_html
from scraper.source import recolher_urls_eventos
from db.supabase_client import limpar_eventos_antigos, upsert_eventos

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
    # busca eventos de agora até +2 meses, mantem 2 meses e depois limpa
    janela_inicio = hoje
    janela_fim = hoje + timedelta(days=60)  # 2 meses frente
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

        apagados = limpar_eventos_antigos(retention_days=60)
        print(f"Auto-limpeza concluída. Eventos apagados: {apagados}")
    except Exception as erro:
        print(f"Upsert ignorado (falta de .env/vars no Railway secalhar): {erro}")
        print(f"Dry-run OK. Eventos extraídos: {len(eventos)}")


if __name__ == "__main__":
    main()
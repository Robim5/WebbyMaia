from __future__ import annotations

import calendar
import os
from datetime import date
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client

# cria o cliente supabase
def get_supabase_client() -> Client:
    # carrega as variáveis de ambiente (dotenv para o railway)
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise RuntimeError(
            "Faltam variáveis de ambiente SUPABASE_URL e/ou SUPABASE_SERVICE_ROLE_KEY."
        )

    return create_client(url, key)


def add_calendar_months(d: date, months: int) -> date:
    """ soma meses de calendário a uma data (ajusta o dia ao fim do mês destino) """
    m0 = d.month - 1 + months
    y = d.year + m0 // 12
    m = m0 % 12 + 1
    last = calendar.monthrange(y, m)[1]
    return date(y, m, min(d.day, last))


# insere ou atualiza os eventos na tabela
def upsert_eventos(eventos: list[dict[str, Any]], *, on_conflict: str = "url_evento") -> int:
    if not eventos:
        return 0

    supabase = get_supabase_client()
    (
        supabase.table("eventos")
        .upsert(eventos, on_conflict=on_conflict)
        .execute()
    )
    return len(eventos)


# auto-limpeza -> apaga eventos cuja data_inicio cai em meses demasiado antigos (4 meses)
def limpar_eventos_antigos(*, meses_passados_a_manter: int = 4) -> int:
    supabase = get_supabase_client()
    hoje = date.today()
    inicio_mes_atual = date(hoje.year, hoje.month, 1)
    cutoff = add_calendar_months(inicio_mes_atual, -meses_passados_a_manter)
    cutoff_iso = cutoff.isoformat()

    resp = (
        supabase.table("eventos")
        .delete()
        .lt("data_inicio", cutoff_iso)
        .execute()
    )

    data = getattr(resp, "data", None)
    if isinstance(data, list):
        return len(data)
    return 0

# lista eventos com filtros opcionais
def listar_eventos(*, limit: int = 200, categoria: str | None = None, q: str | None = None, principal: bool | None = None):
    supabase = get_supabase_client()
    query = supabase.table("eventos").select("*")
    
    if categoria:
        query = query.eq("categoria", categoria)
    if principal is True:
        query = query.eq("is_principal", True)
    if q: 
        # ilike para pesquisar texto (depende do schema é rubusto)
        query = query.ilike("titulo", f"%{q}%")
        
    resp = query.order("data_inicio", desc=False).limit(limit).execute()
    data = getattr(resp, "data", None)
    return data or []

# obtem evento por url_evento
def obter_evento_por_url_evento(url_evento: str):
    supabase = get_supabase_client()
    resp = supabase.table("eventos").select("*").eq("url_evento", url_evento).maybe_single().execute()
    return getattr(resp, "data", None)

def sincronizar_noticias(noticias: list[dict[str, Any]], *, on_conflict: str = "url_noticia") -> int:
    """ guarda as 5 noticias e apaga qualquer outra que ja nao esteja no top 5 """
    if not noticias:
        return 0

    supabase = get_supabase_client()
    urls = [n["url_noticia"] for n in noticias]

    supabase.table("noticias").upsert(noticias, on_conflict=on_conflict).execute()

    if urls:
        supabase.table("noticias").delete().not_.in_("url_noticia", urls).execute()

    return len(noticias)

def listar_noticias(*, limit: int = 5, categoria: str | None = None) -> list[dict]:
    supabase = get_supabase_client()
    query = supabase.table("noticias").select("*")

    if categoria:
        query = query.eq("categoria", categoria)

    resp = query.order("data_publicacao", desc=True).limit(limit).execute()
    data = getattr(resp, "data", None)
    return data or []


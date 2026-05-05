from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
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


# auto-limpeza -> apaga registos com data_extracao mais antiga que retention_days
def limpar_eventos_antigos(*, retention_days: int = 60) -> int:
    supabase = get_supabase_client()
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    cutoff_iso = cutoff.isoformat()

    resp = (
        supabase.table("eventos")
        .delete()
        .lt("data_extracao", cutoff_iso)
        .execute()
    )

    data = getattr(resp, "data", None)
    if isinstance(data, list):
        return len(data)
    return 0

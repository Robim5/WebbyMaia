from __future__ import annotations
import json
from pathlib import Path
from typing import Any

# normaliza nome
def normalizar_nome(texto: str | None) -> str:
    return (texto or "").lower().strip()

# carrega titulos principais do ficheiro JSON
def carregar_titulos_principais(caminho: str = "main_events_agenda.json") -> set[str]:
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    titulos: set[str] = set()

    eventos_ano: dict[str, Any] = dados.get("eventos_2026", {})
    for eventos_do_mes in eventos_ano.values():
        for evento in eventos_do_mes:
            nome = evento.get("nome")
            if nome:
                titulos.add(normalizar_nome(nome))

    return titulos

# marca evento principal se o titulo do evento aparecer dentro do titulo do site
def marcar_evento_principal(evento: dict, titulos_principais: set[str]) -> dict:
    titulo_site = normalizar_nome(evento.get("titulo"))

    # compara do genero: se o título do evento principal aparecer
    evento["is_principal"] = any(tp in titulo_site for tp in titulos_principais)
    return evento


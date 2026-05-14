from __future__ import annotations

REGRAS_CATEGORIA_NOTICIAS = {
    "Voluntariado": [
        "voluntariado",
        "voluntario",
        "voluntária",
        "voluntarios",
        "voluntários",
        "capital europeia do voluntariado",
    ],
    "Solidariedade": [
        "solidariedade",
        "apoio social",
        "banco alimentar",
        "caridade",
        "associacoes",
        "associações",
    ],
    "Educacao": [
        "escola",
        "escolas",
        "alunos",
        "ensino",
        "educacao",
        "educação",
        "professor",
        "professores",
    ],
    "Desporto": [
        "desporto",
        "futebol",
        "torneio",
        "campeonato",
        "ecocaminho",
        "corrida",
        "caminhada",
    ],
    "Turismo": [
        "turismo",
        "visita",
        "roteiro",
        "turismo senior",
        "turismo sénior",
    ],
    "Institucional": [
        "camara municipal",
        "câmara municipal",
        "municipio",
        "município",
        "assembleia",
        "deliberacao",
        "deliberação",
        "conselho municipal",
    ],
    "Cultura": [
        "exposicao",
        "exposição",
        "teatro",
        "museu",
        "arquitectura",
        "arquitetura",
        "centro de documentacao",
        "centro de documentação",
        "biblioteca",
    ],
}

ORDEM_PRIORIDADE_DESEMPATE = (
    "Institucional",
    "Voluntariado",
    "Solidariedade",
    "Desporto",
    "Turismo",
    "Educacao",
    "Cultura",
)

CATEGORIA_DEFAULT = "Cultura"


def _normalizar(texto: str | None) -> str:
    if not texto:
        return ""
    return texto.lower().strip()


def _pontuacoes(texto: str) -> dict[str, list[str]]:
    resultado: dict[str, list[str]] = {}
    for categoria, palavras in REGRAS_CATEGORIA_NOTICIAS.items():
        encontrados = [p for p in palavras if p in texto]
        resultado[categoria] = encontrados
    return resultado


def _escolher(pontuacoes: dict[str, list[str]]) -> tuple[str, list[str]]:
    melhor = CATEGORIA_DEFAULT
    melhor_motivos: list[str] = []
    melhor_pri = len(ORDEM_PRIORIDADE_DESEMPATE) + 1

    for categoria, motivos in pontuacoes.items():
        n = len(motivos)
        if n == 0:
            continue
        try:
            pri = ORDEM_PRIORIDADE_DESEMPATE.index(categoria)
        except ValueError:
            pri = len(ORDEM_PRIORIDADE_DESEMPATE)
        n_melhor = len(melhor_motivos)
        if n > n_melhor or (n == n_melhor and pri < melhor_pri):
            melhor = categoria
            melhor_motivos = motivos
            melhor_pri = pri

    return melhor, melhor_motivos


def detetar_categoria_noticia(*, titulo: str | None = None, resumo: str | None = None) -> dict:
    """ devolve {"categoria": "Cultura", "motivos": [...]} """
    texto = _normalizar(f"{titulo or ''} {resumo or ''}")
    pontuacoes = _pontuacoes(texto)
    categoria, motivos = _escolher(pontuacoes)
    return {"categoria": categoria, "motivos": motivos}
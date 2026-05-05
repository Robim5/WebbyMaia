REGRAS_CATEGORIA = {
    "Institucional": [
        "presidente da camara",
        "presidente da câmara",
        "presidente da republica",
        "presidente da república",
        "vereador",
        "vereadora",
        "assembleia municipal",
        "sessao solene",
        "sessão solene",
        "tomada de posse",
        "inauguracao oficial",
        "inauguração oficial",
        "cerimonia oficial",
        "cerimónia oficial",
    ],
    "Educação": [
        "escola",
        "escolas",
        "agrupamento",
        "secundaria",
        "secundária",
        "basica",
        "básica",
        "alunos",
        "professores",
        "professor",
        "escolar",
        "sala de aula",
        "turma",
        "ensino",
    ],
    "Desporto": [
        "corrida",
        "caminhada",
        "torneio",
        "campeonato",
        "futebol",
        "ginastica",
        "ginástica",
        "desporto",
        "atleta",
        "trail",
        "maratona",
        "wushu",
        "equestre",
        "goalkeeper",
        "urban race",
        "jogos de tabuleiro",
    ],
    "Juventude": [
        "jovens",
        "juventude",
        "adolescentes",
        "maiores de 6 anos",
        "maiores de 12 anos",
        "ferias jovens",
        "férias jovens",
        "inter-rail",
        "interrail",
    ],
    "Turismo": [
        "visita guiada",
        "roteiro",
        "welcome center",
        "turistico",
        "turístico",
        "patrimonio",
        "património",
        "percursos",
        "festival",
        "fest outdoor",
        "beer market",
        "mercado gastronomico",
        "mercado gastronómico",
        "solsticio",
        "solstício",
        "venda de bilhetes",
    ],
    "Cultura": [
        "exposicao",
        "exposição",
        "teatro",
        "cinema",
        "fados",
        "museu",
        "biblioteca",
        "arte",
        "literatura",
        "workshop",
        "oficina",
        "atelier",
        "ateliers",
        "concerto",
        "empreza",
        "bolhão",
        "bolhao",
        "gastronomia",
        "cozinha",
        "brunch",
        "snacks",
        "saladas",
    ],
}

# em empate no número de palavras encontradas, ganha a categoria mais à esquerda
ORDEM_PRIORIDADE_DESEMPATE = (
    "Institucional",
    "Desporto",
    "Turismo",
    "Educação",
    "Juventude",
    "Cultura",
)

CATEGORIA_DEFAULT = "Cultura"

# overrides por subcadeia no título (minúsculas), ordem frases mais longas primeiro
OVERRIDES_TITULO: tuple[tuple[str, str], ...] = (
    ("encontro mensal de jogos de tabuleiro", "Desporto"),
    ("goalkeeper summer tournament", "Desporto"),
    ("maia urban race", "Desporto"),
    ("9.º desfile equestre", "Desporto"),
    ("9º desfile equestre", "Desporto"),
    ("desfile equestre", "Desporto"),
    ("torneio internacional de wushu", "Desporto"),
    ("north festival", "Turismo"),
    ("maia fest outdoor", "Turismo"),
    ("solstício – festival de verão", "Turismo"),
    ("solsticio – festival de verão", "Turismo"),
    ("workshop snacks", "Cultura"),
    ("workshop saladas", "Cultura"),
    ("workshop brunch", "Cultura"),
    ("the beatles", "Turismo"),
    ("tributo aos the beatles", "Turismo"),
    ("empreza do bolhão", "Cultura"),
    ("empreza do bolhao", "Cultura"),
    ("a empreza do bolhão", "Cultura"),
)


def normalizar_texto(texto):
    if not texto:
        return ""
    return texto.lower().strip()


def categoria_por_override_titulo(titulo: str | None) -> str | None:
    if not titulo:
        return None
    t = normalizar_texto(titulo)
    for fragmento, categoria in OVERRIDES_TITULO:
        if fragmento in t:
            return categoria
    return None


def juntar_textos_eventos(titulo=None, descricao=None, local=None, mais_informacoes=None):
    partes = [
        titulo or "",
        descricao or "",
        local or "",
        mais_informacoes or "",
    ]
    return " ".join(partes)


def encontrar_palavras_categoria(texto, palavras):
    encontrados = []

    for palavra in palavras:
        if palavra in texto:
            encontrados.append(palavra)

    return encontrados


def calcular_pontuacoes(texto):
    pontuacoes = {}

    for categoria, palavras in REGRAS_CATEGORIA.items():
        encontrados = encontrar_palavras_categoria(texto, palavras)
        pontuacoes[categoria] = encontrados

    return pontuacoes


def escolher_melhor_categoria(pontuacoes):
    melhor_categoria = CATEGORIA_DEFAULT
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
            melhor_categoria = categoria
            melhor_motivos = motivos
            melhor_pri = pri

    return melhor_categoria, melhor_motivos


def detetar_categoria(titulo=None, descricao=None, local=None, mais_informacoes=None):
    override = categoria_por_override_titulo(titulo)
    if override:
        return {
            "categoria": override,
            "motivos": ["override_titulo"],
            "texto_analisado": normalizar_texto(
                juntar_textos_eventos(
                    titulo=titulo,
                    descricao=descricao,
                    local=local,
                    mais_informacoes=mais_informacoes,
                )
            ),
        }

    texto_completo = juntar_textos_eventos(
        titulo=titulo,
        descricao=descricao,
        local=local,
        mais_informacoes=mais_informacoes,
    )

    texto_normalizado = normalizar_texto(texto_completo)
    pontuacoes = calcular_pontuacoes(texto_normalizado)
    categoria, motivos = escolher_melhor_categoria(pontuacoes)

    return {
        "categoria": categoria,
        "motivos": motivos,
        "texto_analisado": texto_normalizado,
    }

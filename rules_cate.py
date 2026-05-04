REGRAS_CATEGORIA = {
    "Institucional": [
        "presidente",
        "vereador",
        "vereadora",
        "camara municipal",
        "câmara municipal",
        "municipio",
        "município",
        "sessao solene",
        "sessão solene",
        "inauguracao oficial",
        "inauguração oficial",
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
        "escolar",
        "educativo",
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
    ],
    "Juventude": [
        "jovens",
        "juventude",
        "adolescentes",
        "maiores de 6 anos",
        "maiores de 12 anos",
        "oficina",
        "atelier",
        "ateliers",
        "ferias jovens",
        "férias jovens",
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
        "gastronomico",
        "gastronómico",
    ],
    "Cultura": [
        "exposicao",
        "exposição",
        "teatro",
        "concerto",
        "cinema",
        "fados",
        "museu",
        "biblioteca",
        "arte",
        "literatura",
    ],
}

CATEGORIA_DEFAULT = "Cultura"

def normalizar_texto(texto):
    if not texto:
        return ""
    return texto.lower().strip()

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
    melhor_motivos = []

    for categoria, motivos in pontuacoes.items():
        if len(motivos) > len(melhor_motivos):
            melhor_categoria = categoria
            melhor_motivos = motivos

    return melhor_categoria, melhor_motivos

def detetar_categoria(titulo=None, descricao=None, local=None, mais_informacoes=None):
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
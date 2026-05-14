CREATE TABLE IF NOT EXISTS noticias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    categoria TEXT NOT NULL DEFAULT 'Cultura',
    titulo TEXT NOT NULL,
    resumo TEXT,
    data_publicacao DATE,
    autor TEXT DEFAULT 'Redacao Maia ON',
    destaque BOOLEAN DEFAULT FALSE,
    url_noticia TEXT UNIQUE NOT NULL,
    imagem_url TEXT,
    tempo_leitura TEXT,
    data_extracao TIMESTAMPTZ DEFAULT NOW()
);
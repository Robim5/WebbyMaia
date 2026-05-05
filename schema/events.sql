CREATE TABLE IF NOT EXISTS eventos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo TEXT NOT NULL,
    url_evento TEXT UNIQUE NOT NULL,
    data_inicio DATE,
    data_fim DATE,
    descricao TEXT,
    imagem_url TEXT,
    local TEXT, 
    preco TEXT,
    categoria TEXT,
    is_principal BOOLEAN,
    data_extracao TIMESTAMPTZ DEFAULT NOW()
);
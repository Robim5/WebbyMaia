# WebbyMaia — Documentação do *frontend* (web)

Interface **Flask** que lê dados já guardados no **Supabase**: **eventos** (listagem com filtros, paginação, detalhe) e **notícias** (lista curta alimentada pela sincronização das cinco últimas).

---

## Onde está o código

| Caminho | Função |
|---------|--------|
| `web/app.py` | Aplicação Flask: rotas `/`, `/noticias` e `/evento` |
| `web/templates/base.html` | *Layout* comum (cabeçalho, navegação Eventos / Notícias, CSS) |
| `web/templates/index.html` | Lista de eventos, formulário de filtros, paginação |
| `web/templates/noticias.html` | Lista das **5** notícias (filtro opcional por categoria) |
| `web/templates/evento.html` | Detalhe de um evento |
| `web/static/styles.css` | Estilos (tema, grelha, cartões, paginação) |
| `web/static/webby.png` | Logótipo servido em `/static/` |

O cliente Supabase reutiliza `db/supabase_client.py` (`listar_eventos`, `obter_evento_por_url_evento`, `listar_noticias`).

---

## Como correr em local

Na raiz do projeto (com o *virtualenv* ativo e dependências instaladas):

```bash
python -m web.app
```

Por omissão o servidor fica em `http://127.0.0.1:5000/`.

São necessárias as mesmas variáveis do Supabase que o *scraper* usa (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` no `.env`), porque a web **não** grava eventos nem notícias: só consulta as tabelas `eventos` e `noticias`.

---

## Rotas e fluxo

### `GET /` — Listagem de eventos

1. Lê a *query string*: `q` (pesquisa por título), `categoria`, `principal=1` (só eventos marcados como principais), `page` (número da página).
2. Chama `listar_eventos(limit=1000, ...)` com os filtros aplicados no Supabase.
3. **Paginação em memória**: o limite alto traz a lista filtrada; o Python corta o *slice* da página atual (`per_page = 18` eventos por página).
4. Calcula `total_pages` e passa tudo ao *template* `index.html`.

**Nota:** para volumes muito grandes de eventos no futuro, faria sentido paginar na *query* (*offset*/*limit* no PostgREST). Para o volume atual da janela de *scrape* (quatro meses à frente), a abordagem é suficiente.

### `GET /noticias` — Notícias (cinco entradas)

1. Lê `categoria` opcional na *query string*.
2. Chama `listar_noticias(limit=5, categoria=...)`.
3. Renderiza `noticias.html` com a lista (no máximo cinco linhas, coerente com o que `main.py` / `sincronizar_noticias` mantém na base de dados).

### `GET /evento?url=<url codificada>` — Detalhe do evento

1. O link “Ver detalhes” na lista usa `ev.url_evento` com `urlencode`.
2. A rota obtém o registo com `obter_evento_por_url_evento(url_evento)`.
3. Se não existir → **404**. Se faltar o parâmetro `url` → **400**.

---

## O que o utilizador vê

### Cabeçalho e navegação (`base.html`)

- Marca WebbyMaia + subtítulo; logótipo ao lado do texto; link para `/`.
- Navegação: **Eventos** (`/`) e **Notícias** (`/noticias`).

### Listagem de eventos (`index.html`)

- **Formulário** (método `GET` na mesma página): pesquisa por título, filtro por categoria (lista fixa alinhada com as categorias do *backend*), caixa de visto “Só principais”, botão “Aplicar” e link “Limpar”.
- **Resumo:** total de eventos após filtros.
- **Grelha de cartões:** cada evento mostra imagem (se `imagem_url` existir), título, *badge* “principal” se `is_principal`, meta (datas, local, preço, categoria), acções “Ver detalhes” e “Abrir fonte” (URL original do Visit Maia).
- **Paginação** (só se `total_pages > 1`): controlo compacto com **`<`** e **`>`** nas pontas e indicador **`página/total`** ao centro (ex.: `1/3`). Setas inativas na primeira/última página (estilo desativado, sem link).

### Página de notícias (`noticias.html`)

- Listagem das notícias sincronizadas (até **cinco**), com título, data, categoria, resumo e ligação para o artigo no sítio da CM Maia, conforme os campos gravados na tabela `noticias`.

### Página de detalhe do evento (`evento.html`)

- Ligação “voltar” para `/`.
- Cartão alargado com imagem grande (quando existe), título, *badge* principal, bloco de meta, descrição e botão para abrir no Visit Maia.

---

## Tema e responsividade (`styles.css`)

Paleta baseada em **cinzento azulado**, **azul escuro** e **verde escuro** (variáveis CSS em `:root`), com:

- fundo da página e gradiente suave no *topbar*;
- cartões com sombra e *hover*;
- formulário e *inputs* coerentes com o tema;
- grelha `repeat(auto-fill, minmax(...))` para adaptar o número de colunas ao ecrã;
- *media queries* para ecrãs estreitos (cabeçalho, formulário em coluna, margens).

---

## Ficheiros estáticos e *cache*

- O CSS é referenciado com `url_for('static', filename='styles.css')` (*cache busting* manual só se mudar o nome do ficheiro).
- A *logo* deve existir em `web/static/webby.png` para o `img` do cabeçalho carregar sem erro em qualquer *deploy*.

## WebbyMaia — Documentação do backend (dados e base de dados)

### O que é este projeto
O **WebbyMaia** é um conjunto de scripts em Python que:
- vão ao site `visitmaia.pt`
- descobrem **eventos** através do **calendário do site** (API JSON)
- visitam cada página de evento para extrair campos úteis
- classificam cada evento com **regras de categoria** (`rules_cate.py`)
- guardam tudo na tabela `eventos` do Supabase com **upsert**
- fazem **auto-limpeza** de eventos antigos com base na **`data_inicio`** do evento (não na data de extração)
- em paralelo, recolhem as **5 notícias mais recentes** do sítio da **Câmara Municipal da Maia** (`cm-maia.pt`), classificam-nas (`rules_news_cate.py`) e **sincronizam** a tabela `noticias` no Supabase (o conjunto visível no site é sempre esse “top 5”)

O objetivo é correr o extrator sozinho no **Railway**, como Cron Job. A **interface web** (Flask) só lê estes dados; está documentada em [`webbyWebDoc.md`](webbyWebDoc.md).

---

## Como a recolha de eventos funciona (importante)

### Porque “o calendário” é obrigatório
Na página `https://visitmaia.pt/eventos` existe um calendário. Quando se escolhe um dia, a lista ao lado muda.

Isso acontece porque o site **não traz todos os eventos no HTML inicial**. Usa JavaScript para carregar os eventos.

### A solução sem browser
O site chama uma API:
- **GET** `https://visitmaia.pt/api/aapillevents`

Essa API devolve uma lista grande de eventos com campos como:
- `slug` (para construir o URL do evento)
- `year`, `month`, `day` (data do evento no calendário)
- `name`, `local`, etc.

Usamos essa API para obter mais eventos (sem Playwright).

---

## Estrutura do projeto (o que faz cada pasta/ficheiro)

### `main.py` (o “chefe” do scrape)
É o ficheiro que o Railway corre no job agendado.

**Eventos** — faz, por esta ordem:
1. Define a janela de scraping: **hoje → mais 4 meses de calendário** (função `add_calendar_months` em `db/supabase_client.py`, não são 120 dias fixos)
2. Recolhe URLs via API do calendário (`recolher_urls_eventos(inicio, fim)`)
3. Para cada URL:
   - faz o pedido do HTML
   - extrai campos (título, datas, descrição, imagem, preço, categoria, etc.)
   - marca `is_principal` conforme `main_events_agenda.json`
4. Filtra eventos cuja janela de datas intersecta a janela de scrape
5. Faz `upsert` na tabela `eventos` no Supabase
6. Faz **auto-limpeza** no Supabase (remove eventos cuja `data_inicio` é anterior ao corte — ver abaixo)
7. Termina (importante para Cron Jobs)

**Notícias** — a seguir, `main_noticias()`:
1. Obtém **5** notícias da listagem institucional (`scraper/news/source.py`)
2. Faz `sincronizar_noticias`: *upsert* das 5 e **apaga** na BD qualquer notícia cujo `url_noticia` já não esteja nesse conjunto (o site fica sempre alinhado com essas cinco)

### `scraper/fetch.py` (pedidos HTTP)
- `fetch_html(url)`: devolve HTML como texto
- `fetch_json(url)`: devolve JSON (usado na API do calendário)

### `scraper/source.py` (descobrir URLs de eventos)
Responsável por descobrir URLs como:
`https://visitmaia.pt/eventos/<slug>`

Tem duas fontes:
- **Fonte principal**: API do calendário `https://visitmaia.pt/api/aapillevents` (mais completa)
- **Fallback**: páginas “estáticas” com poucos links (se a API falhar)

### `scraper/parse.py` (extrair dados do HTML do evento)
Recebe o HTML de uma página de evento e devolve um `dict` com os campos para a BD.

Pontos importantes:
- **Imagem do evento** (`extrair_imagem_evento`): já **não** se confia só no primeiro `og:image` ou na primeira `<img>`. O parser junta imagens cujo `src` contém `/assets/images/events/`, **pontua** cada candidata (conteúdo principal *vs.* barra lateral/rodapé/cabeçalho, proximidade do `h4` do título, tamanho mínimo) e escolhe a melhor. O `og:image` só entra na disputa se for URL de *asset* de evento, com peso baixo.
- **Descrição**: primeiro parágrafo com texto real a seguir ao `h4` (há `<p>` vazios no HTML)
- **Preço**: normalização em `normalizar_preco` (ver secção mais abaixo)
- **Categoria**: resultado de `detetar_categoria` em `rules_cate.py` (título, descrição, local, “Mais informações” da tabela)

### `scraper/news/` (notícias da CM Maia)
- **`source.py`**: página de listagem `https://www.cm-maia.pt/institucional/atualidade-e-participacao/noticias`; `recolher_noticias_recentes(limit=5)` por omissão
- **`parse.py`**: extrai título, URL, resumo, data em formato ISO, imagem, tempo de leitura; categoria via `rules_news_cate`

### `rules_cate.py` (categoria do evento)
- **`REGRAS_CATEGORIA`**: palavras-chave por categoria (Institucional, Educação, Desporto, Juventude, Turismo, Cultura).
- **Institucional** está **restrito** a contextos tipo cargos políticos, sessões solenes, tomada de posse, etc. **Não** se usam termos genéricos como “câmara municipal” só na descrição de uma exposição — isso gerava falsos positivos.
- **`ORDEM_PRIORIDADE_DESEMPATE`**: em empate no número de palavras encontradas, decide qual categoria vence.
- **`OVERRIDES_TITULO`**: pares (fragmento do título em minúsculas, categoria) avaliados **antes** das regras gerais, para casos muito específicos (ex.: *workshops* de gastronomia, festivais, torneios).
- **`CATEGORIA_DEFAULT`**: `Cultura`, quando não há *matches*.

### `rules_news_cate.py` (categoria da notícia)
Regras semelhantes em espírito às dos eventos, aplicadas ao título/resumo das notícias para preencher `categoria` na tabela `noticias`.

### `scraper/main_agenda.py` (marcar eventos principais)
Lê `main_events_agenda.json` (agenda manual) e marca:
- `is_principal=True` se o nome da agenda aparecer no título do site

### `db/supabase_client.py` (ligação ao Supabase)
Funções principais:
- `add_calendar_months(d, months)`: aritmética de **meses de calendário** (útil para a janela de scrape e para o corte de limpeza)
- `upsert_eventos(eventos, on_conflict="url_evento")`: insere ou atualiza eventos
- `limpar_eventos_antigos(meses_passados_a_manter=4)`: apaga eventos com `data_inicio` **estritamente anterior** ao primeiro dia do mês resultante de: **(1.º dia do mês corrente) − 4 meses**. Exemplo: em **julho de 2026** o corte é **1 de março de 2026** — removem-se eventos que começam em **janeiro**, **fevereiro** ou antes (mantêm-se a partir de março, inclusivamente)
- `listar_eventos(...)`: usado pela aplicação web (filtros opcionais)
- `obter_evento_por_url_evento(url)`: detalhe de um evento na web
- `sincronizar_noticias(noticias)`: *upsert* das URLs atuais e remoção das restantes na tabela `noticias`
- `listar_noticias(limit=5, ...)`: leitura para a página de notícias na web

---

## O que acontece na base de dados (Supabase)

### Tabela `eventos` (schema em `schema/events.sql`)

| Coluna | Notas |
|--------|--------|
| `id` | UUID, chave primária |
| `titulo` | Obrigatório |
| `url_evento` | **UNIQUE**, chave lógica do *upsert* |
| `data_inicio`, `data_fim` | Datas ISO (`DATE`); a **limpeza** usa `data_inicio` |
| `descricao`, `imagem_url`, `local`, `preco`, `categoria` | Texto |
| `is_principal` | Boolean |
| `data_extracao` | `TIMESTAMPTZ`, preenchido na inserção/atualização (já **não** serve de critério principal para apagar eventos) |

### Tabela `noticias` (schema em `schema/news.sql`)

| Coluna | Notas |
|--------|--------|
| `id` | UUID, chave primária |
| `categoria` | Texto; por omissão na BD `Cultura`; o scraper preenche conforme `rules_news_cate` |
| `titulo` | Obrigatório |
| `resumo` | Texto opcional |
| `data_publicacao` | `DATE` |
| `autor` | Texto; valor por omissão no *scraper* alinhado com a listagem |
| `destaque` | Boolean |
| `url_noticia` | **UNIQUE**, chave do *upsert* / sincronização |
| `imagem_url`, `tempo_leitura` | Texto opcional |
| `data_extracao` | `TIMESTAMPTZ` |

### Como o *upsert* decide “criar *vs.* atualizar”
**Eventos:** se `url_evento` **não existe** → cria; se **já existe** → atualiza (incluindo `categoria`, `imagem_url`, etc., conforme o último scrape).

**Notícias:** idem com `url_noticia`. Depois do *upsert*, linhas com outros URLs são **removidas**, para a BD refletir apenas as cinco notícias atuais.

---

## Regras importantes do campo `preco` (eventos)
O objetivo é ter um valor curto e útil (não `null`, não um texto gigante).

Regras:
- Se tiver “Gratuito” → `Gratuito`
- Se tiver “Sob consulta” → `Sob Consulta`
- Se tiver 1 valor em € (ex.: `30.00 €`) → `30€` (ou `30.50€`)
- Se tiver vários valores em € → `Desde X€` (pega no menor, ex.: `Desde 5€`)
- Se não houver nenhum valor claro em € → `Sob Consulta`

---

## Janela de scrape e retenção na base de dados (eventos)

### Janela à frente (calendário)
O script considera eventos **desde hoje até quatro meses à frente** no calendário (soma de meses à data de hoje, com ajuste ao último dia do mês de destino). A API filtra por dia; cada página é ainda validada contra a mesma janela.

### Retenção (passado)
A auto-limpeza **não** usa `data_extracao` como critério principal. Remove linhas em que **`data_inicio` < primeiro dia do mês (hoje − 4 meses)**, contando a partir do dia 1 do mês corrente.

**Nota:** notícias **não** são limpas por esta função; o modelo é “sincronizar sempre 5 URLs”.

**Eventos sem `data_inicio`:** a condição `data_inicio < corte` em SQL não apaga linhas com `NULL` nesse campo. Se existirem, convém corrigi-los no *scrape* ou tratar manualmente.

---

## Railway — quando a base de dados é atualizada

### Quem manda no horário
Quem define isto é o **Cron Schedule** do Railway.

Exemplo comum (referido no README):
- `0 6 * * *` → uma vez por dia às **06:00 UTC**

### Fuso horário
O Railway avalia o *cron* em **UTC** (normalmente). Se o objetivo for uma hora fixa em Portugal continental, há que contar com a diferença para UTC (incluindo horário de verão).

---

## Variáveis do Railway (configuração)
No Railway → Service → Variables:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- (opcional) `MAX_URLS` (ex.: `80`, para limitar quantos URLs se processam)

---

## Como validar que está tudo bem

### Localmente (`python main.py`)
Deve aparecer:
- `Janela de datas: ...` (intervalo de cerca de quatro meses à frente)
- `URLs recolhidos (calendário/API): N`
- `Upsert concluído. Eventos enviados: N`
- `Auto-limpeza concluída. Eventos apagados: X`
- Bloco `--- Notícias CM Maia ---`, linhas `[noticia i/5] ...`
- `Notícias sincronizadas: 5` (em condições normais)

### No Railway
Nos *logs* do serviço, as mesmas linhas devem surgir.

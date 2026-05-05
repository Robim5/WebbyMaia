## WebbyMaia — Documentação do backend (dados e base de dados)

### O que é este projeto
O **WebbyMaia** é um conjunto de scripts em Python que:
- vão ao site `visitmaia.pt`
- descobrem eventos através do **calendário do site** (API JSON)
- visitam cada página de evento para extrair campos úteis
- classificam cada evento com **regras de categoria** (`rules_cate.py`)
- guardam tudo na tabela `eventos` do Supabase com **upsert**
- e no fim fazem **auto-limpeza** (apagam registos com `data_extracao` mais antiga que o período configurado)

O objetivo é correr o extrator sozinho no **Railway**, como Cron Job. A **interface web** (Flask) só lê estes dados; está documentada em [`webbyWebDoc.md`](webbyWebDoc.md).

---

## Como a recolha de eventos funciona (importante)

### Porque “o calendário” é obrigatório
Na página `https://visitmaia.pt/eventos` existe um calendário. Quando clicas num dia, a lista ao lado muda.

Isso acontece porque o site **não traz todos os eventos no HTML inicial**. Ele usa JavaScript para carregar os eventos.

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

Ele faz:
1. Define a janela de scraping: **hoje → +60 dias (~2 meses)**
2. Recolhe URLs via API do calendário (`recolher_urls_eventos(inicio, fim)`)
3. Para cada URL:
   - faz download do HTML
   - extrai campos (título, datas, descrição, imagem, preço, categoria, etc.)
   - marca `is_principal` conforme `main_events_agenda.json`
4. Filtra eventos dentro da janela de datas
5. Faz `upsert` no Supabase
6. Faz auto-limpeza no Supabase (apaga registos com `data_extracao` antiga)
7. Termina (importante para Cron Jobs)

### `scraper/fetch.py` (pedidos HTTP)
- `fetch_html(url)`: devolve HTML como texto
- `fetch_json(url)`: devolve JSON (usado na API do calendário)

### `scraper/source.py` (descobrir URLs de eventos)
Responsável por descobrir URLs como:
`https://visitmaia.pt/eventos/<slug>`

Tem duas fontes:
- **Fonte principal**: API do calendário `https://visitmaia.pt/api/aapillevents` (mais completa)
- **Fallback**: páginas “estáticas” com poucos links (se a API falhar)

### `scraper/parse.py` (extrair dados do HTML)
Recebe o HTML de uma página de evento e devolve um `dict` com os campos para a BD.

Pontos importantes:
- **Imagem do evento** (`extrair_imagem_evento`): já **não** se confia só no primeiro `og:image` ou na primeira `<img>`. O parser junta todas as imagens cujo `src` contém `/assets/images/events/`, **pontua** cada uma (conteúdo principal vs sidebar/footer/header, proximidade do `h4` do título, tamanho mínimo) e escolhe a melhor candidata. O `og:image` só entra na disputa se for URL de asset de evento, com peso baixo, para não “roubar” a imagem certa do corpo da página.
- **Descrição**: primeiro parágrafo com texto real a seguir ao `h4` (há `<p>` vazios no HTML)
- **Preço**: normalização em `normalizar_preco` (ver secção abaixo)
- **Categoria**: resultado de `detetar_categoria` em `rules_cate.py` (título, descrição, local, “Mais informações” da tabela)

### `rules_cate.py` (categoria do evento)
- **`REGRAS_CATEGORIA`**: palavras-chave por categoria (Institucional, Educação, Desporto, Juventude, Turismo, Cultura).
- **Institucional** está **restrito** a contextos tipo cargos políticos, sessões solenes, tomada de posse, etc. **Não** se usam termos genéricos como “câmara municipal” só na descrição de uma exposição — isso gerava falsos positivos.
- **`ORDEM_PRIORIDADE_DESEMPATE`**: em empate no número de palavras encontradas, decide qual categoria vence.
- **`OVERRIDES_TITULO`**: pares (fragmento do título em minúsculas, categoria) avaliados **antes** das regras gerais, para casos muito específicos (ex.: workshops de gastronomia, festivais, torneios).
- **`CATEGORIA_DEFAULT`**: `Cultura`, quando não há matches.

### `scraper/main_agenda.py` (marcar eventos principais)
Lê `main_events_agenda.json` (agenda manual) e marca:
- `is_principal=True` se o nome da agenda aparecer no título do site

### `db/supabase_client.py` (falar com Supabase)
Funções:
- `upsert_eventos(eventos, on_conflict="url_evento")`: insere ou atualiza
- `limpar_eventos_antigos(retention_days=60)`: apaga eventos antigos pela `data_extracao`
- `listar_eventos(...)`: usado pela app web (filtros opcionais)
- `obter_evento_por_url_evento(url)`: detalhe de um evento na web

---

## O que acontece na base de dados (Supabase)

### Tabela `eventos` (schema em `schema/events.sql`)

| Coluna | Notas |
|--------|--------|
| `id` | UUID, chave primária |
| `titulo` | Obrigatório |
| `url_evento` | **UNIQUE**, chave lógica do upsert |
| `data_inicio`, `data_fim` | Datas ISO (`DATE`) |
| `descricao`, `imagem_url`, `local`, `preco`, `categoria` | Texto |
| `is_principal` | Boolean |
| `data_extracao` | `TIMESTAMPTZ`, preenchido na inserção/atualização |

### Como o upsert decide “criar vs atualizar”
- Se `url_evento` **não existe** → cria um registo novo
- Se `url_evento` **já existe** → atualiza esse registo (incluindo `categoria`, `imagem_url`, etc., conforme o último scrape)

Isto permite correr todos os dias sem duplicar linhas e **corrige** imagens e categorias quando o parser ou as regras melhoram.

---

## Regras importantes do campo `preco`
O objetivo é ter um valor curto e útil (não `null`, não um texto gigante).

Regras:
- Se tiver “Gratuito” → `Gratuito`
- Se tiver “Sob consulta” → `Sob Consulta`
- Se tiver 1 valor em € (ex: `30.00 €`) → `30€` (ou `30.50€`)
- Se tiver vários valores em € → `Desde X€` (pega no menor, ex: `Desde 5€`)
- Se não houver nenhum valor claro em € → `Sob Consulta`

---

## “2 meses” -> o que significa exatamente

### Janela de scraping
O script procura eventos **de hoje até ~60 dias à frente** na API e, ao processar cada página, mantém só os que caem nesse intervalo de datas do evento.

### Retenção na base de dados
O script apaga eventos com `data_extracao` mais antiga que ~60 dias (`limpar_eventos_antigos`).

Exemplo: um evento extraído hoje “expira” na BD daqui a ~2 meses, no sentido da **limpeza por data de extração** (não confundir com a data em que o evento acontece).

---

## Railway -> quando atualiza a BD e quantas vezes

### Quem manda no horário
Quem define isto é o **Cron Schedule** do Railway.

Exemplo comum (que está no README):
- `0 6 * * *` → 1 vez por dia às **06:00 UTC**

### Importante: fuso horário
O Railway avalia o cron em **UTC** (normalmente).
Se quiseres que corra às 06:00 em Portugal, confirma a diferença de UTC na época (horário de verão pode mudar).

---

## Variáveis do Railway (o que tens de configurar)
No Railway → Service → Variables:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- (opcional) `MAX_URLS` (ex: `80`, para controlar custo)

---

## Como validar que está tudo OK

### Localmente (scrape)
Quando corres `python main.py` deves ver:
- `Janela de datas: ...`
- `URLs recolhidos (calendário/API): N`
- `Upsert concluído. Eventos enviados: N`
- `Auto-limpeza concluída. Eventos apagados: X`

### No Railway
Abre os logs do serviço e procura as mesmas linhas.
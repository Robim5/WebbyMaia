<p align="center">
  <img src="assets/webby.png?v=2" alt="Logo WebbyMaia" width="250" />
</p>

<hr />

# WebbyMaia

« Um programinho que liga o calendário da Maia ao teu ecrã. »

---

## Para que serve este projeto

O **WebbyMaia** existe para uma coisa simples e útil: **juntar num só sítio os eventos públicos do Visit Maia** e guardá-los numa **base de dados (Supabase/PostgreSQL)**, já com campos limpos e prontos a consumir noutra app, num site, num bot ou num painel.

Não substitui o site oficial: **respeita a fonte** e só organiza a informação para quem precisa de dados estruturados (estudantes, associações, developers, curiosos...).

---

## O que faz?

1. Vai buscar uma lista de URLs de eventos no site (sem browser), usando a **API do calendário** (`/api/aapillevents`).
2. Visita **cada página de evento** (uma vez por URL, para não repetir trabalho).
3. Extrai `titulo`, `url_evento`, `datas`, `local`, `preco`, `descricao`, `imagem_url` (com heurística para escolher a **imagem certa** do evento, ver documentação).
4. Atribui **categoria** com `rules_cate.py` (palavras-chave, desempates e **overrides por título** quando necessário).
5. Marca `is_principal=True` se o evento aparecer na agenda anual (`main_events_agenda.json`).
6. Faz **upsert** no Supabase (cria ou atualiza pelo `url_evento` UNIQUE).
7. Faz **auto-limpeza**: remove da BD eventos com `data_extracao` mais antiga que ~2 meses.

Além disso, o projeto inclui uma **interface web** em Flask (`web/`) que lê o Supabase e mostra a listagem com filtros, **18 eventos por página**, paginação compacta (`<` · `1/N` · `>`) e página de detalhe.

É, na prática, uma **ponte** entre o calendário bonito do Visit Maia e o formato que máquinas adoram: chaves, listas e ISO dates no cabeçalho do ficheiro — com opção de ver tudo num browser.

---

## Atualizações recentes (resumo)

- **Imagens:** parser a pontuar candidatos no HTML (evita `og:image` ou primeira `<img>` erradas entre eventos).
- **Categorias:** Institucional mais restrito; desempate entre categorias; overrides por título para casos limite.
- **Web:** tema cinzento-azulado / azul escuro / verde escuro, layout responsivo, logo em `web/static/webby.png`.
- **Documentação:** [`documentation/webbyDoc.md`](documentation/webbyDoc.md) (backend / BD), [`documentation/webbyWebDoc.md`](documentation/webbyWebDoc.md) (frontend).

---

## Interface web (espaço para captura de ecrã)


<p align="center">
  <img src="assets/displayFront.png" alt="WebbyMaia - Interface web com listagem de eventos" width="920" />
</p>

**Correr a interface:** `python -m web.app` (requer `.env` com Supabase, veja a secção de variáveis de ambiente).

---

## Ficheiros principais

| Ficheiro / pasta | Papel |
|------------------|-------|
| `main.py` | Script principal (Railway Cron Job): extrai → filtra → upsert → limpa → termina |
| `scraper/` | Scraping sem browser (`httpx` + `BeautifulSoup`) |
| `db/supabase_client.py` | Cliente Supabase: upsert, limpeza, leitura para a web |
| `rules_cate.py` | Categorização (regras, desempates, overrides por título) |
| `web/` | App Flask: listagem, filtros, paginação, detalhe do evento |
| `main_events_agenda.json` | Agenda “principal” para marcar `is_principal=True` |

---

## Requisitos

- Python 3.x
- `httpx`, `beautifulsoup4`, `lxml`, `supabase`, `python-dotenv`, `flask`, `gunicorn` (ver `requirements.txt`)

---

## Como correr

Na pasta do projeto:

```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Para **só ver os eventos no browser** (lê o Supabase):

```bash
python -m web.app
```

O script `main.py` imprime logs tipo:

- `URLs recolhidos (calendário/API): N`
- `Janela de datas: hoje -> +2 meses`
- `Upsert concluído. Eventos enviados: N`
- `Auto-limpeza concluída. Eventos apagados: X`

Se ainda não tiveres variáveis do Supabase, ele faz **dry-run** (extrai dados e termina, sem gravar). A app web **precisa** do Supabase configurado para listar dados.

---

## Variáveis de ambiente (segurança)

Cria um ficheiro `.env` (não comites; já está no `.gitignore`) com:

```env
SUPABASE_URL=https://<teu-projeto>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<a-tua-service-role-key>
MAX_URLS=80
```

- `SUPABASE_SERVICE_ROLE_KEY`: usa **Service Role** porque isto corre no backend (Railway). Nunca usar esta chave em frontend.
- `MAX_URLS` é opcional: serve para limitar quantos eventos processas e manter custos baixos.

---

## Janela de scraping e retenção (2 meses)

- O script **não está a tentar procurar eventos passados**.
- Ele guarda eventos **de hoje até ~2 meses à frente**.
- E faz **auto-limpeza** na BD: qualquer evento com `data_extracao` mais antiga que ~2 meses é apagado.

Exemplo: se um evento foi extraído hoje, ele “expira” na BD daqui a ~2 meses (aprox. 60 dias).

---

## Regras do campo `preco`

O site às vezes mostra preços como texto longo ou várias opções. Para manter a BD limpa, gravamos:

- Se o texto contiver **“Gratuito”** → `Gratuito`
- Se o texto contiver **“Sob consulta”** → `Sob Consulta`
- Se tiver **1 valor em €** → `X€` (ex: `30€`)
- Se tiver **vários valores em €** → `Desde X€` (usa o menor, ex: `Desde 5€`)
- Se não houver nenhum valor claro em € → `Sob Consulta`

---

## Deploy no Railway (Cron Job)

1. Liga o projeto ao GitHub no Railway.
2. Em **Variables**, adiciona:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - (opcional) `MAX_URLS`
3. Em **Start Command**, usa: `python main.py`
4. Em **Settings → Cron Schedule**, usa por exemplo:
   - `0 6 * * *` (todos os dias às 06:00 UTC)
5. Confirma nos logs que aparece:
   - `Upsert concluído...`
   - `Auto-limpeza concluída...`

---

## Sobre a logo 

O logótipo foi desenhado por mim (Robim) utilizando o [Canva](https://www.canva.com/). O ficheiro fonte está em `assets/webby.png`; para a interface Flask usa-se também uma cópia em `web/static/webby.png` (servida como ficheiro estático).

O conceito principal é um "W" de Webby, construído com a paleta de cores que melhor caracteriza a cidade da Maia:

- **Verde:** Inspirado na natureza local, como os emblemáticos parques, os jardins e a biodiversidade da cidade.
- **Azul e Cinzento:** Refletem a vertente urbana e digital. Representam tanto a arquitetura local (como o centro da Maia e a Torre do Lidador) como a identidade online e tecnológica do município.
---

## Nota importante

Web scraping depende do layout do site: se o Visit Maia mudar HTML, pode ser preciso ajustar selectores no `scraper/parse.py`. Usa os dados com bom senso e **em linha com os termos do site** que estás a ler.

---

<p align="center">
  <small>— WebbyMaia - dados de diversão, um mês de cada vez —</small>
</p>

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

1. Vai buscar uma lista de URLs de eventos no site (sem browser).
2. Visita **cada página de evento** (uma vez por URL, para não repetir trabalho).
3. Extrai `titulo`, `url_evento`, `datas`, `local`, `preco`, `descricao`, `imagem_url`.
4. Sugere uma **categoria** com regras de palavras-chave (`rules_cate.py`).
5. Marca `is_principal=True` se o evento aparecer na agenda anual (`main_events_agenda.json`).
6. Faz **upsert** no Supabase (cria ou atualiza pelo `url_evento` UNIQUE).
7. Faz **auto-limpeza**: remove da BD eventos com `data_extracao` mais antiga que ~2 meses.

É, na prática, uma **ponte** entre o calendário bonito do Visit Maia e o formato que máquinas adoram: chaves, listas e ISO dates no cabeçalho do ficheiro.

---

## Ficheiros principais

| Ficheiro        | Papel |
|-----------------|-------|
| `main.py` | Script principal (Railway Cron Job): extrai → filtra → upsert → limpa → termina |
| `scraper/` | Scraping sem browser (`httpx` + `BeautifulSoup`) |
| `db/supabase_client.py` | Cliente Supabase + upsert + limpeza |
| `rules_cate.py` | Regras simples para classificar eventos por palavras no texto |
| `main_events_agenda.json` | Agenda “principal” para marcar `is_principal=True` |

---

## Requisitos

- Python 3.x
- `httpx`, `beautifulsoup4`, `supabase`, `python-dotenv`

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

O script imprime logs tipo:

- `URLs recolhidos: N`
- `Janela de datas: hoje -> +2 meses`
- `Upsert concluído. Eventos enviados: N`
- `Auto-limpeza concluída. Eventos apagados: X`

Se ainda não tiveres variáveis do Supabase, ele faz **dry-run** (extrai dados e termina, sem gravar).

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

## Como funciona o Upsert (em português simples)

- A coluna `url_evento` na tabela `eventos` é **UNIQUE**.
- Quando fazemos `upsert(..., on_conflict="url_evento")`:
  - se a `url_evento` ainda não existir, cria um registo novo
  - se já existir, atualiza o registo existente

Resultado: podes correr o script todos os dias sem criar duplicados.

---

## Janela de scraping e retenção (2 meses)

- O script **não está a tentar “procurar eventos passados”**.
- Ele guarda eventos **de hoje até ~2 meses à frente**.
- E faz **auto-limpeza** na BD: qualquer evento com `data_extracao` mais antiga que ~2 meses é apagado.

Exemplo: se um evento foi extraído hoje, ele “expira” na BD daqui a ~2 meses (aprox. 60 dias).

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

O logótipo foi desenhado por mim (Robim) utilizando o [Canva](https://www.canva.com/). 

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

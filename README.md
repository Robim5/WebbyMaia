<p align="center">
  <img src="assets/webby.png" alt="Logo WebbyMaia" width="220" />
</p>

<hr />

# WebbyMaia

« Um programinho que liga o calendário da Maia ao teu ecrã. »

---

## Para que serve este projeto

O **WebbyMaia** existe para uma coisa simples e útil: **juntar num só sítio os eventos públicos do Visit Maia**.Aqueles eventos que aparecem no calendário de [visitmaia.pt/eventos](https://visitmaia.pt/eventos) e queremos **guardá-los em JSON**, já com texto limpo e campos que podes consumir noutra app, num site, num bot ou num painel.

Não substitui o site oficial: **respeita a fonte** e só organiza a informação para quem precisa de dados estruturados (estudantes, associações, developers, curiosos com uma folha de cálculo à mão…).

---

## O que faz?

1. Abre a página dos eventos como um browser faria (porque o calendário vive de JavaScript).
2. **Navega dia a dia** pelos próximos **30 dias**, como se estivesses a clicar em cada data.
3. Para cada dia, recolhe os **links** dos cartões de evento.
4. Visita **cada página de evento** (uma vez por URL, para não repetir trabalho).
5. Extrai título, local, datas, preço, descrição, imagem e **sugere uma categoria** com regras de palavras-chave (`rules_cate.py`).
6. Grava tudo em **`eventos.json`**, agrupado por data (`eventos_por_dia`).

É, na prática, uma **ponte** entre o calendário bonito do Visit Maia e o formato que máquinas adoram: chaves, listas e ISO dates no cabeçalho do ficheiro.

---

## Ficheiros principais

| Ficheiro        | Papel |
|-----------------|-------|
| `scrappy.py`    | Script Playwright: calendário → links → detalhes → JSON |
| `rules_cate.py` | Regras simples para classificar eventos por palavras no texto |
| `eventos.json`  | Saída gerada pelo script |

---

## Requisitos

- Python 3.x
- [Playwright](https://playwright.dev/python/) para Python (e browsers instalados com `playwright install`)

---

## Como correr

Na pasta do projeto:

```bash
pip install playwright
playwright install chromium
python scrappy.py
```

O script abre o Chromium (visível por defeito), percorre os dias e no fim escreve `eventos.json`. Se quiseres correr às escuras, podes alterar em `scrappy.py` o `headless=False` para `headless=True`.

---

## Sobre a logo 

O logótipo foi desenhado por mim (Robim) utilizando o [Canva](https://www.canva.com/). 

O conceito principal é um "W" de Webby, construído com a paleta de cores que melhor caracteriza a cidade da Maia:

- **Verde:** Inspirado na natureza local, como os emblemáticos parques, os jardins e a biodiversidade da cidade.
- **Azul e Cinzento:** Refletem a vertente urbana e digital. Representam tanto a arquitetura local (como o centro da Maia e a Torre do Lidador) como a identidade online e tecnológica do município.
---

## Nota importante

Web scraping depende do layout do site: se o Visit Maia mudar classes HTML ou o calendário, pode ser preciso ajustar selectores em `scrappy.py`. Usa os dados com bom senso e **em linha com os termos do site** que estás a ler.

---

<p align="center">
  <small>— WebbyMaia - dados de diversão, um mês de cada vez —</small>
</p>

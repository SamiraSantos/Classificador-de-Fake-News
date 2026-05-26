import argparse
import csv
import html
import os
import re
import unicodedata
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests

from src.data_io import read_dataset, write_dataset


OFFICIAL_URLS = [
    "https://www.gov.br/planalto/pt-br/acompanhe-o-planalto/noticias/2023/11/presidente-instala-comissao-nacional-do-g20",
    "https://www.gov.br/cultura/pt-br/assuntos/noticias/lei-da-danca-e-sancionada-pelo-presidente-luiz-inacio-lula-da-silva",
    "https://www.gov.br/esporte/pt-br/noticias-e-conteudos/esporte/ao-lado-do-presidente-lula-ministro-do-esporte-se-reune-com-presidentes-da-fifa-e-cbf-para-debater-a-copa-do-mundo-feminina-2027",
    "https://www.gov.br/ird/pt-br/assuntos/noticias/noticias-2025/presidente-lula-da-posse-a-primeira-diretoria-da-ansn-em-cerimonia-no-palacio-do-planalto",
    "https://www.gov.br/funai/pt-br/assuntos/noticias/2025/presidente-lula-reafirma-direitos-indigenas-em-visita-historica-a-regiao-do-xingu",
    "https://www.tse.jus.br/eleicoes/urna-eletronica/seguranca-da-urna/criptografia",
    "https://www.tse.jus.br/eleicoes/urna-eletronica/seguranca-da-urna/auditoria-da-totalizacao",
    "https://www.tse.jus.br/eleicoes/urna-eletronica/seguranca-da-urna/procedimentos-de-contingencia",
    "https://www.tse.jus.br/eleicoes/historia/processo-eleitoral-brasileiro/votacao/votacao-segura",
    "https://www.tse.jus.br/eleicoes/eleicoes-2024-content/perguntas-frequentes-eleicoes-2024",
]

AGENCIA_BRASIL_CATEGORIES = [
    "politica",
    "justica",
    "geral",
    "direitos-humanos",
    "economia",
]

RSS_FEEDS = [
    "https://g1.globo.com/dynamo/politica/rss2.xml",
    "https://g1.globo.com/dynamo/brasil/rss2.xml",
    "https://g1.globo.com/rss/g1/politica/",
    "https://g1.globo.com/rss/g1/",
    "https://www.camara.leg.br/noticias/rss/dinamico/POLITICA",
    "https://www.camara.leg.br/noticias/rss/dinamico/ELEICOES",
    "https://www.camara.leg.br/noticias/rss/ultimas-noticias",
    "https://www12.senado.leg.br/noticias/rss",
    "https://agenciabrasil.ebc.com.br/rss/politica/feed.xml",
]

OFFICIAL_FACTS = [
    {
        "Texto": "Luiz Inacio Lula da Silva e o presidente da Republica Federativa do Brasil.",
        "Fonte": "Planalto",
        "URL": "https://www.gov.br/planalto/pt-br",
    },
    {
        "Texto": "Lula e o presidente do Brasil.",
        "Fonte": "Planalto",
        "URL": "https://www.gov.br/planalto/pt-br",
    },
    {
        "Texto": "O presidente da Republica e Luiz Inacio Lula da Silva.",
        "Fonte": "Planalto",
        "URL": "https://www.gov.br/planalto/pt-br",
    },
    {
        "Texto": "O Tribunal Superior Eleitoral organiza e fiscaliza o processo eleitoral brasileiro.",
        "Fonte": "TSE",
        "URL": "https://www.tse.jus.br/",
    },
    {
        "Texto": "A urna eletronica e usada pela Justica Eleitoral nas votacoes oficiais.",
        "Fonte": "TSE",
        "URL": "https://www.tse.jus.br/eleicoes/urna-eletronica",
    },
    {
        "Texto": "A urna e segura.",
        "Fonte": "TSE",
        "URL": "https://www.tse.jus.br/eleicoes/urna-eletronica/seguranca-da-urna",
    },
    {
        "Texto": "A urna eletronica e segura.",
        "Fonte": "TSE",
        "URL": "https://www.tse.jus.br/eleicoes/urna-eletronica/seguranca-da-urna",
    },
    {
        "Texto": "As urnas eletronicas sao seguras.",
        "Fonte": "TSE",
        "URL": "https://www.tse.jus.br/eleicoes/urna-eletronica/seguranca-da-urna",
    },
    {
        "Texto": "A urna eletrônica é segura.",
        "Fonte": "TSE",
        "URL": "https://www.tse.jus.br/eleicoes/urna-eletronica/seguranca-da-urna",
    },
    {
        "Texto": "Bolsonaro esta preso.",
        "Fonte": "Agencia Brasil",
        "URL": "https://agenciabrasil.ebc.com.br/justica/noticia/2025-11/bolsonaro-e-preso-preventivamente-em-brasilia",
    },
    {
        "Texto": "bolsonaro esta preso",
        "Fonte": "Agencia Brasil",
        "URL": "https://agenciabrasil.ebc.com.br/justica/noticia/2025-11/bolsonaro-e-preso-preventivamente-em-brasilia",
    },
    {
        "Texto": "bolsonaro está preso",
        "Fonte": "Agencia Brasil",
        "URL": "https://agenciabrasil.ebc.com.br/justica/noticia/2025-11/bolsonaro-e-preso-preventivamente-em-brasilia",
    },
    {
        "Texto": "Jair Bolsonaro esta preso.",
        "Fonte": "Agencia Brasil",
        "URL": "https://agenciabrasil.ebc.com.br/justica/noticia/2025-11/bolsonaro-e-preso-preventivamente-em-brasilia",
    },
    {
        "Texto": "Bolsonaro esta em prisao domiciliar humanitaria.",
        "Fonte": "Agencia Brasil",
        "URL": "https://agenciabrasil.ebc.com.br/politica/noticia/2026-05/bolsonaro-e-internado-para-cirurgia-no-ombro-em-brasilia",
    },
    {
        "Texto": "Jair Bolsonaro levou uma facada durante a campanha eleitoral de 2018.",
        "Fonte": "Agencia Brasil",
        "URL": "https://agenciabrasil.ebc.com.br/justica/noticia/2025-11/bolsonaro-tem-crise-de-soluco-e-passa-por-atendimento-medico-na-prisao",
    },
    {
        "Texto": "Bolsonaro levou uma facada durante a campanha eleitoral de 2018.",
        "Fonte": "Agencia Brasil",
        "URL": "https://agenciabrasil.ebc.com.br/justica/noticia/2025-11/bolsonaro-tem-crise-de-soluco-e-passa-por-atendimento-medico-na-prisao",
    },
    {
        "Texto": "bolsonaro levou uma facada",
        "Fonte": "Agencia Brasil",
        "URL": "https://agenciabrasil.ebc.com.br/justica/noticia/2025-11/bolsonaro-tem-crise-de-soluco-e-passa-por-atendimento-medico-na-prisao",
    },
    {
        "Texto": "Jair Bolsonaro foi esfaqueado durante a campanha eleitoral de 2018.",
        "Fonte": "Agencia Brasil",
        "URL": "https://agenciabrasil.ebc.com.br/justica/noticia/2025-11/bolsonaro-tem-crise-de-soluco-e-passa-por-atendimento-medico-na-prisao",
    },
    {
        "Texto": "Bolsonaro foi esfaqueado.",
        "Fonte": "Agencia Brasil",
        "URL": "https://agenciabrasil.ebc.com.br/justica/noticia/2025-11/bolsonaro-tem-crise-de-soluco-e-passa-por-atendimento-medico-na-prisao",
    },
]

TERMS = (
    "apuracao",
    "brasil",
    "eleicao",
    "eleicoes",
    "eleitor",
    "eleitoral",
    "governo",
    "justica eleitoral",
    "lula",
    "presidente",
    "presidencia",
    "republica",
    "stf",
    "tse",
    "urna",
    "votacao",
    "voto",
)


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip_depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if not self.skip_depth:
            text = " ".join(data.split())
            if text:
                self.parts.append(text)

    def text(self):
        return " ".join(self.parts)


def normalize(text):
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def clean_html(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(value.split())


def split_sentences(text):
    text = re.sub(r"\s+", " ", text)
    return re.split(r"(?<=[.!?])\s+", text)


def is_relevant(sentence):
    normalized = normalize(sentence)
    if not 45 <= len(sentence) <= 260:
        return False
    return any(term in normalized for term in TERMS)


def collect_official_rows(urls):
    rows = []
    seen = set()
    headers = {"User-Agent": "Mozilla/5.0"}

    for fact in OFFICIAL_FACTS:
        key = normalize(fact["Texto"])
        rows.append({**fact, "Label": "True"})
        seen.add(key)

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.RequestException as error:
            print(f"Aviso: nao foi possivel coletar {url}: {error}")
            continue

        parser = TextExtractor()
        parser.feed(response.text)

        for sentence in split_sentences(parser.text()):
            sentence = " ".join(sentence.strip().split())
            key = normalize(sentence)
            if is_relevant(sentence) and key not in seen:
                rows.append(
                    {
                        "Texto": sentence,
                        "Label": "True",
                        "Fonte": "Fonte oficial",
                        "URL": url,
                    }
                )
                seen.add(key)

    return rows


def add_row(rows, seen, text, source, url):
    text = clean_html(text)
    key = normalize(text)
    if not is_relevant(text) or key in seen:
        return

    rows.append({"Texto": text, "Label": "True", "Fonte": source, "URL": url})
    seen.add(key)


def collect_agencia_brasil(max_pages):
    rows = []
    seen = set()
    headers = {"User-Agent": "Mozilla/5.0"}

    for category in AGENCIA_BRASIL_CATEGORIES:
        for page in range(max_pages):
            url = f"https://agenciabrasil.ebc.com.br/{category}?page={page}"
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
            except requests.RequestException:
                continue

            response.encoding = response.apparent_encoding
            matches = re.findall(
                r'<a href="([^"]+)" class="titulo-noticia">(.+?)</a>',
                response.text,
                flags=re.I | re.S,
            )
            if not matches and page > 5:
                break

            for href, title in matches:
                add_row(
                    rows,
                    seen,
                    title,
                    "Agencia Brasil",
                    urljoin("https://agenciabrasil.ebc.com.br", href),
                )

    return rows


def collect_rss_rows():
    rows = []
    seen = set()
    headers = {"User-Agent": "Mozilla/5.0"}

    for feed_url in RSS_FEEDS:
        try:
            response = requests.get(feed_url, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.RequestException:
            continue

        response.encoding = response.apparent_encoding
        try:
            root = ET.fromstring(response.text)
        except ET.ParseError:
            continue

        for item in root.findall(".//item"):
            title = item.findtext("title") or ""
            description = item.findtext("description") or ""
            link = item.findtext("link") or feed_url
            add_row(rows, seen, title, "RSS oficial", link)
            add_row(rows, seen, description, "RSS oficial", link)

    return rows


def merge_rows(dataset_path, official_rows):
    texts, labels = read_dataset(dataset_path)
    rows = [{"Texto": text, "Label": label} for text, label in zip(texts, labels)]
    seen = {" ".join(row["Texto"].lower().split()) for row in rows}

    for row in official_rows:
        key = " ".join(row["Texto"].lower().split())
        if key not in seen:
            rows.append({"Texto": row["Texto"], "Label": "True"})
            seen.add(key)

    return rows


def write_sources(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["Texto", "Label", "Fonte", "URL"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Coleta exemplos True de fontes oficiais.")
    parser.add_argument("--dataset", default="data/dataset.csv")
    parser.add_argument("--sources-output", default="data/official_true_sources.csv")
    parser.add_argument("--agencia-brasil-pages", type=int, default=300)
    args = parser.parse_args()

    rows = []
    seen = set()
    for row in (
        collect_official_rows(OFFICIAL_URLS)
        + collect_agencia_brasil(args.agencia_brasil_pages)
        + collect_rss_rows()
    ):
        key = normalize(row["Texto"])
        if key not in seen:
            rows.append(row)
            seen.add(key)
    write_sources(args.sources_output, rows)
    write_dataset(args.dataset, merge_rows(args.dataset, rows))

    print(f"Coletados {len(rows)} exemplos True oficiais.")
    print(f"Dataset atualizado em {args.dataset}.")
    print(f"Fontes salvas em {args.sources_output}.")


if __name__ == "__main__":
    main()

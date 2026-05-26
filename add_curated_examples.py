import argparse
import csv
import os
import unicodedata

from src.data_io import read_dataset, write_dataset


CURATED_EXAMPLES = [
    ("Lula foi preso.", "True", "CNN Brasil", "https://www.cnnbrasil.com.br/politica/lula-faz-cerimonia-para-lembrar-5-anos-da-saida-da-prisao/"),
    ("Lula já foi preso.", "True", "CNN Brasil", "https://www.cnnbrasil.com.br/politica/lula-faz-cerimonia-para-lembrar-5-anos-da-saida-da-prisao/"),
    ("Lula foi preso em 2018.", "True", "CNN Brasil", "https://www.cnnbrasil.com.br/politica/lula-faz-cerimonia-para-lembrar-5-anos-da-saida-da-prisao/"),
    ("Luiz Inácio Lula da Silva foi preso em 2018.", "True", "CNN Brasil", "https://www.cnnbrasil.com.br/politica/lula-faz-cerimonia-para-lembrar-5-anos-da-saida-da-prisao/"),
    ("Lula ficou preso em Curitiba.", "True", "CNN Brasil", "https://www.cnnbrasil.com.br/politica/lula-faz-cerimonia-para-lembrar-5-anos-da-saida-da-prisao/"),
    ("Lula ficou preso por 580 dias.", "True", "CNN Brasil", "https://www.cnnbrasil.com.br/politica/lula-faz-cerimonia-para-lembrar-5-anos-da-saida-da-prisao/"),
    ("Lula foi solto em 2019.", "True", "CNN Brasil", "https://www.cnnbrasil.com.br/politica/lula-faz-cerimonia-para-lembrar-5-anos-da-saida-da-prisao/"),
    ("Lula foi solto em novembro de 2019.", "True", "CNN Brasil", "https://www.cnnbrasil.com.br/politica/lula-faz-cerimonia-para-lembrar-5-anos-da-saida-da-prisao/"),
    ("Lula não está preso atualmente.", "True", "Planalto", "https://www.gov.br/sri/pt-br/presidente-lula-recebe-a-confederacao-nacional-dos-municipios"),
    ("Lula está solto atualmente.", "True", "Planalto", "https://www.gov.br/sri/pt-br/presidente-lula-recebe-a-confederacao-nacional-dos-municipios"),
    ("Lula exerce a Presidência da República em 2026.", "True", "Planalto", "https://www.gov.br/sri/pt-br/presidente-lula-recebe-a-confederacao-nacional-dos-municipios"),
    ("Lula é presidente do Brasil em 2026.", "True", "Planalto", "https://www.gov.br/sri/pt-br/presidente-lula-recebe-a-confederacao-nacional-dos-municipios"),
    ("As condenações de Lula na Lava Jato foram anuladas pelo STF.", "True", "Agência Brasil", "https://agenciabrasil.ebc.com.br/justica/noticia/2021-04/stf-mantem-anulacao-das-condenacoes-de-lula"),
    ("O STF anulou as condenações de Lula na Lava Jato.", "True", "Agência Brasil", "https://agenciabrasil.ebc.com.br/justica/noticia/2021-03/fachin-anula-condenacoes-de-lula-na-lava-jato"),
    ("Lula teve as condenações anuladas pelo STF.", "True", "Agência Brasil", "https://agenciabrasil.ebc.com.br/justica/noticia/2021-04/stf-mantem-anulacao-das-condenacoes-de-lula"),
    ("Lula recuperou os direitos políticos após a anulação das condenações.", "True", "Agência Brasil", "https://agenciabrasil.ebc.com.br/justica/noticia/2021-04/stf-mantem-anulacao-das-condenacoes-de-lula"),
    ("O Supremo Tribunal Federal fica em Brasília.", "True", "STF", "https://portal.stf.jus.br/"),
    ("O STF fica em Brasília.", "True", "STF", "https://portal.stf.jus.br/"),
    ("O STF está localizado em Brasília.", "True", "STF", "https://portal.stf.jus.br/"),
    ("O Brasil tem eleições presidenciais.", "True", "TSE", "https://www.tse.jus.br/eleicoes"),
    ("No Brasil há eleições presidenciais.", "True", "TSE", "https://www.tse.jus.br/eleicoes"),
    ("O Brasil realiza eleição presidencial.", "True", "TSE", "https://www.tse.jus.br/eleicoes"),
    ("O presidente do Brasil é escolhido por eleição.", "True", "TSE", "https://www.tse.jus.br/eleicoes"),
    ("O TSE organiza as eleições no Brasil.", "True", "TSE", "https://www.tse.jus.br/"),
    ("A Justiça Eleitoral organiza as eleições.", "True", "TSE", "https://www.tse.jus.br/"),
    ("A votação no Brasil usa urna eletrônica.", "True", "TSE", "https://www.tse.jus.br/eleicoes/urna-eletronica"),
    ("Lula está preso.", "Fake", "Planalto", "https://www.gov.br/sri/pt-br/presidente-lula-recebe-a-confederacao-nacional-dos-municipios"),
    ("Lula está preso atualmente.", "Fake", "Planalto", "https://www.gov.br/sri/pt-br/presidente-lula-recebe-a-confederacao-nacional-dos-municipios"),
    ("Lula continua preso.", "Fake", "CNN Brasil", "https://www.cnnbrasil.com.br/politica/lula-faz-cerimonia-para-lembrar-5-anos-da-saida-da-prisao/"),
    ("Lula está na cadeia.", "Fake", "Planalto", "https://www.gov.br/sri/pt-br/presidente-lula-recebe-a-confederacao-nacional-dos-municipios"),
    ("Lula está detido atualmente.", "Fake", "Planalto", "https://www.gov.br/sri/pt-br/presidente-lula-recebe-a-confederacao-nacional-dos-municipios"),
    ("Lula foi preso em 2026.", "Fake", "Planalto", "https://www.gov.br/sri/pt-br/presidente-lula-recebe-a-confederacao-nacional-dos-municipios"),
    ("Lula foi preso preventivamente em Brasília.", "Fake", "Planalto", "https://www.gov.br/sri/pt-br/presidente-lula-recebe-a-confederacao-nacional-dos-municipios"),
    ("Lula foi preso pelo STF em Brasília.", "Fake", "Planalto", "https://www.gov.br/sri/pt-br/presidente-lula-recebe-a-confederacao-nacional-dos-municipios"),
    ("Lula nunca foi preso.", "Fake", "CNN Brasil", "https://www.cnnbrasil.com.br/politica/lula-faz-cerimonia-para-lembrar-5-anos-da-saida-da-prisao/"),
    ("Lula não foi preso em 2018.", "Fake", "CNN Brasil", "https://www.cnnbrasil.com.br/politica/lula-faz-cerimonia-para-lembrar-5-anos-da-saida-da-prisao/"),
    ("Lula ainda cumpre pena em Curitiba.", "Fake", "CNN Brasil", "https://www.cnnbrasil.com.br/politica/lula-faz-cerimonia-para-lembrar-5-anos-da-saida-da-prisao/"),
    ("Lula foi declarado culpado pelo STF em 2021.", "Fake", "Agência Brasil", "https://agenciabrasil.ebc.com.br/justica/noticia/2021-04/stf-mantem-anulacao-das-condenacoes-de-lula"),
    ("O STF fica no Rio de Janeiro.", "Fake", "STF", "https://portal.stf.jus.br/"),
    ("O STF fica em São Paulo.", "Fake", "STF", "https://portal.stf.jus.br/"),
    ("O Brasil não tem eleições presidenciais.", "Fake", "TSE", "https://www.tse.jus.br/eleicoes"),
    ("O presidente do Brasil não é escolhido por eleição.", "Fake", "TSE", "https://www.tse.jus.br/eleicoes"),
]


def normalize(text):
    normalized = unicodedata.normalize("NFKD", text.lower())
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(without_accents.split())


def curated_rows():
    return [
        {"Texto": text, "Label": label, "Fonte": source, "URL": url}
        for text, label, source, url in CURATED_EXAMPLES
    ]


def merge_examples(dataset_path):
    texts, labels = read_dataset(dataset_path)
    rows = [{"Texto": text, "Label": label} for text, label in zip(texts, labels)]
    seen = {(normalize(row["Texto"]), row["Label"]) for row in rows}
    added = 0

    for row in curated_rows():
        key = (normalize(row["Texto"]), row["Label"])
        if key not in seen:
            rows.append({"Texto": row["Texto"], "Label": row["Label"]})
            seen.add(key)
            added += 1

    return rows, added


def write_sources(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["Texto", "Label", "Fonte", "URL"])
        writer.writeheader()
        writer.writerows(curated_rows())


def main():
    parser = argparse.ArgumentParser(description="Adiciona exemplos curados e rastreáveis ao dataset.")
    parser.add_argument("--dataset", default="data/dataset.csv")
    parser.add_argument("--sources-output", default="data/curated_examples_sources.csv")
    args = parser.parse_args()

    rows, added = merge_examples(args.dataset)
    write_dataset(args.dataset, rows)
    write_sources(args.sources_output)

    print(f"Exemplos curados adicionados: {added}.")
    print(f"Dataset atualizado em {args.dataset}.")
    print(f"Fontes salvas em {args.sources_output}.")


if __name__ == "__main__":
    main()

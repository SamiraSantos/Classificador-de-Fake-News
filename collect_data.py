import argparse
import csv
import glob
import os
import shutil
import unicodedata
from datetime import datetime

from src.data_io import read_dataset, write_dataset


KEYWORDS = [
    "eleicao",
    "urna",
    "voto",
    "Bolsonaro",
    "Lula",
    "TSE",
    "fraude eleitoral",
    "eleicao 2022",
    "eleicoes 2024",
    "urna eletronica",
    "voto impresso",
    "apuracao votos",
    "boletim de urna",
    "TSE fraude",
    "TSE urna",
    "Bolsonaro eleicao",
    "Lula eleicao",
    "PT eleicao",
    "campanha eleitoral",
    "voto em branco",
    "voto nulo",
    "voto em transito",
    "titulo de eleitor",
    "e-Titulo",
    "pesquisa eleitoral",
    "justica eleitoral",
    "desinformacao eleitoral",
    "compra de votos",
    "mesario eleicao",
    "politica",
    "politico",
    "governo",
    "presidente",
    "deputado",
    "senador",
    "camara dos deputados",
    "senado",
    "congresso nacional",
    "STF",
    "supremo tribunal federal",
    "Alexandre de Moraes",
    "Bolsonaro preso",
    "Bolsonaro prisao",
    "prisao Bolsonaro",
    "Bolsonaro STF",
    "Bolsonaro tornozeleira",
    "Bolsonaro condenacao",
    "Lula governo",
    "Lula corrupcao",
    "Moraes Bolsonaro",
    "Flavio Dino",
    "Sergio Moro",
    "Michelle Bolsonaro",
    "Eduardo Bolsonaro",
    "Flavio Bolsonaro",
    "Carlos Bolsonaro",
    "Nikolas Ferreira",
    "Pablo Marcal",
    "Guilherme Boulos",
    "Tabata Amaral",
    "Tarcisio de Freitas",
    "Fernando Haddad",
    "Jair Bolsonaro",
    "Luiz Inacio Lula da Silva",
]

FALSE_TERMS = (
    "fake",
    "falso",
    "falsa",
    "false",
    "enganoso",
    "enganosa",
    "enganador",
    "distorcido",
    "distorcida",
    "errado",
    "errada",
    "sem contexto",
    "fora de contexto",
    "impreciso",
    "imprecisa",
    "exagerado",
    "exagerada",
    "esticado",
    "esticada",
    "insustentavel",
    "insustentável",
    "nao e bem assim",
    "não é bem assim",
    "nao_e_bem_assim",
    "não_é_bem_assim",
    "nao e verdade",
    "não é verdade",
    "boato",
    "mentira",
    "montagem",
    "sem registro",
    "sem provas",
    "incorreto",
    "incorreta",
)
TRUE_TERMS = (
    "verdadeiro",
    "verdadeira",
    "true",
    "correto",
    "correta",
    "comprovado",
    "comprovada",
    "confirmado",
    "confirmada",
    "certo",
    "certa",
)


def normalize_text(value):
    normalized = unicodedata.normalize("NFKD", (value or "").lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return normalized.replace("_", " ")


def slugify(value):
    normalized = normalize_text(value)
    keep = [char if char.isalnum() else "_" for char in normalized]
    return "_".join("".join(keep).split("_")).strip("_")


def infer_label(value):
    normalized = normalize_text(value)
    if any(term in normalized for term in FALSE_TERMS):
        return "Fake"
    if any(term in normalized for term in TRUE_TERMS):
        return "True"
    return None


def first_available(row, candidates):
    for candidate in candidates:
        value = row.get(candidate)
        if value:
            return value.strip()
    return ""


def extract_true_statement_from_verdict(verdict):
    verdict = (verdict or "").strip()
    normalized = normalize_text(verdict)

    if ":" in verdict:
        prefix, statement = verdict.split(":", 1)
        normalized_prefix = normalize_text(prefix)
        if any(
            term in normalized_prefix
            for term in [
                "falso",
                "enganoso",
                "distorcido",
                "errado",
                "contextualizando",
                "satira",
                "sem contexto",
                "fora de contexto",
            ]
        ):
            statement = statement.strip()
            if 50 <= len(statement) <= 350:
                return statement

    # Alguns verificadores retornam uma explicacao diretamente, sem rotulo curto.
    if infer_label(verdict) is None and 50 <= len(verdict) <= 350:
        return verdict

    return None


def collect_with_factcheckexplorer(output_dir, num_results, max_pages, max_keywords):
    from factcheckexplorer import FactCheckLib

    os.makedirs(output_dir, exist_ok=True)
    created_files = []

    for keyword in KEYWORDS[:max_keywords]:
        safe_keyword = slugify(keyword)
        for page in range(max_pages):
            offset = page * num_results
            csv_filename = os.path.join(output_dir, f"factcheck_{safe_keyword}_{offset}.csv")
            fact_check = FactCheckLib(
                query=keyword,
                language="pt",
                num_results=num_results,
                csv_filename=csv_filename,
            )
            fact_check.params["offset"] = str(offset)
            try:
                fact_check.process()
            except Exception as error:
                print(f"Aviso: falha na busca '{keyword}' offset {offset}: {error}")
                continue
            if os.path.exists(csv_filename):
                created_files.append(csv_filename)

    # Algumas versoes da biblioteca gravam em nome automatico no diretorio atual.
    for csv_file in glob.glob("*.csv"):
        if csv_file not in created_files and csv_file.startswith("factcheck"):
            target = os.path.join(output_dir, os.path.basename(csv_file))
            shutil.move(csv_file, target)
            created_files.append(target)

    return created_files


def build_dataset_from_raw(raw_files):
    rows = []
    source_rows = []
    seen = set()

    text_fields = ["claim", "Claim", "text", "Text", "title", "Title", "claimReview", "review"]
    label_fields = [
        "rating",
        "Rating",
        "textualRating",
        "Textual Rating",
        "reviewRating",
        "label",
        "Verdict",
    ]

    for raw_file in raw_files:
        with open(raw_file, "r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            for raw_row in reader:
                text = first_available(raw_row, text_fields)
                rating = first_available(raw_row, label_fields)
                label = infer_label(rating)
                key = " ".join(text.lower().split())
                if text and label and key not in seen:
                    rows.append({"Texto": text, "Label": label})
                    source_rows.append(
                        {
                            "Texto": text,
                            "Label": label,
                            "Tipo": "claim",
                            "Veredito original": rating,
                            "Fonte": first_available(raw_row, ["Source Name", "source", "Source"]),
                            "URL": first_available(raw_row, ["Source URL", "url", "URL"]),
                            "Data": first_available(
                                raw_row,
                                ["Review Publication Date", "date", "Date", "publishedDate"],
                            ),
                            "Arquivo bruto": raw_file,
                        }
                    )
                    seen.add(key)

                true_statement = extract_true_statement_from_verdict(rating)
                true_key = " ".join((true_statement or "").lower().split())
                if true_statement and true_key not in seen:
                    rows.append({"Texto": true_statement, "Label": "True"})
                    source_rows.append(
                        {
                            "Texto": true_statement,
                            "Label": "True",
                            "Tipo": "verdict_correction",
                            "Veredito original": rating,
                            "Fonte": first_available(raw_row, ["Source Name", "source", "Source"]),
                            "URL": first_available(raw_row, ["Source URL", "url", "URL"]),
                            "Data": first_available(
                                raw_row,
                                ["Review Publication Date", "date", "Date", "publishedDate"],
                            ),
                            "Arquivo bruto": raw_file,
                        }
                    )
                    seen.add(true_key)

    return rows, source_rows


def read_seed_rows(path):
    if not path or not os.path.exists(path):
        return []

    texts, labels = read_dataset(path)
    return [{"Texto": text, "Label": label} for text, label in zip(texts, labels)]


def merge_rows(seed_rows, collected_rows):
    rows = []
    seen = set()

    for row in seed_rows + collected_rows:
        text = row["Texto"].strip()
        label = row["Label"].strip()
        key = " ".join(text.lower().split())
        if text and label in {"Fake", "True"} and key not in seen:
            rows.append({"Texto": text, "Label": label})
            seen.add(key)

    return rows


def write_source_dataset(path, rows):
    if not rows:
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Coleta dados eleitorais via factcheckexplorer.")
    parser.add_argument("--output", default="data/dataset.csv", help="CSV final do dataset.")
    parser.add_argument("--seed", default="", help="CSV manual/base opcional para manter no dataset.")
    parser.add_argument(
        "--sources-output",
        default="data/factcheck_sources.csv",
        help="CSV com veredito e fonte originais das checagens.",
    )
    parser.add_argument("--raw-dir", default="data/raw", help="Diretorio para CSVs brutos.")
    parser.add_argument("--num-results", type=int, default=100, help="Resultados por palavra-chave.")
    parser.add_argument("--max-pages", type=int, default=10, help="Paginas de resultados por palavra-chave.")
    parser.add_argument(
        "--max-keywords",
        type=int,
        default=len(KEYWORDS),
        help="Quantidade de palavras-chave usadas, na ordem da lista KEYWORDS.",
    )
    args = parser.parse_args()

    print(f"Iniciando coleta em {datetime.now().isoformat(timespec='seconds')}")
    raw_files = collect_with_factcheckexplorer(
        args.raw_dir,
        args.num_results,
        args.max_pages,
        args.max_keywords,
    )
    raw_files = sorted(set(raw_files + glob.glob(os.path.join(args.raw_dir, "*.csv"))))
    collected_rows, source_rows = build_dataset_from_raw(raw_files)
    rows = merge_rows(read_seed_rows(args.seed), collected_rows)

    if not collected_rows:
        raise RuntimeError(
            "Nenhuma linha rotulada foi criada. Verifique os CSVs brutos e ajuste os nomes das colunas."
        )

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    write_dataset(args.output, rows)
    write_source_dataset(args.sources_output, source_rows)
    print(f"Coleta gerou {len(collected_rows)} exemplos rotulados.")
    print(f"Dataset salvo em {args.output} com {len(rows)} exemplos no total.")
    print(f"Fontes salvas em {args.sources_output}.")


if __name__ == "__main__":
    main()

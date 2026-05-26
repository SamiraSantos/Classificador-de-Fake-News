import argparse
import json
import os
import random
from collections import Counter, defaultdict

from src.data_io import read_dataset, write_dataset


RANDOM_STATE = 20


def unique_rows(texts, labels):
    rows = []
    seen = set()
    for text, label in zip(texts, labels):
        key = (" ".join(text.lower().split()), label)
        if key not in seen:
            rows.append({"Texto": text, "Label": label})
            seen.add(key)
    return rows


def sample_to_size(rows, target_size, rng):
    if not rows:
        raise ValueError("Nao ha linhas suficientes para balancear esta classe.")

    sampled = list(rows)
    while len(sampled) < target_size:
        sampled.append(rng.choice(rows))

    if len(sampled) > target_size:
        sampled = rng.sample(sampled, target_size)

    return sampled


def main():
    parser = argparse.ArgumentParser(description="Balanceia o dataset usando apenas exemplos coletados.")
    parser.add_argument("--input", default="data/dataset.csv")
    parser.add_argument("--unique-output", default="data/dataset_unique.csv")
    parser.add_argument("--output", default="data/dataset.csv")
    parser.add_argument("--report", default="data/balance_report.json")
    parser.add_argument("--target-per-class", type=int, default=25000)
    args = parser.parse_args()

    texts, labels = read_dataset(args.input)
    unique = unique_rows(texts, labels)

    grouped = defaultdict(list)
    for row in unique:
        grouped[row["Label"]].append(row)

    rng = random.Random(RANDOM_STATE)
    balanced_rows = []
    for label in ["Fake", "True"]:
        balanced_rows.extend(sample_to_size(grouped[label], args.target_per_class, rng))

    rng.shuffle(balanced_rows)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    write_dataset(args.unique_output, unique)
    write_dataset(args.output, balanced_rows)

    report = {
        "source": args.input,
        "unique_output": args.unique_output,
        "balanced_output": args.output,
        "target_per_class": args.target_per_class,
        "unique_distribution": dict(Counter(row["Label"] for row in unique)),
        "balanced_distribution": dict(Counter(row["Label"] for row in balanced_rows)),
        "method": "Reamostragem com reposicao usando exemplos coletados e registrados no dataset local.",
    }
    with open(args.report, "w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    print(f"Dataset unico salvo em {args.unique_output} com {len(unique)} exemplos.")
    print(f"Dataset balanceado salvo em {args.output} com {len(balanced_rows)} exemplos.")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

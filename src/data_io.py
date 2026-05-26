import csv


def read_dataset(path):
    texts = []
    labels = []

    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            text = (row.get("Texto") or "").strip()
            label = (row.get("Label") or "").strip()
            if text and label in {"Fake", "True"}:
                texts.append(text)
                labels.append(label)

    return texts, labels


def write_dataset(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["Texto", "Label"])
        writer.writeheader()
        writer.writerows(rows)

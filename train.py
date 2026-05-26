import argparse
import json
import os
import random
from collections import Counter, defaultdict

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.data_io import read_dataset


LABELS = ["Fake", "True"]
MIN_CONFIDENCE = 0.95
MIN_SIMILARITY = 0.35
RANDOM_STATE = 20


def unique_rows(texts, labels):
    unique_texts = []
    unique_labels = []
    seen = set()
    for text, label in zip(texts, labels):
        key = (" ".join(text.lower().split()), label)
        if key not in seen:
            unique_texts.append(text)
            unique_labels.append(label)
            seen.add(key)
    return unique_texts, unique_labels


def balance_training_data(texts, labels):
    grouped = defaultdict(list)
    for text, label in zip(texts, labels):
        grouped[label].append(text)

    target_size = max(len(values) for values in grouped.values())
    rng = random.Random(RANDOM_STATE)
    balanced_rows = []

    for label, class_texts in grouped.items():
        sampled = list(class_texts)
        while len(sampled) < target_size:
            sampled.append(rng.choice(class_texts))
        balanced_rows.extend((text, label) for text in sampled)

    rng.shuffle(balanced_rows)
    return [text for text, _ in balanced_rows], [label for _, label in balanced_rows]


def build_pipeline():
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",
                    lowercase=True,
                    ngram_range=(3, 6),
                    strip_accents="unicode",
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=4,
                    class_weight="balanced",
                    max_iter=5000,
                    random_state=RANDOM_STATE,
                    solver="liblinear",
                ),
            ),
        ]
    )


def confident_metrics(model, texts, labels, evidence_texts):
    from sklearn.metrics.pairwise import cosine_similarity

    predictions = model.predict(texts)
    probabilities = model.predict_proba(texts)
    vectorizer = model.named_steps["tfidf"]
    evidence_matrix = vectorizer.transform(evidence_texts)
    text_matrix = vectorizer.transform(texts)
    similarities = cosine_similarity(text_matrix, evidence_matrix).max(axis=1)

    accepted_indexes = [
        index
        for index, probability in enumerate(probabilities)
        if max(probability) >= MIN_CONFIDENCE and similarities[index] >= MIN_SIMILARITY
    ]
    if not accepted_indexes:
        return {
            "minimum_confidence": MIN_CONFIDENCE,
            "minimum_similarity": MIN_SIMILARITY,
            "accepted_predictions": 0,
            "coverage": 0.0,
            "accuracy_on_accepted_predictions": 0.0,
        }

    accepted_labels = [labels[index] for index in accepted_indexes]
    accepted_predictions = [predictions[index] for index in accepted_indexes]
    return {
        "minimum_confidence": MIN_CONFIDENCE,
        "minimum_similarity": MIN_SIMILARITY,
        "accepted_predictions": len(accepted_indexes),
        "coverage": len(accepted_indexes) / len(labels),
        "accuracy_on_accepted_predictions": accuracy_score(accepted_labels, accepted_predictions),
    }


def main():
    parser = argparse.ArgumentParser(description="Treina o classificador de Fake News.")
    parser.add_argument("--dataset", default="data/dataset.csv")
    parser.add_argument("--model", default="models/logistic_regression_model.joblib")
    parser.add_argument("--metrics", default="models/metrics.json")
    args = parser.parse_args()

    texts, labels = read_dataset(args.dataset)
    unique_texts, unique_labels = unique_rows(texts, labels)
    if len(set(unique_labels)) < 2:
        raise ValueError("O dataset precisa ter exemplos das classes Fake e True.")

    train_texts, test_texts, train_labels, test_labels = train_test_split(
        unique_texts,
        unique_labels,
        test_size=0.25,
        random_state=RANDOM_STATE,
        stratify=unique_labels,
    )
    balanced_train_texts, balanced_train_labels = balance_training_data(train_texts, train_labels)

    evaluation_model = build_pipeline()
    evaluation_model.fit(balanced_train_texts, balanced_train_labels)
    predictions = evaluation_model.predict(test_texts)

    precision, recall, f1, support = precision_recall_fscore_support(
        test_labels,
        predictions,
        labels=LABELS,
        zero_division=0,
    )
    results = {
        "algorithm": "TF-IDF + Logistic Regression",
        "dataset_size": len(texts),
        "unique_dataset_size": len(unique_texts),
        "class_distribution": {
            "Fake": labels.count("Fake"),
            "True": labels.count("True"),
        },
        "unique_class_distribution": dict(Counter(unique_labels)),
        "train_size": len(train_texts),
        "balanced_train_size": len(balanced_train_texts),
        "test_size": len(test_texts),
        "accuracy": accuracy_score(test_labels, predictions),
        "precision": dict(zip(LABELS, precision)),
        "recall": dict(zip(LABELS, recall)),
        "f1_score": dict(zip(LABELS, f1)),
        "support": dict(zip(LABELS, [int(value) for value in support])),
        "labels": LABELS,
        "confusion_matrix": confusion_matrix(test_labels, predictions, labels=LABELS).tolist(),
        "classification_report": classification_report(
            test_labels,
            predictions,
            labels=LABELS,
            zero_division=0,
            output_dict=True,
        ),
        "confidence_filter": confident_metrics(
            evaluation_model,
            test_texts,
            test_labels,
            train_texts,
        ),
    }

    final_model = build_pipeline()
    final_model.fit(texts, labels)

    os.makedirs(os.path.dirname(args.model), exist_ok=True)
    joblib.dump(final_model, args.model)
    with open(args.metrics, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)

    print("Treinamento concluido.")
    print(f"Modelo salvo em: {args.model}")
    print(f"Metricas salvas em: {args.metrics}")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

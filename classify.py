import argparse
import re
import unicodedata

import joblib
from sklearn.metrics.pairwise import cosine_similarity

from src.data_io import read_dataset


DEFAULT_MODEL_PATH = "models/logistic_regression_model.joblib"
DEFAULT_DATASET_PATH = "data/dataset.csv"
DEFAULT_MIN_CONFIDENCE = 0.95
DEFAULT_MIN_SIMILARITY = 0.35
DEFAULT_STRONG_MATCH_SIMILARITY = 0.75
AMBIGUOUS_INCONCLUSIVE_TERMS = (
    ("lula", "inocent"),
    ("lula", "absolv"),
)


def normalize_text(text):
    normalized = unicodedata.normalize("NFKD", text.lower())
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", without_accents).split())


def is_ambiguous_claim(text):
    normalized = normalize_text(text)
    return any(all(term in normalized for term in terms) for terms in AMBIGUOUS_INCONCLUSIVE_TERMS)


def build_dataset_index(model, dataset_path):
    texts, labels = read_dataset(dataset_path)
    vectorizer = model.named_steps["tfidf"]
    dataset_matrix = vectorizer.transform(texts)
    label_by_normalized_text = {}
    text_by_normalized_text = {}
    conflicts = set()

    for text, label in zip(texts, labels):
        key = normalize_text(text)
        if key in label_by_normalized_text and label_by_normalized_text[key] != label:
            conflicts.add(key)
        else:
            label_by_normalized_text[key] = label
            text_by_normalized_text[key] = text

    for key in conflicts:
        label_by_normalized_text.pop(key, None)
        text_by_normalized_text.pop(key, None)

    return {
        "texts": texts,
        "labels": labels,
        "matrix": dataset_matrix,
        "label_by_normalized_text": label_by_normalized_text,
        "text_by_normalized_text": text_by_normalized_text,
    }


def nearest_dataset_example(model, dataset_path, text, dataset_index=None):
    if dataset_index is None:
        dataset_index = build_dataset_index(model, dataset_path)

    texts = dataset_index["texts"]
    labels = dataset_index["labels"]
    dataset_matrix = dataset_index["matrix"]
    vectorizer = model.named_steps["tfidf"]
    text_vector = vectorizer.transform([text])
    similarities = cosine_similarity(text_vector, dataset_matrix).ravel()
    best_index = similarities.argmax()
    return similarities[best_index], texts[best_index], labels[best_index]


def classify_text(
    text,
    model,
    dataset_path=DEFAULT_DATASET_PATH,
    dataset_index=None,
    min_confidence=DEFAULT_MIN_CONFIDENCE,
    min_similarity=DEFAULT_MIN_SIMILARITY,
    strong_match_similarity=DEFAULT_STRONG_MATCH_SIMILARITY,
):
    if is_ambiguous_claim(text):
        return {
            "label": "Inconclusiva",
            "confidence": 0.0,
            "display_confidence": 0.0,
            "similarity": 0.0,
            "model_label": "Inconclusiva",
            "nearest_label": "Inconclusiva",
            "nearest_text": "",
            "decision": "ambiguous_claim",
        }

    if dataset_index is None:
        dataset_index = build_dataset_index(model, dataset_path)

    normalized_text = normalize_text(text)
    direct_label = dataset_index["label_by_normalized_text"].get(normalized_text)
    if direct_label:
        return {
            "label": direct_label,
            "confidence": 1.0,
            "display_confidence": 1.0,
            "similarity": 1.0,
            "model_label": direct_label,
            "nearest_label": direct_label,
            "nearest_text": dataset_index["text_by_normalized_text"].get(normalized_text, text),
            "decision": "direct_dataset_match",
        }

    probabilities = dict(zip(model.classes_, model.predict_proba([text])[0]))
    model_label = max(probabilities, key=probabilities.get)
    confidence = float(probabilities[model_label])
    similarity, nearest_text, nearest_label = nearest_dataset_example(
        model,
        dataset_path,
        text,
        dataset_index=dataset_index,
    )

    label = "Inconclusiva"
    decision = "low_confidence_or_similarity"

    if similarity >= strong_match_similarity:
        label = nearest_label
        decision = "nearest_dataset_match"
    elif confidence >= min_confidence and similarity >= min_similarity:
        label = model_label
        decision = "model_confidence"

    if label == "Inconclusiva":
        display_confidence = min(confidence, float(similarity))
    elif decision == "nearest_dataset_match":
        display_confidence = max(confidence, float(similarity))
    else:
        display_confidence = confidence

    return {
        "label": label,
        "confidence": confidence,
        "display_confidence": float(display_confidence),
        "similarity": float(similarity),
        "model_label": model_label,
        "nearest_label": nearest_label,
        "nearest_text": nearest_text,
        "decision": decision,
    }


def main():
    parser = argparse.ArgumentParser(description="Classifica uma afirmação como Fake ou True.")
    parser.add_argument("texto", nargs="?", help="Afirmação ou notícia a ser classificada.")
    parser.add_argument("--model", default=DEFAULT_MODEL_PATH)
    parser.add_argument("--dataset", default=DEFAULT_DATASET_PATH)
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=DEFAULT_MIN_CONFIDENCE,
        help="Confiança mínima para aceitar a classificação.",
    )
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=DEFAULT_MIN_SIMILARITY,
        help="Similaridade minima com algum exemplo do dataset local.",
    )
    parser.add_argument(
        "--strong-match-similarity",
        type=float,
        default=DEFAULT_STRONG_MATCH_SIMILARITY,
        help="Similaridade para aceitar diretamente o rotulo do exemplo mais proximo.",
    )
    args = parser.parse_args()

    text = args.texto or input("Digite a afirmação/notícia: ").strip()
    model = joblib.load(args.model)
    dataset_index = build_dataset_index(model, args.dataset)
    result = classify_text(
        text,
        model,
        dataset_path=args.dataset,
        dataset_index=dataset_index,
        min_confidence=args.min_confidence,
        min_similarity=args.min_similarity,
        strong_match_similarity=args.strong_match_similarity,
    )

    print(f"Classificacao: {result['label']}")


if __name__ == "__main__":
    main()

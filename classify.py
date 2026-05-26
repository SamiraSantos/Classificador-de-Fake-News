import argparse

import joblib
from sklearn.metrics.pairwise import cosine_similarity

from src.data_io import read_dataset


DEFAULT_MODEL_PATH = "models/logistic_regression_model.joblib"
DEFAULT_DATASET_PATH = "data/dataset.csv"
DEFAULT_MIN_CONFIDENCE = 0.95
DEFAULT_MIN_SIMILARITY = 0.35
DEFAULT_STRONG_MATCH_SIMILARITY = 0.75


def build_dataset_index(model, dataset_path):
    texts, labels = read_dataset(dataset_path)
    vectorizer = model.named_steps["tfidf"]
    dataset_matrix = vectorizer.transform(texts)
    return {
        "texts": texts,
        "labels": labels,
        "matrix": dataset_matrix,
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

import json
import math
from collections import Counter, defaultdict

from .text_utils import tokenize


class MultinomialNaiveBayes:
    def __init__(self, alpha=1.0):
        self.alpha = alpha
        self.labels = []
        self.vocabulary = []
        self.class_doc_counts = Counter()
        self.class_token_counts = defaultdict(Counter)
        self.class_total_tokens = Counter()
        self.total_docs = 0

    def fit(self, texts, labels):
        self.labels = sorted(set(labels))
        self.total_docs = len(texts)

        vocabulary = set()
        for text, label in zip(texts, labels):
            tokens = tokenize(text)
            self.class_doc_counts[label] += 1
            self.class_token_counts[label].update(tokens)
            self.class_total_tokens[label] += len(tokens)
            vocabulary.update(tokens)

        self.vocabulary = sorted(vocabulary)
        return self

    def predict_one(self, text):
        scores = self.predict_proba_one(text)
        return max(scores, key=scores.get)

    def predict(self, texts):
        return [self.predict_one(text) for text in texts]

    def predict_proba_one(self, text):
        if not self.labels:
            raise ValueError("Modelo ainda nao foi treinado.")

        tokens = tokenize(text)
        vocab_size = max(len(self.vocabulary), 1)
        log_scores = {}

        for label in self.labels:
            prior = (self.class_doc_counts[label] + self.alpha) / (
                self.total_docs + self.alpha * len(self.labels)
            )
            score = math.log(prior)
            denominator = self.class_total_tokens[label] + self.alpha * vocab_size

            for token in tokens:
                token_count = self.class_token_counts[label][token]
                likelihood = (token_count + self.alpha) / denominator
                score += math.log(likelihood)

            log_scores[label] = score

        return self._softmax(log_scores)

    def save(self, path):
        data = {
            "alpha": self.alpha,
            "labels": self.labels,
            "vocabulary": self.vocabulary,
            "class_doc_counts": dict(self.class_doc_counts),
            "class_token_counts": {
                label: dict(counter) for label, counter in self.class_token_counts.items()
            },
            "class_total_tokens": dict(self.class_total_tokens),
            "total_docs": self.total_docs,
        }
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        model = cls(alpha=data["alpha"])
        model.labels = data["labels"]
        model.vocabulary = data["vocabulary"]
        model.class_doc_counts = Counter(data["class_doc_counts"])
        model.class_token_counts = defaultdict(Counter)
        for label, counter in data["class_token_counts"].items():
            model.class_token_counts[label] = Counter(counter)
        model.class_total_tokens = Counter(data["class_total_tokens"])
        model.total_docs = data["total_docs"]
        return model

    @staticmethod
    def _softmax(log_scores):
        max_score = max(log_scores.values())
        exp_scores = {
            label: math.exp(score - max_score) for label, score in log_scores.items()
        }
        total = sum(exp_scores.values())
        return {label: score / total for label, score in exp_scores.items()}

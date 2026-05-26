from collections import Counter


def accuracy_score(y_true, y_pred):
    correct = sum(1 for truth, pred in zip(y_true, y_pred) if truth == pred)
    return correct / len(y_true) if y_true else 0.0


def precision_recall_f1(y_true, y_pred, positive_label="Fake"):
    true_positive = sum(
        1
        for truth, pred in zip(y_true, y_pred)
        if truth == positive_label and pred == positive_label
    )
    false_positive = sum(
        1
        for truth, pred in zip(y_true, y_pred)
        if truth != positive_label and pred == positive_label
    )
    false_negative = sum(
        1
        for truth, pred in zip(y_true, y_pred)
        if truth == positive_label and pred != positive_label
    )

    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def confusion_matrix(y_true, y_pred, labels):
    matrix = {truth: Counter() for truth in labels}
    for truth, pred in zip(y_true, y_pred):
        matrix[truth][pred] += 1
    return [[matrix[truth][pred] for pred in labels] for truth in labels]

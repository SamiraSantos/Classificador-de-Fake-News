import re
import unicodedata


STOPWORDS = {
    "a",
    "ao",
    "aos",
    "as",
    "com",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "na",
    "nas",
    "no",
    "nos",
    "o",
    "os",
    "para",
    "por",
    "que",
    "sem",
    "um",
    "uma",
}


def normalize_text(text):
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text


def tokenize(text):
    normalized = normalize_text(text)
    tokens = re.findall(r"[a-z0-9]+", normalized)
    words = [token for token in tokens if len(token) > 1 and token not in STOPWORDS]
    bigrams = [f"{words[index]}_{words[index + 1]}" for index in range(len(words) - 1)]
    return words + bigrams

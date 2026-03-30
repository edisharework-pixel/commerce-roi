from difflib import SequenceMatcher


def compute_similarity(name_a: str, name_b: str) -> float:
    if name_a == name_b:
        return 1.0
    if not name_a or not name_b:
        return 0.0
    tokens_a = set(name_a.split())
    tokens_b = set(name_b.split())
    if not tokens_a or not tokens_b:
        return 0.0
    jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
    seq_ratio = SequenceMatcher(None, name_a, name_b).ratio()
    return (jaccard + seq_ratio) / 2

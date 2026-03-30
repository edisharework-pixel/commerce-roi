from app.matching.similarity import compute_similarity


def test_exact_match():
    assert compute_similarity("바디트리머 프로", "바디트리머 프로") == 1.0


def test_high_similarity():
    score = compute_similarity("바디트리머 프로 남성용", "바디트리머 프로 블랙")
    assert score > 0.5


def test_low_similarity():
    score = compute_similarity("바디트리머 프로", "볼펜녹음기 32GB")
    assert score < 0.3


def test_empty_strings():
    assert compute_similarity("", "") == 1.0
    assert compute_similarity("상품", "") == 0.0

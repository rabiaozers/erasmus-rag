from retrieval import rrf_merge, tokenize


def row(page, text="x"):
    return ("doc", page, f"{text}{page}", 0.0)


def test_tokenize_drops_stop_words_and_stems():
    assert tokenize("What are the Youth Exchanges grants?") == ["youth", "exchang", "grant"]


def test_rrf_prefers_chunks_found_by_both_searches():
    a = [row(1), row(2), row(3)]           # page 1 is first only in list a
    b = [row(9), row(3), row(8)]           # page 3 is in both lists
    best = rrf_merge([a, b], k=1)
    assert best[0][1] == 3


def test_rrf_returns_at_most_k_unique_chunks():
    a = [row(1), row(2)]
    b = [row(2), row(1)]
    assert len(rrf_merge([a, b], k=5)) == 2

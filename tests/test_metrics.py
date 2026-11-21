from metrics import numbers, parse_pages


def test_parse_pages_reads_source_and_page():
    assert parse_pages("igu-steps:2;igu-slides:8") == {("igu-steps", 2), ("igu-slides", 8)}


def test_parse_pages_empty():
    assert parse_pages("") == set()


def test_numbers_joins_thousands():
    assert numbers("Two lump sums: 30 000 EUR or 60 000 EUR") == {"30000", "60000"}


def test_summarize_verdicts_counts_each_kind():
    import pandas as pd

    from metrics import summarize_verdicts

    judged = pd.DataFrame({
        "type": ["number", "number", "table", "none"],
        "correctness": ["correct", "incorrect", "no_answer", "refused"],
        "grounded": [True, False, None, None],
    })
    lines = summarize_verdicts(judged)
    assert "correct:              1/3" in lines
    assert "grounded in cited pages: 1/2 answered" in lines
    assert "refused unanswerable: 1/1" in lines

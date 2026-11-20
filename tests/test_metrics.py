from metrics import numbers, parse_pages


def test_parse_pages_reads_source_and_page():
    assert parse_pages("igu-steps:2;igu-slides:8") == {("igu-steps", 2), ("igu-slides", 8)}


def test_parse_pages_empty():
    assert parse_pages("") == set()


def test_numbers_joins_thousands():
    assert numbers("Two lump sums: 30 000 EUR or 60 000 EUR") == {"30000", "60000"}

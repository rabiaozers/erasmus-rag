from chunking import split_pages


def test_chunks_have_the_right_size_and_overlap():
    words = [f"w{i}" for i in range(300)]
    chunks = split_pages([{"page": 7, "text": " ".join(words)}], size=150, overlap=30)
    assert [len(c["text"].split()) for c in chunks] == [150, 150, 60]
    assert chunks[1]["text"].split()[0] == "w120"           # starts 150 - 30 words later
    assert all(c["page"] == 7 for c in chunks)


def test_short_page_is_one_chunk():
    chunks = split_pages([{"page": 1, "text": "only a few words"}])
    assert len(chunks) == 1

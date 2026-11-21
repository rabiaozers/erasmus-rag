"""Small helpers for evaluation, kept free of heavy imports so the tests run fast."""
import re

import pandas as pd


def parse_pages(value):
    """'igu-steps:2;igu-slides:8' -> {("igu-steps", 2), ("igu-slides", 8)};  empty -> empty set"""
    if pd.isna(value) or str(value).strip() == "":
        return set()
    pairs = set()
    for item in str(value).split(";"):
        source, page = item.rsplit(":", 1)
        pairs.add((source, int(page)))
    return pairs


def numbers(text):
    """'750 EUR, 20%, July 20, 2026' -> {'750', '20', '2026'};  '30 000' counts as '30000'"""
    return set(re.findall(r"\d+", str(text).replace(" 000", "000")))


def summarize_verdicts(judged):
    """Summary lines for a judged answer table (see judge.py)."""
    answerable = judged[judged["type"] != "none"]
    n = len(answerable)
    counts = answerable["correctness"].value_counts()
    answered = answerable[answerable["correctness"].isin(["correct", "partial", "incorrect"])]
    lines = [
        f"correct:              {counts.get('correct', 0)}/{n}",
        f"partial:              {counts.get('partial', 0)}/{n}",
        f"incorrect:            {counts.get('incorrect', 0)}/{n}",
        f"no answer (said so):  {counts.get('no_answer', 0)}/{n}",
        f"grounded in cited pages: {int(answered['grounded'].astype(bool).sum())}/{len(answered)} answered",
    ]
    unanswerable = judged[judged["type"] == "none"]
    if len(unanswerable):
        lines.append(f"refused unanswerable: {int((unanswerable['correctness'] == 'refused').sum())}/{len(unanswerable)}")
    return lines

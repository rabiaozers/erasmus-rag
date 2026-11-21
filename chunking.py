"""Read the Erasmus+ Programme Guide and the IGU documents and split them into chunks with page numbers."""
import json
import re

from pypdf import PdfReader

PDF_PATH = "data/programme-guide.pdf"

# Every document the assistant can answer from: (source name, file)
SOURCES = [
    ("programme-guide-2027", "data/programme-guide.pdf"),          # EU rules (466 pages)
    ("igu-steps", "data/igu-application-steps.pdf"),               # IGU step-by-step guide (9 pages)
    ("igu-slides", "data/igu-documents-ocr.json"),                 # IGU orientation slides, text read with OCR (20 slides)
    # IGU's own rules for the 2026 project year (English versions, public on udio-k.gelisim.edu.tr).
    # Only guides: result lists with names or student numbers are never added.
    ("igu-study-2026", "data/igu-2026-study-guide.pdf"),           # study mobility: dates, exam, selection, grants
    ("igu-internship-2026", "data/igu-2026-internship-guide.pdf"), # traineeship mobility: same, plus traineeship rules
    ("igu-portal", "data/igu-application-portal-guide.pdf"),       # how to use the national application portal
    ("igu-exam-subjects", "data/exam/igu-exam-subjects-2019.pdf"),  # what each part of IGU's Erasmus exam tests (TR + EN)
]

# Letterheads repeated on every page: they add nothing and would make every IGU chunk look alike
BOILERPLATE = [
    re.compile(r"Cihangir Mah\..*?erasmus@gelisim\.edu\.tr"),
    re.compile(r"T\.C\. MINISTRY OF FOREIGN AFFAIRS DIRECTORATE OF EU AFFAIRS TURKISH NATIONAL AGENCY"
               r"(?: Avrupa Birliği.*?hs01\.kep\.tr)?"),
]


def clean(text):
    """Join the text into one line and remove the repeated letterheads."""
    text = " ".join((text or "").split())
    for pattern in BOILERPLATE:
        text = pattern.sub(" ", text)
    return " ".join(text.split())


def load_pages(path):
    """Return one dict per page: {"page": 1, "text": "..."}"""
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        pages.append({"page": i + 1, "text": clean(page.extract_text())})
    return pages


def load_ocr_pages(path):
    """The IGU slides are images, so their text was extracted once with OCR (tesseract) into a JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)                 # [{"page": 1, "text": "..."}, ...]


def load_source(path):
    """Load a PDF with pypdf, or an OCR JSON file."""
    return load_ocr_pages(path) if path.endswith(".json") else load_pages(path)


def split_pages(pages, size=150, overlap=30):
    """Split every page into chunks of `size` words; neighbouring chunks share `overlap` words.
    Chunks never cross a page boundary, so each chunk keeps one page number."""
    step = size - overlap
    chunks = []
    for page in pages:
        words = page["text"].split()
        for start in range(0, len(words), step):
        
            text = " ".join(words[start : start + size])
            chunks.append({"page": page["page"], "text": text})
            if start + size >= len(words):      # this chunk already reached the end of the page
                break
    return chunks


if __name__ == "__main__":
    pages = load_pages(PDF_PATH)
    print("pages:", len(pages))
    print(pages[79]["page"], pages[79]["text"][:500])
    chunks = split_pages(pages)
    print("chunks:", len(chunks))
    for c in chunks[:4]:
        print(c["page"], len(c["text"].split()), "words:", c["text"][:80])

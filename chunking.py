"""Read the Erasmus+ Programme Guide and split it into chunks with page numbers."""
import json

from pypdf import PdfReader

PDF_PATH = "data/programme-guide.pdf"

# Every document the assistant can answer from: (source name, file)
SOURCES = [
    ("programme-guide-2027", "data/programme-guide.pdf"),          # EU rules (466 pages)
    ("igu-steps", "data/igu-application-steps.pdf"),               # IGU step-by-step guide (9 pages)
    ("igu-slides", "data/igu-documents-ocr.json"),                 # IGU orientation slides, text read with OCR (20 slides)
]


def load_pages(path):
    """Return one dict per page: {"page": 1, "text": "..."}"""
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        pages.append({"page": i + 1, "text": page.extract_text()})
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

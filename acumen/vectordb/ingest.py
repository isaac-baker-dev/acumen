"""Acumen Document Ingestion - Supports txt, md, py, json, csv, pdf, docx"""

from pathlib import Path
from acumen.core.text_utils import split_into_chunks, clean_text
from acumen.memory import MemoryManager
from acumen.security.permissions import check_file_read
from acumen.core.logger import get_logger

logger = get_logger("acumen.vectordb.ingest")

def extract_pdf(file_path):
    try:
        import fitz
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        logger.warning(f"PDF extraction failed: {e}")
        return ""

def extract_docx(file_path):
    try:
        from docx import Document
        doc = Document(file_path)
        text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return text
    except Exception as e:
        logger.warning(f"DOCX extraction failed: {e}")
        return ""

def extract_text(file_path):
    path = Path(file_path)
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_pdf(str(path))
    elif ext == ".docx":
        return extract_docx(str(path))
    else:
        return path.read_text(encoding="utf-8", errors="replace")

def ingest_file(file_path, topic=None, source=None):
    if not check_file_read(file_path):
        return 0
    path = Path(file_path)
    if not path.exists():
        return 0
    content = clean_text(extract_text(str(path)))
    if len(content) < 50:
        return 0
    chunks = split_into_chunks(content)
    metadatas = [{"source": source or str(path), "topic": topic or "general",
                  "chunk": i, "total": len(chunks), "filetype": path.suffix} for i in range(len(chunks))]
    MemoryManager().save_knowledge_batch(chunks, metadatas)
    logger.info(f"Ingested {len(chunks)} chunks from {path.name}")
    return len(chunks)

def ingest_text(text, topic="general", source="manual"):
    chunks = split_into_chunks(clean_text(text))
    metas = [{"source": source, "topic": topic, "chunk": i} for i in range(len(chunks))]
    MemoryManager().save_knowledge_batch(chunks, metas)
    return len(chunks)
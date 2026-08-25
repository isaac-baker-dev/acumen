"""Acumen Text Utilities - Shared text processing."""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from acumen.core.config import CHUNK_SIZE, CHUNK_OVERLAP
import re

def split_into_chunks(text, chunk_size=None, chunk_overlap=None):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or CHUNK_SIZE,
        chunk_overlap=chunk_overlap or CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "])
    return splitter.split_text(text)

def truncate(text, max_chars=500):
    return text[:max_chars-3] + "..." if len(text) > max_chars else text

def clean_text(text):
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()
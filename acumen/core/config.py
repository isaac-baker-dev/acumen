"""
Acumen Core Configuration
========================
Single source of truth for all paths, constants, and settings.
Every module imports from here. No hardcoded paths anywhere else.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# -- Paths --
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = DATA_DIR / "chromadb"
SQLITE_DIR = DATA_DIR / "sqlite"
LOG_DIR = DATA_DIR / "logs"
OUTPUT_DIR = DATA_DIR / "outputs"
CONVO_DIR = DATA_DIR / "conversations"
CONFIG_DIR = PROJECT_ROOT / "config"
for d in [DATA_DIR, CHROMA_DIR, SQLITE_DIR, LOG_DIR, OUTPUT_DIR, CONVO_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# -- Models --
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
MODELS = {
    "fast": "qwen2.5:3b",
    "reasoning": "qwen2.5:3b",
    "code": "qwen2.5-coder:7b-instruct-q5_K_M",
    "embedding": "nomic-embed-text",
    "router": "tinyllama:1.1b",
}

# -- Cloud (optional) --
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

def is_cloud_available() -> bool:
    return bool(ANTHROPIC_API_KEY or OPENAI_API_KEY)

# -- Memory --
EPISODIC_DB_PATH = SQLITE_DIR / "episodic.db"
CHROMA_COLLECTION = "acumen_knowledge"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# -- Agents --
AGENT_MAX_ITER = 5
AGENT_VERBOSE = True
DEFAULT_TEMP = 0.3

# -- Security --
ALLOWED_READ_DIRS = [str(DATA_DIR), str(CONFIG_DIR), str(PROJECT_ROOT / "acumen")]
ALLOWED_WRITE_DIRS = [str(CHROMA_DIR), str(SQLITE_DIR), str(LOG_DIR), str(OUTPUT_DIR)]
BLOCKED_COMMANDS = ["rm -rf","sudo","chmod","chown","curl","wget","nc","ssh"]
SANDBOX_TIMEOUT = 30
SANDBOX_MAX_MEM = "512m"

# -- DAG Engine --
DAG_ENGINE_HOST = "127.0.0.1"
DAG_ENGINE_PORT = 9090
WORKER_POOL_SIZE = 4

# -- Web Interface --
API_HOST = "127.0.0.1"
API_PORT = 8000

# -- Green Computing --
DEFAULT_CTX = 8192
OLLAMA_KEEP_ALIVE = "5m"
MAX_CONCURRENT_MODELS = 1
BATCH_EMBEDDING_SIZE = 32

# -- Telemetry (always disabled) --
TELEMETRY_ENABLED = False
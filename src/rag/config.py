"""Configuration loaded from environment and an optional .env file."""

from dataclasses import dataclass
import os
from pathlib import Path


def _load_dotenv() -> None:
    path = Path(".env")
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


@dataclass(frozen=True)
class Settings:
    embedding_model: str = "intfloat/multilingual-e5-small"
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 5
    raw_dir: Path = Path("data/raw")
    store_dir: Path = Path("data/processed")
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv()
        settings = cls(
            embedding_model=os.getenv("EMBEDDING_MODEL", cls.embedding_model),
            chunk_size=int(os.getenv("CHUNK_SIZE", cls.chunk_size)),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", cls.chunk_overlap)),
            top_k=int(os.getenv("TOP_K", cls.top_k)),
            raw_dir=Path(os.getenv("RAW_DIR", str(cls.raw_dir))),
            store_dir=Path(os.getenv("STORE_DIR", str(cls.store_dir))),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", cls.ollama_base_url).rstrip("/"),
            ollama_model=os.getenv("OLLAMA_MODEL", cls.ollama_model),
        )
        if settings.chunk_size <= 0 or not 0 <= settings.chunk_overlap < settings.chunk_size:
            raise ValueError("CHUNK_SIZE must be positive and CHUNK_OVERLAP must be between 0 and CHUNK_SIZE")
        if settings.top_k <= 0:
            raise ValueError("TOP_K must be positive")
        return settings
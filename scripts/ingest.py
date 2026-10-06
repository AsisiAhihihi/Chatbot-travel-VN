"""Build or replace the local vector index from data/raw."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag.pipeline import RAGPipeline
from rag.config import Settings


def main() -> int:
    try:
        settings = Settings.from_env()
        count = RAGPipeline(settings).ingest()
    except Exception as exc:
        print(f"Ingest failed: {exc}", file=sys.stderr)
        return 1
    print(f"Indexed {count} chunks in {settings.store_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
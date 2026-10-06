"""Read supported files while retaining paths for answer citations."""

from pathlib import Path

from langchain_core.documents import Document
from .travel import parse_frontmatter

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


def load_documents(raw_dir: Path) -> list[Document]:
    if not raw_dir.exists():
        return []
    documents: list[Document] = []
    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if path.name.lower() in {"readme.md", "huong_dan_rag.md", "danh_muc_diem_den.md"}:
            continue
        try:
            if path.suffix.lower() == ".pdf":
                from pypdf import PdfReader

                text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
            else:
                text = path.read_text(encoding="utf-8", errors="replace")
            metadata = {"source": path.relative_to(raw_dir).as_posix()}
            if path.suffix.lower() == ".md":
                frontmatter, text = parse_frontmatter(text)
                metadata.update(frontmatter)
        except Exception as exc:
            print(f"Skipping {path}: {exc}")
            continue
        if text.strip():
            documents.append(
                Document(
                    page_content=text.strip(),
                    metadata=metadata,
                )
            )
    return documents
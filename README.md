# HuyG RAG chatbot

A local-first LangChain retrieval-augmented chatbot for Markdown, text, and PDF documents. It uses LangChain `Document` objects, `RecursiveCharacterTextSplitter`, local multilingual E5 embeddings, and a persistent Chroma vector store, then retrieves top-k passages and answers with source citations.

## Windows PowerShell setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Install [Ollama](https://ollama.com), start it, then download a chat model (the default is `llama3.2`):

```powershell
ollama pull llama3.2
```

Put `.txt`, `.md`, or `.pdf` files (including files in subfolders) in `data/raw`, then build the index and ask:

```powershell
python scripts/ingest.py
python scripts/ask.py "Tài liệu nói gì về chủ đề này?"
```

The embedding model `intfloat/multilingual-e5-small` is downloaded and cached locally the first time it is used. Ingest after adding or changing documents; ingest replaces the local Chroma collection. The generated `data/processed` store is disposable and is not committed. If Ollama is not running, retrieval still works and the CLI prints the matching passages rather than claiming an LLM answer.

## Configuration

## Travel knowledge dataset

The active knowledge base contains only the 34 province/city Markdown documents
in `data/raw/vietnam_travel_rag`. The seven previous travel guides have been removed.
These documents now use dataset version 2.1: 209 destination entries after
reviewed separation of 35 grouped entries (previously 174),
with descriptions researched on October 1, 2026 and original price sources
researched on September 30, 2026 (neither date guarantees current prices).
The imported source is `vietnam_travel_rag_bo_sung_174_muc/vietnam_travel_rag_v2`.
Its JSONL duplicates the destination descriptions and is not ingested.
The original import remains unchanged for provenance. Active province files are
in `data/raw/vietnam_travel_rag`; do not overwrite them with the original v2 files.
Introduction/discovery responses are composed from typed source evidence, regional
itineraries use one local-area cluster, and comparison/general generation retains
the configured Ollama model. Route feasibility and current quotes are not verified.
README, operational instructions and the destination index are excluded from ingestion.

Province YAML frontmatter is stored as metadata (list values are JSON strings for
Chroma compatibility). Travel documents are split by Markdown headings, retaining
each POI and each complete price row. Long tables are split between rows with their
headers repeated. Source URLs and publication/date notes are attached to each
relevant chunk, including inline description sources, and included in the LLM context; they are not treated as verified
current prices. Province names and aliases are matched accent-insensitively and
retrieval combines semantic and keyword ranks, with coverage for multiple explicitly
requested provinces within TOP_K. No coordinates or images are invented.

Rebuild the index after replacing documents:

```powershell
.\.venv\Scripts\python.exe scripts/ingest.py
.\.venv\Scripts\python.exe scripts/ask.py "Hà Giang có những điểm du lịch nào?"
```

Ingestion replaces the `huyg_rag` Chroma collection, removing old indexed chunks.
The frontend demo catalogue is separate; importing this dataset does not connect
the frontend to a `/chat` backend or add map markers.

Retrieval scores are reciprocal-rank fusion relevance scores (higher is better),
not cosine similarities or raw Chroma distances.

### Environment variables

Environment variables (or values in `.env`) include `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `EMBEDDING_MODEL`, `CHUNK_SIZE` (800), `CHUNK_OVERLAP` (120), `TOP_K` (5), `RAW_DIR`, and `STORE_DIR`.

## Tests

```powershell
python -m unittest discover -s tests -v
```
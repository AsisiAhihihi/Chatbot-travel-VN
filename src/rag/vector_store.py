"""Persistent local Chroma vector store through LangChain integrations."""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from .travel import normalize, resolve_provinces


class LangChainVectorStore:
    def __init__(self, store: Chroma) -> None:
        self.store = store

    @classmethod
    def from_documents(cls, documents, embeddings, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        store = Chroma(
            embedding_function=embeddings,
            persist_directory=str(directory),
            collection_name="huyg_rag",
        )
        store.delete_collection()
        store = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=str(directory),
            collection_name="huyg_rag",
        )
        return cls(store)

    @classmethod
    def load(cls, embeddings, directory: Path):
        if not directory.exists():
            raise FileNotFoundError(f"Vector index not found at {directory}; run scripts/ingest.py first")
        return cls(
            Chroma(
                persist_directory=str(directory),
                embedding_function=embeddings,
                collection_name="huyg_rag",
            )
        )

    def similarity_search_with_score(self, query: str, k: int = 5, candidates=None):
        if candidates is not None:
            # Filter scope and kind BEFORE ranking, not after a global top-k.
            if not candidates:
                return []
            identifiers = [doc.metadata.get('place_id') for doc in candidates]
            if all(identifiers):
                where = {'place_id': {'$in': identifiers}}
            else:
                clauses = []
                for doc in candidates:
                    clauses.append({'$and': [{'source': doc.metadata['source']},
                                            {'start_index': doc.metadata['start_index']}]})
                where = clauses[0] if len(clauses) == 1 else {'$or': clauses}
            semantic = self.store.similarity_search_with_score(query, k=len(candidates), filter=where)
            def identity(doc):
                return (doc.metadata.get('source'), doc.metadata.get('start_index'), doc.page_content)
            q = normalize(query)
            tokens = set(q.split())
            lexical = sorted(candidates, key=lambda doc: (
                100 * int(f" {normalize(doc.metadata.get('section', ''))} " in f' {q} ')
                + sum(len(t) for t in tokens if len(t) > 2 and t in normalize(doc.page_content).split())
            ), reverse=True)
            scores = {}
            for ranked in ([doc for doc, _ in semantic], lexical):
                for rank, doc in enumerate(ranked):
                    key = identity(doc)
                    scores[key] = scores.get(key, 0) + 1 / (60 + rank)
            return [(doc, scores.get(identity(doc), 0)) for doc in sorted(
                candidates, key=lambda doc: scores.get(identity(doc), 0), reverse=True)[:k]]
        payload = self.store.get(include=["metadatas", "documents"])
        provinces = resolve_provinces(query, payload["metadatas"])
        where = {"province_id": {"$in": provinces}} if provinces else None
        semantic = self.store.similarity_search_with_score(query, k=max(k * 3, 15), filter=where)
        # Reciprocal-rank fusion retains exact names alongside semantic matches.
        q = normalize(query)
        tokens = set(q.split())
        lexical = []
        for text, metadata in zip(payload["documents"], payload["metadatas"]):
            if provinces and metadata.get("province_id") not in provinces:
                continue
            body = normalize(text)
            heading = normalize(metadata.get("section", ""))
            value = sum(len(token) for token in tokens if len(token) > 2 and token in body.split())
            if heading and f" {heading} " in f" {q} ":
                value += 100
            if value:
                lexical.append((value, Document(page_content=text, metadata=metadata)))
        lexical.sort(key=lambda item: item[0], reverse=True)
        fused, documents = {}, {}
        def key(doc):
            return (doc.metadata.get("source"), doc.metadata.get("start_index"), doc.page_content)
        for rank, (doc, _) in enumerate(semantic):
            identifier = key(doc)
            fused[identifier] = 1 / (60 + rank)
            documents[identifier] = doc
        for rank, (_, doc) in enumerate(lexical[:max(k * 3, 15)]):
            identifier = key(doc)
            fused[identifier] = fused.get(identifier, 0) + 1 / (60 + rank)
            documents[identifier] = doc
        ordered = sorted(fused, key=fused.get, reverse=True)
        # Include at least one result per explicitly requested province where possible.
        chosen = []
        for province in provinces[:k]:
            candidate = next((identifier for identifier in ordered
                              if documents[identifier].metadata.get("province_id") == province), None)
            if candidate is not None:
                chosen.append(candidate)
        chosen.extend(identifier for identifier in ordered if identifier not in chosen)
        # Scores are fusion relevance scores (larger is better), not Chroma distances.
        return [(documents[identifier], float(fused[identifier])) for identifier in chosen[:k]]
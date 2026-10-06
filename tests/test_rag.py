import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.config import Settings
from rag.pipeline import RAGPipeline


class LangChainRAGTests(unittest.TestCase):
    def test_splitter_preserves_source_and_adds_offsets(self):
        document = Document(page_content="abcdefghij", metadata={"source": "notes.md"})
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=6, chunk_overlap=2, add_start_index=True,
            separators=[""],
        )
        chunks = splitter.split_documents([document])
        self.assertEqual([chunk.page_content for chunk in chunks], ["abcdef", "efghij"])
        self.assertTrue(all(chunk.metadata["source"] == "notes.md" for chunk in chunks))
        self.assertEqual([chunk.metadata["start_index"] for chunk in chunks], [0, 4])

    def test_invalid_overlap_fails(self):
        with TemporaryDirectory() as directory:
            settings = replace(
                Settings(),
                raw_dir=Path(directory),
                store_dir=Path(directory) / "index",
                chunk_size=5,
                chunk_overlap=5,
            )
            pipeline = RAGPipeline(settings=settings, embedder=object(), llm=object())
            with self.assertRaises(ValueError):
                pipeline.ingest()


if __name__ == "__main__":
    unittest.main()
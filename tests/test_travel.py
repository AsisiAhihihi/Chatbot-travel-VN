import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from langchain_core.embeddings import Embeddings
from rag.loader import load_documents
from rag.travel import parse_frontmatter, resolve_provinces, split_travel_document
from rag.grounding import introduction_excerpt
from rag.models import SearchResult
from rag.vector_store import LangChainVectorStore


ROOT = Path(__file__).resolve().parents[1]


class TestEmbeddings(Embeddings):
    """Deterministic offline embeddings for actual Chroma integration tests."""
    def embed_documents(self, texts):
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text):
        return [value / 255 for value in hashlib.sha256(text.encode()).digest()]


class TravelTests(unittest.TestCase):
    def test_frontmatter_and_aliases(self):
        metadata, body = parse_frontmatter('---\nprovince_id: test\naliases: ["Hà Giang"]\nresearched_on: 2026-09-30\n---\n# Test')
        self.assertEqual(json.loads(metadata['aliases']), ['Hà Giang'])
        self.assertEqual(metadata['researched_on'], '2026-09-30')
        self.assertEqual(body, '# Test')
        self.assertEqual(resolve_provinces('du lich ha giang', [metadata]), ['test'])
        self.assertEqual(resolve_provinces('giang', [metadata]), [])

    def test_dataset_and_readme_exclusion(self):
        docs = load_documents(ROOT / 'data' / 'raw')
        self.assertEqual(len(docs), 34)
        self.assertEqual(len({doc.metadata['province_id'] for doc in docs}), 34)
        self.assertTrue(all('README' not in doc.metadata['source'] for doc in docs))
        self.assertTrue(all(not doc.page_content.startswith('---') for doc in docs))
        with TemporaryDirectory() as directory:
            for name in ('README.md', 'HUONG_DAN_RAG.md', 'DANH_MUC_DIEM_DEN.md'):
                Path(directory, name).write_text('Not knowledge', encoding='utf-8')
            self.assertEqual(load_documents(Path(directory)), [])

    def test_v2_metadata_and_description_sources(self):
        docs = load_documents(ROOT / 'data' / 'raw')
        self.assertTrue(all(doc.metadata['dataset_version'] == '2.1' for doc in docs))
        chunks = [c for d in docs for c in split_travel_document(d, 800, 120)]
        attractions = [c for c in chunks if c.metadata.get('place_id')]
        self.assertEqual(len(attractions), 209)
        self.assertEqual(len({c.metadata['place_id'] for c in attractions}), 209)
        for chunk in attractions:
            self.assertEqual(chunk.metadata['content_type'], 'attraction')
            self.assertTrue(json.loads(chunk.metadata['search_names']))
            urls = json.loads(chunk.metadata['source_urls'])
            self.assertTrue(urls)
            self.assertTrue(all(not url.endswith(')') for url in urls))
            self.assertIn('2026-09-30', chunk.metadata['base_prices_researched_on'])
        chunk = next(c for c in attractions if c.metadata['place_id'] == 'ninh_binh_poi_01')
        result = SearchResult(text=chunk.page_content, source=chunk.metadata['source'],
                              score=1.0, index=0, metadata=chunk.metadata)
        excerpt = introduction_excerpt('Tràng An', [result])
        self.assertIn('hành trình thuyền', excerpt)
        self.assertIn('Nguồn:', excerpt)
        self.assertNotIn('chưa có thông tin đủ rõ', excerpt)

    def test_chunks_keep_pois_rows_and_scoped_sources(self):
        docs = load_documents(ROOT / 'data' / 'raw')
        for doc in docs:
            chunks = split_travel_document(doc, 800, 120)
            self.assertTrue(chunks)
            expected_pois = doc.page_content.count('- `place_id`:')
            self.assertEqual(sum('place_id' in chunk.metadata for chunk in chunks), expected_pois)
            expected_rows = [line for line in doc.page_content.splitlines()
                             if line.startswith('|') and '`' in line]
            for row in expected_rows:
                self.assertEqual(sum(row in chunk.page_content for chunk in chunks), 1)
            for chunk in chunks:
                self.assertEqual(chunk.metadata['province_id'], doc.metadata['province_id'])
                for value in chunk.metadata.values():
                    self.assertIsInstance(value, (str, int, float, bool))
                if '[S' in chunk.page_content:
                    self.assertIn('https', chunk.metadata['source_details'])
                self.assertNotIn('## Quy tắc trả lời', chunk.page_content)

    def test_alias_filter_multi_province_and_replacement(self):
        docs = load_documents(ROOT / 'data' / 'raw')
        selected = [doc for doc in docs if doc.metadata['province_id'] in {'tuyen_quang', 'dak_lak', 'ha_noi'}]
        chunks = [chunk for doc in selected for chunk in split_travel_document(doc, 800, 120)]
        embeddings = TestEmbeddings()
        # Chroma retains mmap handles until process exit on Windows; do not fail
        # successful assertions solely because temporary mmap cleanup is deferred.
        with TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = LangChainVectorStore.from_documents(chunks, embeddings, Path(directory))
            matches = store.similarity_search_with_score('Hà Giang có gì?', k=5)
            self.assertTrue(matches)
            self.assertTrue(all(doc.metadata['province_id'] == 'tuyen_quang' for doc, _ in matches))
            matches = store.similarity_search_with_score('Du lịch Hà Giang và Phú Yên', k=5)
            self.assertEqual({doc.metadata['province_id'] for doc, _ in matches}, {'tuyen_quang', 'dak_lak'})
            reloaded = LangChainVectorStore.load(embeddings, Path(directory))
            self.assertTrue(reloaded.similarity_search_with_score('ha noi'))
            replacement = [chunk for chunk in chunks if chunk.metadata['province_id'] == 'ha_noi']
            rebuilt = LangChainVectorStore.from_documents(replacement, embeddings, Path(directory))
            metadata = rebuilt.store.get(include=['metadatas'])['metadatas']
            self.assertTrue(all(item['province_id'] == 'ha_noi' for item in metadata))
            rebuilt.store.delete_collection()


if __name__ == '__main__':
    unittest.main()
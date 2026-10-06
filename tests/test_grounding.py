"""Regression coverage uses real source chunks and real Chroma, no network/model needed."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from rag.loader import load_documents
from rag.pipeline import RAGPipeline
from rag.travel import split_travel_document
from rag.vector_store import LangChainVectorStore
from test_travel import TestEmbeddings


class RecordingLLM:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt, system):
        self.prompts.append((prompt, system))
        return "Câu trả lời kiểm thử."


class GroundingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = TemporaryDirectory(ignore_cleanup_errors=True)
        cls.embeddings = TestEmbeddings()
        docs = load_documents(Path(__file__).resolve().parents[1] / 'data/raw')
        cls.store = LangChainVectorStore.from_documents(
            [c for d in docs for c in split_travel_document(d, 800, 120)],
            cls.embeddings, Path(cls.directory.name))

    @classmethod
    def tearDownClass(cls):
        cls.store.store.delete_collection()
        cls.directory.cleanup()

    def setUp(self):
        self.llm = RecordingLLM()
        self.pipeline = RAGPipeline(embedder=self.embeddings, llm=self.llm)
        self.pipeline.store = self.store

    def test_exact_input_and_stale_context(self):
        history = [{'role': 'user', 'text': 'Khách sạn Cà Mau và An Giang'},
                   {'role': 'assistant', 'text': 'Chào Mây, Nhà Của Mây ở Cà Mau'}]
        result = self.pipeline.answer('Hạ Long và Tràng An', history)
        self.assertEqual({r.metadata['place_id'] for r in result.sources},
                         {'quang_ninh_poi_01', 'ninh_binh_poi_01'})
        for forbidden in ('Cà Mau', 'An Giang', 'khách sạn', 'homestay', 'Chào Mây'):
            self.assertNotIn(forbidden, result.answer)
        self.assertIn('Vịnh Hạ Long', result.answer)
        self.assertIn('Tràng An', result.answer)
        self.assertIn('hang', result.answer)
        self.assertNotIn('Tam Cốc', result.answer)
        self.assertNotIn('Tên dùng tìm kiếm', result.answer)
        self.assertFalse(self.llm.prompts)
        self.assertTrue(all(r.metadata['source_urls'] for r in result.sources))

    def test_hotel_and_activities_have_distinct_context(self):
        hotels = self.pipeline.retrieve('Khách sạn ở Hạ Long')
        self.assertTrue(hotels)
        self.assertTrue(all(r.metadata['content_kind'] == 'accommodation' for r in hotels))
        self.assertTrue(all(r.metadata['province_id'] == 'quang_ninh' for r in hotels))
        self.assertIn('Wyndham', hotels[0].text)
        activities = self.pipeline.retrieve('Tràng An có hoạt động gì?')
        self.assertTrue(activities)
        self.assertTrue(all(r.metadata['place_id'] == 'ninh_binh_poi_01' for r in activities))

    def test_followup_ignores_assistant_contamination(self):
        history = [{'role': 'user', 'text': 'Tràng An'},
                   {'role': 'assistant', 'text': 'Hạ Long và Cà Mau'}]
        rows = self.pipeline.retrieve('Ở đó chơi gì?', history)
        self.assertTrue(rows)
        self.assertTrue(all(r.metadata['place_id'] == 'ninh_binh_poi_01' for r in rows))
        result = self.pipeline.answer('Ở đó chơi gì?', [{'role': 'user', 'text': 'Hạ Long và Tràng An'}])
        self.assertIn('hay', result.answer)
        self.assertFalse(result.sources)

    def test_business_province_and_price_provenance(self):
        result = self.pipeline.answer('Nhà Của Mây ở đâu?')
        self.assertTrue(result.sources)
        self.assertTrue(all(r.metadata['province_id'] == 'an_giang' for r in result.sources))
        self.assertIn('núi Cấm', result.answer)
        self.assertIn('An Giang', result.answer)
        self.assertNotIn('Cà Mau', result.answer)
        self.pipeline.answer('Khách sạn ở Hạ Long')
        from rag.pipeline import SYSTEM_PROMPT
        system = SYSTEM_PROMPT
        self.assertIn('Wyndham', self.pipeline.answer('Khách sạn ở Hạ Long').answer)
        self.assertFalse(self.llm.prompts)
        self.assertIn('Mây không phải tên người dùng', system)
        prices = self.pipeline.retrieve('Giá vé Tràng An')
        self.assertTrue(prices)
        self.assertTrue(all('published_reference' in r.metadata['price_status'] for r in prices))
        self.assertTrue(all('researched_on' in r.metadata for r in prices))

    def test_province_qualifier_does_not_add_recommendations(self):
        rows = self.pipeline.retrieve('Hạ Long Quảng Ninh và Tràng An Ninh Bình')
        self.assertEqual({r.metadata['place_id'] for r in rows},
                         {'quang_ninh_poi_01', 'ninh_binh_poi_01'})

    def test_missing_scope_has_no_nationwide_fallback(self):
        self.assertFalse(self.pipeline.retrieve('điểm chưa có trong dữ liệu xyz'))

    def test_v2_search_names_and_scoped_description_sources(self):
        rows = self.pipeline.retrieve('Muốn đến Bút Tháp')
        self.assertTrue(rows)
        self.assertTrue(all(r.metadata['province_id'] == 'bac_ninh' for r in rows))
        self.assertTrue(all('Bút Tháp' in r.text for r in rows))
        self.assertTrue(all(r.metadata['source_urls'] != '[]' for r in rows))
        rows = self.pipeline.retrieve('Hang Múa có rừng quốc gia không?')
        self.assertTrue(rows)
        self.assertTrue(all(r.metadata['place_id'] == 'ninh_binh_poi_03' for r in rows))
        self.assertIn('không phải vườn quốc gia', rows[0].text)


if __name__ == '__main__':
    unittest.main()
"""Intent, evidence isolation, regional plans and response contracts."""
import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from rag.api import create_app
from rag.grounding import resolve_request, intent_for
from rag.loader import load_documents
from rag.travel import split_travel_document
from rag.advice import select_itinerary, distance
import test_grounding


class AdviceTests(unittest.TestCase):
    setUpClass = classmethod(test_grounding.GroundingTests.setUpClass.__func__)
    tearDownClass = classmethod(test_grounding.GroundingTests.tearDownClass.__func__)
    setUp = test_grounding.GroundingTests.setUp
    def test_regional_itinerary_not_rejected(self):
        answer = self.pipeline.answer('Gợi ý chuyến đi 3 ngày 2 đêm ở miền Nam')
        self.assertTrue(answer.sources)
        self.assertIn('Ngày 1', answer.answer)
        self.assertIn('Ngày 3', answer.answer)
        self.assertIn('nghỉ đêm', answer.answer)
        self.assertIn('sơ bộ', answer.answer)
        self.assertIn('xuất phát', answer.answer)
        self.assertEqual(len({r.metadata['local_area'] for r in answer.sources}), 1)
        self.assertTrue(answer.itinerary_ids)
        self.assertNotIn('cho biết tên', answer.answer)

    def test_province_descriptions_and_old_names(self):
        for question in ('Vĩnh Long có gì?', 'vinh long co gi', 'Bến Tre có gì?'):
            result = self.pipeline.answer(question)
            self.assertGreaterEqual(len(result.sources), 3)
            self.assertTrue(all(r.metadata['province_id'] == 'vinh_long' for r in result.sources))
            self.assertIn('Bạn có thể', result.answer)
            self.assertGreater(len(result.answer.split()), 70)

    def test_split_children_and_parent_relationship(self):
        result = self.pipeline.answer('Tràng An và Tam Cốc')
        self.assertEqual(set(result.place_ids), {'ninh_binh_poi_01', 'ninh_binh_poi_01_b'})
        result = self.pipeline.answer('Fansipan có gì?')
        self.assertEqual(result.place_ids, ['lao_cai_poi_01_b'])
        self.assertEqual(result.sources[0].metadata['parent_place_id'], 'lao_cai_poi_01')
        self.assertNotIn('ruộng bậc thang', result.answer)

    def test_comparison_uses_clean_evidence_and_existing_model(self):
        self.pipeline.answer('So sánh Hạ Long và Tràng An')
        self.assertEqual(len(self.llm.prompts), 1)
        prompt, _ = self.llm.prompts[0]
        for field in ('place_id', 'content_type', 'Tên dùng tìm kiếm', 'Tam Cốc', 'latitude'):
            self.assertNotIn(field, prompt)
        self.assertIn('Tràng An', prompt)

    def test_unknown_place_does_not_use_other_provinces(self):
        result = self.pipeline.answer('Điểm xyz chưa có có gì?')
        self.assertFalse(result.sources)
        self.assertFalse(result.place_ids)

    def test_price_rows_are_exact_and_preserve_units(self):
        result = self.pipeline.answer('Giá đi thuyền Tràng An?')
        self.assertTrue(result.sources)
        self.assertNotIn('Tam Cốc', result.answer)
        self.assertNotIn('Homestay', result.answer)
        self.assertIn('tham khảo', result.answer)
        self.assertIn('2026-09-30', result.answer)
        self.assertIn('VND', result.answer)

    def test_context_and_ambiguity(self):
        result = self.pipeline.answer('Mỹ Khê có gì?')
        self.assertFalse(result.sources)
        self.assertIn('tỉnh', result.answer)
        result = self.pipeline.answer('Mỹ Khê có gì?', [{'role': 'user', 'text': 'Đà Nẵng'}])
        self.assertTrue(result.sources)
        self.assertTrue(all(r.metadata['province_id'] == 'da_nang' for r in result.sources))
        scope, _ = self.pipeline.request_scope('Thích sông nước', [{'role': 'user', 'text': 'Miền Nam 3 ngày 2 đêm'}])
        self.assertEqual((scope.region, scope.days, scope.nights), ('nam', 3, 2))
        rows = self.pipeline.retrieve('Ở đó chơi gì?', [{'role': 'user', 'text': 'Vĩnh Long có gì?'},
                                     {'role': 'user', 'text': 'Giá đi thuyền Tràng An?'}])
        self.assertEqual({r.metadata['place_id'] for r in rows}, {'ninh_binh_poi_01'})
        scope, _ = self.pipeline.request_scope('mien nam 3 ngay 2 dem, xuat phat tu Ha Noi')
        self.assertEqual(scope.region, 'nam')
        self.assertNotIn('ha_noi', {t.province_id for t in scope.targets})

    def test_api_sources_and_map_status_are_separate(self):
        client = TestClient(create_app(lambda: self.pipeline))
        from unittest.mock import patch
        from rag.api import CATALOGUE
        with patch('rag.api.CATALOGUE', [{**p, 'coordinates': None} for p in CATALOGUE]):
            data = client.post('/chat', json={'question': 'Mang Thít có gì?'}).json()
        self.assertNotIn('tọa độ', data['answer'])
        self.assertEqual(data['map_action'], 'keep')
        self.assertIsNone(data['route'])
        self.assertTrue(data['map_status'])
        self.assertTrue(data['sources'])
        self.assertTrue(all(not s['title'].endswith('.md') for s in data['sources']))
        self.assertTrue(all(p['coordinates'] is None for p in data['places']))


if __name__ == '__main__':
    unittest.main()
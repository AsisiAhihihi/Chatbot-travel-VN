import json
from pathlib import Path
import unittest

from rag.catalogue_builder import build_catalogue
from rag.api import ambiguous_matches, match_places, create_app
from rag.models import RAGAnswer, SearchResult
from fastapi.testclient import TestClient
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class CatalogueTests(unittest.TestCase):
    def test_supplied_coordinates_preserve_usage(self):
        rows = json.loads((ROOT / 'toa_do_75_dia_diem/poi_coordinates.json').read_text(encoding='utf8'))
        records = {p['id']: p for p in json.loads((ROOT/'src/rag/catalogue.json').read_text(encoding='utf8'))}
        self.assertEqual(len(rows), 75)
        for row in rows:
            place = records[row['id']]
            self.assertEqual(place['coordinates'], row['coordinates'])
            self.assertEqual(place['map_usage'], row['map_usage'])
            self.assertEqual(place['resolved_name'], row['resolved_name'])
            self.assertFalse(place['navigation_ready'])
        self.assertEqual(sum(p.get('map_usage') == 'zoom_only' for p in records.values()), 3)
    def test_reproducible_and_traceable(self):
        base = ROOT / 'src' / 'rag'
        overrides = json.loads((base / 'catalogue_overrides.json').read_text(encoding='utf8'))
        locations = json.loads((base / 'catalogue_locations.json').read_text(encoding='utf8'))
        records, report = build_catalogue(ROOT / 'data' / 'raw', overrides, locations)
        self.assertEqual(records, json.loads((base / 'catalogue.json').read_text(encoding='utf8')))
        self.assertEqual(report['files'], 34)
        self.assertEqual(report['rag_records'], 209)
        self.assertEqual(len({p['id'] for p in records}), len(records))
        self.assertEqual(sum(len(p['rag_ids']) for p in records), 209)
        self.assertEqual(report['mapped'], len(overrides) + len(locations))
        self.assertTrue(all(p['coordinates'] is None for p in records if p['id'] not in {o['id'] for o in overrides + locations}))
        self.assertTrue(all(p['coordinate_source'].startswith('https://') for p in locations))
        hoi_an = next(p for p in records if p['id'] == 'hoi-an')
        self.assertIn('da_nang_poi_03', hoi_an['rag_ids'])
        self.assertTrue(hoi_an['documents'][0]['sources'])

    def test_duplicate_names_require_context(self):
        selected, ambiguous = ambiguous_matches(match_places('Mỹ Khê'), 'Mỹ Khê')
        self.assertFalse(selected)
        self.assertEqual(len(ambiguous), 2)
        selected, ambiguous = ambiguous_matches(match_places('Mỹ Khê Đà Nẵng'), 'Mỹ Khê Đà Nẵng')
        self.assertEqual(selected[0]['id'], 'da_nang_poi_01')
        self.assertFalse(ambiguous)

    def test_unmapped_reply_never_moves_camera_or_draws_route(self):
        class Pipeline:
            def answer(self, question, history=None):
                return RAGAnswer('Sơn Trà – Ngũ Hành Sơn và Bến Ninh Kiều.', [SearchResult('Thông tin', 'notes.md', 1, 0)])
        from rag.api import CATALOGUE
        # Missing-coordinate behavior must not depend on which real points were
        # subsequently verified and populated.
        unlocated = [{**p, 'coordinates': None} for p in CATALOGUE]
        client = TestClient(create_app(Pipeline))
        with patch('rag.api.CATALOGUE', unlocated):
            result = client.post('/chat', json={'question': 'Lịch trình Sơn Trà – Ngũ Hành Sơn và Bến Ninh Kiều'}).json()
        self.assertEqual(result['map_action'], 'keep')
        self.assertIsNone(result['route'])
        self.assertEqual(len(result['places']), 3)
        self.assertNotIn('tọa độ', result['answer'])
        self.assertTrue(result['map_status'])
        self.assertEqual(len(client.get('/places').json()), 209)


if __name__ == '__main__':
    unittest.main()
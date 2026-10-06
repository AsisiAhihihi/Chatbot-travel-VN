import unittest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient
from rag.api import create_app
from rag.models import RAGAnswer, SearchResult


class StubPipeline:
    calls = []

    def answer(self, question, history=None):
        self.calls.append((question, history))
        return RAGAnswer("Hội An và Mỹ Sơn là các điểm được nhắc trong tài liệu.", [
            SearchResult("Thông tin tham khảo https://whc.unesco.org/en/list/948/", "notes.md", 1, 0)
        ])


class APITests(unittest.TestCase):
    def setUp(self):
        StubPipeline.calls = []
        self.client = TestClient(create_app(StubPipeline))

    def test_real_contract_and_verified_coordinates(self):
        data = self.client.post('/chat', json={"question": "Hội An có gì?", "history": []}).json()
        self.assertEqual(data['map_action'], 'focus')
        self.assertEqual(data['places'][0]['id'], 'hoi-an')
        self.assertEqual(data['places'][0]['coordinates'], [108.333333, 15.883333])
        self.assertTrue(data['sources'])

    def test_itinerary(self):
        data = self.client.post('/chat', json={"question": "Lịch trình Hội An và Mỹ Sơn"}).json()
        self.assertEqual(data['itinerary'], ['hoi-an', 'my-son'])
        self.assertEqual(data['route']['kind'], 'illustrative')
        self.assertGreater(data['route']['distance_m'], 10000)
        self.assertLess(data['route']['distance_m'], 100000)
        self.assertNotIn('duration_s', data['route'])

    def test_history_and_ambiguity(self):
        self.client.post('/chat', json={"question": "Ở đó có gì?", "history": [{"role": "user", "text": "Hội An"}]})
        self.assertEqual(StubPipeline.calls[-1][0], 'Ở đó có gì?')
        self.assertEqual(StubPipeline.calls[-1][1][0]['text'], 'Hội An')
        count = len(StubPipeline.calls)
        data = self.client.post('/chat', json={"question": "An Bình"}).json()
        self.assertEqual(data['map_action'], 'keep')
        self.assertEqual(len(StubPipeline.calls), count)

    def test_failures_are_not_demo_responses(self):
        class Broken:
            def answer(self, *args, **kwargs):
                raise ConnectionError()
        response = TestClient(create_app(Broken)).post('/chat', json={"question": "Hội An"})
        self.assertEqual(response.status_code, 503)
        self.assertIn('Ollama', response.json()['detail'])
        self.assertEqual(self.client.post('/chat', json={"question": " "}).status_code, 422)

    def test_cors_and_document_security(self):
        response = self.client.options('/chat', headers={
            'Origin': 'http://127.0.0.1:5173', 'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type'})
        self.assertEqual(response.headers['access-control-allow-origin'], 'http://127.0.0.1:5173')
        self.assertEqual(self.client.get('/sources/%2E%2E/%2E%2E/.env').status_code, 404)

    def test_public_images_and_rate_limit(self):
        with patch.dict(os.environ, {'PUBLIC_DEPLOY': 'true', 'CHAT_REQUESTS_PER_MINUTE': '1', 'FRONTEND_ORIGINS': 'https://asisiahihihi.github.io'}):
            client = TestClient(create_app(StubPipeline))
            places = client.get('/places').json()
            self.assertEqual(len(places), 209)
            for place in places:
                if place.get('image'):
                    self.assertNotEqual(place['image'].get('rights_status'), 'permission_required')
                    self.assertTrue(place['image'].get('license'))
            self.assertEqual(client.post('/chat', json={'question': 'Hội An'}).status_code, 200)
            self.assertEqual(client.post('/chat', json={'question': 'Hội An'}).status_code, 429)
            response = client.options('/chat', headers={'Origin': 'https://asisiahihihi.github.io', 'Access-Control-Request-Method': 'POST'})
            self.assertEqual(response.headers['access-control-allow-origin'], 'https://asisiahihihi.github.io')


if __name__ == '__main__':
    unittest.main()
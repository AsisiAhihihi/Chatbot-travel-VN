"""Live verification against the installed index and Ollama; writes a UTF-8 report."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / 'src'))

from rag.pipeline import RAGPipeline


if __name__ == '__main__':
    pipeline = RAGPipeline()
    cases = [
        ('Hạ Long và Tràng An', [{'role': 'user', 'text': 'Khách sạn Cà Mau và An Giang'},
                                {'role': 'assistant', 'text': 'Chào Mây, Nhà Của Mây ở Cà Mau'}]),
        ('Khách sạn ở Hạ Long', []),
        ('Tràng An có hoạt động gì?', []),
        ('Ở đó chơi gì?', [{'role': 'user', 'text': 'Tràng An'},
                          {'role': 'assistant', 'text': 'Cà Mau'}]),
        ('Nhà Của Mây ở đâu?', []),
    ]
    report = []
    for question, history in cases:
        answer = pipeline.answer(question, history)
        report.append({'question': question, 'answer': answer.answer,
                       'chunks': [r.metadata for r in answer.sources]})
        (ROOT / 'grounding-live.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    first = report[0]
    assert {r['place_id'] for r in first['chunks']} == {'quang_ninh_poi_01', 'ninh_binh_poi_01'}
    assert all(s not in first['answer'] for s in ('Cà Mau', 'An Giang', 'khách sạn', 'homestay', 'Chào Mây'))
    assert all(r['content_kind'] == 'accommodation' for r in report[1]['chunks'])
    assert all(r['place_id'] == 'ninh_binh_poi_01' for r in report[2]['chunks'] + report[3]['chunks'])
    assert 'An Giang' in report[4]['answer'] and 'Cà Mau' not in report[4]['answer']
    print('Live grounding verification passed (5 cases). Report: grounding-live.json')
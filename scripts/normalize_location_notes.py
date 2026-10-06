"""Repair the UTF-8 note without changing sourced numeric coordinates."""
import json
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'src/rag/catalogue_locations.json'
if __name__ == '__main__':
    records = json.loads(path.read_text(encoding='utf8'))
    for record in records:
        record['coordinate_note'] = 'Vị trí tham chiếu theo nguồn địa lý, không phải lối vào hoặc bến đón đã xác nhận; vùng cảnh quan có thể trải rộng quanh điểm này.'
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
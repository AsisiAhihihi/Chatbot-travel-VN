"""Fetch named OSM objects for manual review. Does not write the live catalogue."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from rag.travel import normalize


def main():
    records = json.loads((ROOT / 'src/rag/catalogue.json').read_text(encoding='utf8'))
    targets = [p for p in records if p['coordinates'] is None]
    elements = []
    for start in range(0, len(targets), 20):
        pattern = '|'.join(re.escape(p['name']) for p in targets[start:start+20])
        query = f'[out:json][timeout:90];nwr["name"~"{pattern}",i](8,102,24,110);out center tags;'
        url = 'https://overpass.kumi.systems/api/interpreter?' + urlencode({'data': query})
        try:
            with urlopen(Request(url, headers={'User-Agent': 'VietnamTravelCatalogue/1.0'}), timeout=120) as response:
                elements.extend(json.load(response).get('elements', []))
        except Exception as error:
            print('Batch unavailable:', start, str(error))
        (ROOT / 'data/geography/osm_raw_coordinates.json').write_text(json.dumps(elements, ensure_ascii=False), encoding='utf8')
    payload = {'elements': list({(e['type'], e['id']): e for e in elements}.values())}
    output = []
    for place in targets:
        matches = []
        for item in payload.get('elements', []):
            tags = item.get('tags', {})
            name = tags.get('name', '')
            aliases = [place['name'], *place.get('aliases', [])]
            if any(normalize(a) in normalize(name) for a in aliases):
                matches.append(item)
        output.append({'id': place['id'], 'name': place['name'], 'candidates': matches})
    path = ROOT / 'data/geography/osm_coordinate_candidates.json'
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf8')
    print('OSM objects:', len(payload.get('elements', [])), 'matched destinations:', sum(bool(o['candidates']) for o in output))


if __name__ == '__main__':
    main()
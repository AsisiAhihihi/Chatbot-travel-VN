"""Import user-supplied references by exact ID, retaining map usage restrictions."""
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    source = ROOT / 'toa_do_75_dia_diem/poi_coordinates.json'
    rows = json.loads(source.read_text(encoding='utf-8'))
    base = ROOT / 'src/rag'
    catalogue = {p['id']: p for p in json.loads((base/'catalogue.json').read_text(encoding='utf-8'))}
    path = base/'catalogue_locations.json'
    locations = {p['id']: p for p in json.loads(path.read_text(encoding='utf-8'))}
    seen = set()
    for row in rows:
        identifier = row['id']
        assert identifier in catalogue and identifier not in seen, identifier
        seen.add(identifier)
        assert row['name'] == catalogue[identifier]['name'] and row['region'] == catalogue[identifier]['region'], identifier
        assert row['crs'] == 'WGS84' and row['navigation_ready'] is False, identifier
        assert row['coordinates'] == [row['longitude'], row['latitude']], identifier
        lon, lat = row['coordinates']
        assert 102 <= lon <= 110 and 8 <= lat <= 24, identifier
        assert row['source_urls'] and all(u.startswith('https://') for u in row['source_urls']), identifier
        assert row['map_usage'] in {'zoom_only', 'marker_and_zoom', 'representative_marker_and_zoom'}, identifier
        note = row['notes'] or 'Vị trí tham chiếu theo nguồn cung cấp; chưa kiểm chứng cổng vào hoặc điểm đón khách.'
        locations[identifier] = {
            'id': identifier, 'coordinates': row['coordinates'],
            'coordinate_source': row['source_urls'][0], 'coordinate_sources': row['source_urls'],
            'coordinate_status': row['coordinate_status'], 'coordinate_type': row['coordinate_type'],
            'coordinate_retrieved_on': row['checked_on'], 'coordinate_note': note,
            'resolved_name': row['resolved_name'], 'map_usage': row['map_usage'],
            'navigation_ready': False, 'crs': row['crs'],
            'coordinate_import_source': source.relative_to(ROOT).as_posix(),
        }
    backup = ROOT/'data/backups'/('supplied_coordinates_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True)
    for filename in ('catalogue_locations.json', 'catalogue.json', 'catalogue_report.json'):
        shutil.copy2(base/filename, backup/filename)
    path.write_text(json.dumps(list(locations.values()), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'imported': len(rows), 'zoom_only': sum(r['map_usage']=='zoom_only' for r in rows), 'backup': str(backup)}))

if __name__ == '__main__':
    main()
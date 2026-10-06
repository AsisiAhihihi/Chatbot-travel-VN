"""Build offline cartography from Natural Earth; standard library only.

Group polygons are used ONLY to classify actual land polygons, never rendered.
Run with --cache DIR containing the source files to reproduce a downloaded snapshot.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/'
FILES = {'countries': 'ne_10m_admin_0_countries.geojson',
         'minor': 'ne_10m_minor_islands.geojson',
         'groups': 'ne_10m_geography_regions_polys.geojson',
         'ocean': 'ne_10m_ocean.geojson'}


def inside(point, ring):
    x, y = point
    result = False
    for a, b in zip(ring, ring[1:] + ring[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            result = not result
    return result


def polygons(geometry):
    return [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']


def feature(geometry, properties):
    return {'type': 'Feature', 'geometry': geometry, 'properties': properties}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path)
    args = parser.parse_args()
    datasets, sources = {}, []
    for key, name in FILES.items():
        path = args.cache / name if args.cache else None
        data = path.read_bytes() if path and path.exists() else urlopen(BASE+name).read()
        datasets[key] = json.loads(data)
        sources.append({'url': BASE+name, 'sha256': hashlib.sha256(data).hexdigest()})
    groups = {f['properties']['NAME']: f for f in datasets['groups']['features']
              if f['properties']['NAME'] in ['Paracel Islands', 'Spratly Islands']}
    assert len(groups) == 2, 'Both archipelagos must be present explicitly'
    land, islands, vietnam = [], [], []
    for dataset in ['countries', 'minor']:
        for f in datasets[dataset]['features']:
            for poly in polygons(f['geometry']):
                group = next((name for name, g in groups.items()
                              if inside(poly[0][0], g['geometry']['coordinates'][0])), None)
                geometry = {'type': 'Polygon', 'coordinates': poly}
                props = {'source_dataset': FILES[dataset], 'source_properties': {k: v for k, v in f['properties'].items() if k in ['ADMIN', 'SOVEREIGNT', 'NAME', 'NOTE_BRK', 'BRK_NAME', 'featurecla', 'ne_id']}}
                if group:
                    props.update(group=group, disputed=True, label_position='Vietnam stated sovereignty',
                                 administration='China' if group == 'Paracel Islands' else 'Mixed; not assigned per feature by this dataset',
                                 dispute_source='https://amti.csis.org/island-tracker/',
                                 claimants=['Vietnam', 'China', 'Taiwan'] if group == 'Paracel Islands' else ['Vietnam', 'China', 'Taiwan', 'Philippines', 'Malaysia', 'Brunei'])
                    islands.append(feature(geometry, props))
                elif f['properties'].get('ADMIN') == 'Vietnam':
                    vietnam.append(feature(geometry, props))
                else:
                    land.append(feature(geometry, props))
    counts = {name: sum(f['properties']['group'] == name for f in islands) for name in groups}
    assert all(counts.values()), f'Missing actual island geometry: {counts}'
    # Symbol anchors are actual source vertices, NOT fabricated island locations.
    symbols = [feature({'type': 'Point', 'coordinates': f['geometry']['coordinates'][0][0]}, f['properties']) for f in islands]
    labels = []
    for name, title in [('Paracel Islands', 'Quần đảo Hoàng Sa (Việt Nam)'), ('Spratly Islands', 'Quần đảo Trường Sa (Việt Nam)')]:
        candidates = [f for f in symbols if f['properties']['group'] == name]
        anchor = sorted(candidates, key=lambda f: f['geometry']['coordinates'][1])[len(candidates)//2]
        labels.append(feature(anchor['geometry'], {**anchor['properties'], 'label': title, 'kind': 'archipelago'}))
    labels.append(feature({'type': 'Point', 'coordinates': [113.5, 14]},
                          {'label': 'Biển Đông', 'kind': 'sea', 'placement': 'Cartographic label anchor, not a land feature'}))
    out = ROOT / 'public' / 'geo'
    out.mkdir(parents=True, exist_ok=True)
    for name, features in [('surrounding-land', land), ('vietnam', vietnam), ('islands', islands), ('island-symbols', symbols), ('labels', labels)]:
        (out / (name+'.geojson')).write_text(json.dumps({'type': 'FeatureCollection', 'features': features}, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (out / 'ocean.geojson').write_text(json.dumps(datasets['ocean'], ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (out / 'manifest.json').write_text(json.dumps({'sources': sources, 'island_polygon_counts': counts, 'license': 'Natural Earth public domain', 'scale': '1:10 million; generalized, not survey/navigation geometry', 'administration_note': 'Group-level context only. Do not infer individual administration from green styling.'}, indent=2), encoding='utf-8')
    print(counts)


if __name__ == '__main__':
    main()
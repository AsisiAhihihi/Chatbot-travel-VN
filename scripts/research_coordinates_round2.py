"""Collect additional candidates, never publish unreviewed geocoder matches."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode

from fetch_coordinate_candidates import get, ROOT, CACHE


def research():
    candidates = json.loads((CACHE / 'coordinate_candidates.json').read_text(encoding='utf8'))
    reviewed_titles = {
        'an_giang_poi_02_b': 'Tay An Temple', 'bac_ninh_poi_03': 'Đình Bảng communal house',
        'bac_ninh_poi_03_b': 'Lim Festival', 'ca_mau_poi_03': 'Tan Hung Temple',
        'ca_mau_poi_04': 'Bac Lieu Mansion', 'ca_mau_poi_05': 'Xiem Can Pagoda',
        'can_tho_poi_02': 'Ninh Kieu Wharf', 'can_tho_poi_03': 'Binh Thuy Ancient House',
        'dak_lak_poi_03': 'Buon Ma Thuot Prison', 'dien_bien_poi_01': 'A1 Hill',
        'ha_noi_poi_02': 'Old Quarter, Hanoi', 'ha_tinh_poi_01': 'Dong Loc Junction',
        'hung_yen_poi_01': 'Pho Hien', 'khanh_hoa_poi_01': 'Doc Let',
        'khanh_hoa_poi_05': 'Bau Truc', 'ninh_binh_poi_05_b': 'Pho Minh Temple',
        'phu_tho_poi_03': 'Tam Dao', 'phu_tho_poi_04': 'Dai Lai Lake',
        'phu_tho_poi_06': 'Hoa Binh Lake', 'quang_ngai_poi_04': 'Thien An Mountain',
        'son_la_poi_01': 'Son La Prison', 'son_la_poi_02': 'Moc Chau',
        'thanh_hoa_poi_03': 'Pu Luong Nature Reserve', 'vinh_long_poi_03': 'Van Thanh Temple (Vinh Long)',
        'vinh_long_poi_05': 'Ba Om Pond',
    }
    articles = list(dict.fromkeys(c['article'] for c in candidates if c.get('page_id')))
    for start in range(0, len(articles), 35):
        query = get('https://vi.wikipedia.org/w/api.php?' + urlencode({
            'action': 'query', 'format': 'json', 'prop': 'langlinks', 'lllang': 'en',
            'lllimit': 'max', 'titles': '|'.join(articles[start:start+35])}))
        for page in query['query']['pages'].values():
            links = page.get('langlinks', [])
            if links:
                for c in candidates:
                    if c['article'] == page['title']:
                        reviewed_titles[c['id']] = links[0]['*']
    titles = list(dict.fromkeys(reviewed_titles.values()))
    pages = {}
    for start in range(0, len(titles), 35):
        result = get('https://en.wikipedia.org/w/api.php?' + urlencode({
            'action': 'query', 'format': 'json', 'prop': 'coordinates|pageprops|extracts',
            'exintro': 1, 'explaintext': 1, 'titles': '|'.join(titles[start:start+35]), 'colimit': 'max'}))
        pages.update({p['title']: p for p in result['query']['pages'].values()})
    def search(c):
        if c['wiki_coordinates'] or c['wikidata_coordinates']:
            return c['id'], []
        return c['id'], []
    searches = dict(ThreadPoolExecutor(max_workers=3).map(search, candidates))
    output = []
    for c in candidates:
        title = reviewed_titles.get(c['id'])
        output.append({'id': c['id'], 'name': c['name'], 'enwiki': pages.get(title, {}), 'search': searches[c['id']]})
    (CACHE / 'coordinate_round2.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf8')
    for c in output:
        if c['enwiki'].get('coordinates'):
            print(c['id'], c['enwiki']['title'], c['enwiki']['coordinates'])
        elif c['search']:
            print(c['id'], [(r['id'], r.get('label'), r.get('description')) for r in c['search']])


if __name__ == '__main__':
    research()
"""Download coordinate candidates for review; never writes production catalogue.

Use exact article titles/redirects, not geocoder first-result matching. Combined
RAG headings remain unresolved. Cache source responses for reproducible review.
"""
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from rag.travel import normalize

CACHE = ROOT / 'data' / 'geography'
TITLES = {
    'Rừng tràm Trà Sư': 'Rừng tràm Trà Sư',
    'Di tích Nhà tù Hỏa Lò': 'Nhà tù Hỏa Lò',
    'Vườn quốc gia Cát Tiên': 'Vườn quốc gia Cát Tiên',
    'Nhà cổ Bình Thủy': 'Nhà cổ Bình Thủy',
    'Chợ nổi Cái Răng': 'Chợ nổi Cái Răng',
    'Phố cổ Hà Nội': 'Phố cổ Hà Nội',
    'Đất Mũi': 'Mũi Cà Mau', 'U Minh Hạ': 'Vườn quốc gia U Minh Hạ',
    'Tràm Chim': 'Vườn quốc gia Tràm Chim',
    'Bù Gia Mập': 'Vườn quốc gia Bù Gia Mập',
    'Pù Mát': 'Vườn quốc gia Pù Mát', 'Phia Oắc': 'Phia Oắc',
    'Động Thiên Đường': 'Động Thiên Đường',
    'Nhà đày Buôn Ma Thuột': 'Nhà đày Buôn Ma Thuột',
    'Kim Liên': 'Khu di tích Kim Liên',
    'ATK Định Hóa': 'An toàn khu Định Hóa',
    'Tân Cương': 'Tân Cương (Thái Nguyên)',
    'Văn Thánh Miếu': 'Văn Thánh Miếu (Vĩnh Long)',
    'Đền Trần – Phổ Minh': None,
    'Mỹ Khê': None,  # Two distinct beaches; require individual title review.
}

# Reviewed article scopes: never resolve a temple/beach to its namesake ward.
ID_TITLES = {
 'bac_ninh_poi_03': 'Đình làng Đình Bảng',
 'bac_ninh_poi_04': 'Khu du lịch tâm linh Tây Yên Tử',
 'bac_ninh_poi_05': 'Chùa Vĩnh Nghiêm (Bắc Giang)',
 'ca_mau_poi_04': 'Nhà công tử Bạc Liêu',
 'da_nang_poi_01': 'Bãi biển Mỹ Khê',
 'dien_bien_poi_03': 'Khu di tích Mường Phăng',
 'gia_lai_poi_01': 'Hồ Tơ Nưng',
 'gia_lai_poi_04': 'Ghềnh Ráng Tiên Sa',
 'ha_tinh_poi_03': 'Bãi biển Thiên Cầm',
 'hai_phong_poi_01': 'Đảo Cát Bà',
 'hai_phong_poi_02': 'Bãi biển Đồ Sơn',
 'hai_phong_poi_04': 'Chùa Côn Sơn',
 'hung_yen_poi_01': 'Phố Hiến (thương cảng)',
 'lai_chau_poi_01': 'Bản Sin Suối Hồ',
 'lai_chau_poi_04': 'Đèo Ô Quý Hồ',
 'lam_dong_poi_02': 'Hồ Tà Đùng',
 'lam_dong_poi_04': 'Mũi Né (du lịch)',
 'lang_son_poi_02': 'Bắc Sơn (huyện)',
 'lang_son_poi_04': 'Ải Chi Lăng',
 'lao_cai_poi_01': 'Sa Pa (thị xã)',
 'lao_cai_poi_03': 'Bắc Hà (huyện)',
 'lao_cai_poi_04': 'Mù Cang Chải (huyện)',
 'lao_cai_poi_05': 'Trạm Tấu (huyện)',
 'nghe_an_poi_03': 'Bãi biển Cửa Lò',
 'ninh_binh_poi_04': 'Chùa Tam Chúc',
 'ninh_binh_poi_05': 'Đền Trần (Nam Định)',
 'phu_tho_poi_03': 'Tam Đảo (thị trấn)',
 'phu_tho_poi_05': 'Mai Châu (huyện)',
 'phu_tho_poi_06_b': 'Động Thác Bờ',
 'quang_ngai_poi_02': 'Bãi biển Mỹ Khê (Quảng Ngãi)',
 'quang_ngai_poi_03': 'Khu chứng tích Sơn Mỹ',
 'quang_ngai_poi_05': 'Măng Đen (thị trấn)',
 'quang_tri_poi_04': 'Vườn quốc gia Phong Nha – Kẻ Bàng',
 'son_la_poi_02': 'Mộc Châu (huyện)',
 'son_la_poi_04': 'Quỳnh Nhai (huyện)',
 'thai_nguyen_poi_03': 'Tân Cương (xã)',
 'thanh_hoa_poi_03': 'Khu bảo tồn thiên nhiên Pù Luông',
 'thanh_hoa_poi_04': 'Bãi biển Sầm Sơn',
 'thanh_pho_ho_chi_minh_poi_04': 'Khu dự trữ sinh quyển rừng ngập mặn Cần Giờ',
 'tuyen_quang_poi_01': 'Khu di tích Tân Trào',
 'tuyen_quang_poi_03': 'Suối khoáng Mỹ Lâm',
 'tuyen_quang_poi_05': 'Cột cờ Lũng Cú',
 'tuyen_quang_poi_05_b': 'Đồng Văn (huyện)',
 'tuyen_quang_poi_06': 'Hoàng Su Phì (huyện)',
 'vinh_long_poi_02': 'Làng nghề gạch gốm Mang Thít',
}


def get(url):
    request = Request(url, headers={'User-Agent': 'VietnamTravelCatalogue/1.0 (coordinate research; local educational app)'})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def wiki_batch(titles):
    return get('https://vi.wikipedia.org/w/api.php?' + urlencode({
        'action': 'query', 'format': 'json', 'prop': 'coordinates|pageprops',
        'titles': '|'.join(titles), 'redirects': 1, 'colimit': 'max',
    }))


def entity_batch(ids):
    return get('https://www.wikidata.org/w/api.php?' + urlencode({
        'action': 'wbgetentities', 'format': 'json', 'ids': '|'.join(ids),
        'props': 'claims|labels|descriptions', 'languages': 'vi|en',
    }))


if __name__ == '__main__':
    CACHE.mkdir(parents=True, exist_ok=True)
    records = json.loads((ROOT / 'src/rag/catalogue.json').read_text(encoding='utf8'))
    targets = [(p, ID_TITLES.get(p['id'], TITLES.get(p['name'], p['name']))) for p in records if p['coordinates'] is None and ' – ' not in p['name']]
    targets = [(p, t) for p, t in targets if t]
    titles = list(dict.fromkeys(t for _, t in targets))
    batches = [titles[i:i+35] for i in range(0, len(titles), 35)]
    responses = list(ThreadPoolExecutor(max_workers=3).map(wiki_batch, batches))
    pages, redirects = {}, {}
    for result in responses:
        query = result.get('query', {})
        for redirect in query.get('normalized', []) + query.get('redirects', []):
            redirects[redirect['from']] = redirect['to']
        for page in query.get('pages', {}).values():
            pages[page['title']] = page
    ids = list(dict.fromkeys(p.get('pageprops', {}).get('wikibase_item') for p in pages.values() if p.get('pageprops', {}).get('wikibase_item')))
    entities = {}
    for i in range(0, len(ids), 35):
        entities.update(entity_batch(ids[i:i+35]).get('entities', {}))
    candidates = []
    for record, title in targets:
        seen = set()
        while title in redirects and title not in seen:
            seen.add(title)
            title = redirects[title]
        page = pages.get(title, {})
        qid = page.get('pageprops', {}).get('wikibase_item')
        entity = entities.get(qid, {})
        statements = [s for s in entity.get('claims', {}).get('P625', []) if s.get('rank') != 'deprecated' and 'datavalue' in s.get('mainsnak', {})]
        coords = [s['mainsnak']['datavalue']['value'] for s in statements]
        candidates.append({
            'id': record['id'], 'name': record['name'], 'region': record['region'],
            'province': [d['province_name'] for d in record.get('documents', [])],
            'article': title, 'page_id': page.get('pageid'), 'wikidata_id': qid,
            'description': entity.get('descriptions', {}),
            'wiki_coordinates': page.get('coordinates', []),
            'wikidata_coordinates': coords,
            'disambiguation': 'disambiguation' in page.get('pageprops', {}),
            'retrieved_on': str(date.today()), 'review_status': 'pending',
        })
    (CACHE / 'coordinate_candidates.json').write_text(json.dumps(candidates, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    (CACHE / 'coordinate_source_responses.json').write_text(json.dumps({'wikipedia': responses, 'wikidata': entities}, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print('Candidates:', len(candidates), 'with coordinates:', sum(bool(c['wiki_coordinates'] or c['wikidata_coordinates']) for c in candidates))
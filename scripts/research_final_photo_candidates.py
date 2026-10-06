"""Research remaining destinations; never publish unreviewed search matches."""
import json
from concurrent.futures import ThreadPoolExecutor
from prepare_destination_images import ROOT, DATA, api, plain

QUERIES = {
 'ca_mau_poi_03': '"Tan Hung" "Ca Mau"',
 'can_tho_poi_06': '"Ho Be" "Soc Trang"',
 'can_tho_poi_07': '"Mua Xuan" "Hau Giang"',
 'dak_lak_poi_05_b': '"Hon Yen"',
 'dien_bien_poi_03': '"Muong Phang"',
 'dong_nai_poi_05': '"Bu Gia Map" forest',
 'ha_tinh_poi_02': '"Nguyen Du" temple',
 'ha_tinh_poi_04': '"Vu Quang" forest',
 'khanh_hoa_poi_02': '"Bich Dam"',
 'lai_chau_poi_01': '"Sin Suoi Ho"',
 'lai_chau_poi_02': '"Sin Ho" landscape',
 'lam_dong_poi_03': '"Buon Buor"',
 'quang_ngai_poi_02': '"My Khe" "Quang Ngai"',
 'son_la_poi_05': '"Ngoc Chien"',
 'tay_ninh_poi_05': '"Chavi Garden"',
 'thanh_pho_ho_chi_minh_poi_06_b': '"Phu An" bamboo',
 'tuyen_quang_poi_02_b': '"Lam Binh" landscape',
 'tuyen_quang_poi_03': '"My Lam" springs',
}

def research(item):
 identifier, query = item
 row = {'id': identifier, 'query': query, 'candidates': []}
 try:
  pages = api('commons.wikimedia.org', generator='search', gsrsearch=query,
              gsrnamespace=6, gsrlimit=10, prop='imageinfo',
              iiprop='url|extmetadata', iiurlwidth=800).get('query', {}).get('pages', {})
  for page in pages.values():
   for info in page.get('imageinfo', []):
    meta = info.get('extmetadata', {})
    row['candidates'].append({'file': page['title'],
      'description': plain(meta.get('ImageDescription', {}).get('value', '')),
      'author': plain(meta.get('Artist', {}).get('value', '')),
      'license': plain(meta.get('LicenseShortName', {}).get('value', '')),
      'license_url': meta.get('LicenseUrl', {}).get('value', ''),
      'source': info['descriptionurl'], 'url': info.get('thumburl', info['url']),
      'original_url': info['url']})
 except Exception as error:
  row['error'] = str(error)
 print(identifier, len(row['candidates']), row.get('error', ''), flush=True)
 return row

def main():
 catalogue = json.loads((ROOT/'src/rag/catalogue.json').read_text(encoding='utf8'))
 missing = {p['id'] for p in catalogue if not p.get('image')}
 rows = []
 with ThreadPoolExecutor(max_workers=2) as pool:
  for row in pool.map(research, [(k,v) for k,v in QUERIES.items() if k in missing]):
   rows.append(row)
   (DATA/'final_photo_candidates.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n', encoding='utf8')

if __name__ == '__main__':
 main()
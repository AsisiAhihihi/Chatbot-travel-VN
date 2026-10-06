"""Collect Commons search metadata for review, never auto-assign."""
import json
import time
from prepare_destination_images import api, plain, DATA

QUERIES = {
    'bac_ninh_poi_06': '"Cấm Sơn" filetype:bitmap',
    'dien_bien_poi_04': '"Pá Khoang" filetype:bitmap',
    'dong_nai_poi_04': '"Hàng Gòn" filetype:bitmap',
    'hung_yen_poi_05': '"Cồn Vành" filetype:bitmap',
    'vinh_long_poi_01': '"An Bình" filetype:bitmap',
}
if __name__ == '__main__':
    rows = []
    for identifier, query in QUERIES.items():
        row = {'id': identifier, 'query': query, 'candidates': []}
        try:
            pages = api('commons.wikimedia.org', generator='search', gsrsearch=query,
                        gsrnamespace=6, gsrlimit=12, prop='imageinfo',
                        iiprop='url|extmetadata', iiurlwidth=800).get('query', {}).get('pages', {})
            for page in pages.values():
                if not page.get('imageinfo'):
                    continue
                info = page['imageinfo'][0]
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
        rows.append(row)
        (DATA / 'remaining_photo_search.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf8')
        print(identifier, len(row['candidates']), flush=True)
        time.sleep(8)
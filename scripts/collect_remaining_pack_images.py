"""Research reusable alternatives for missing pack photos; never auto-publish."""
import json
import urllib.parse
import urllib.request
import time
from concurrent.futures import ThreadPoolExecutor
from prepare_destination_images import ROOT, DATA, plain, HEADERS


def api(host, **parameters):
    url = 'https://' + host + '/w/api.php?' + urllib.parse.urlencode(
        {'action': 'query', 'format': 'json', **parameters})
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=15) as response:
        return json.load(response)


def collect(row):
    result = {'id': row['id'], 'name': row['name'], 'location_scope': row.get('location_scope'), 'candidates': []}
    try:
        pages = api('commons.wikimedia.org', generator='search',
                    gsrsearch='"' + row['name'] + '" filetype:bitmap',
                    gsrnamespace=6, gsrlimit=6, prop='imageinfo',
                    iiprop='url|extmetadata', iiurlwidth=800).get('query', {}).get('pages', {})
        for page in pages.values():
            if not page.get('imageinfo'):
                continue
            info = page['imageinfo'][0]
            meta = info.get('extmetadata', {})
            license_name = plain(meta.get('LicenseShortName', {}).get('value', ''))
            if not license_name.startswith(('CC BY', 'CC0', 'Public domain')):
                continue
            result['candidates'].append({
                'file': page['title'], 'description': plain(meta.get('ImageDescription', {}).get('value', '')),
                'author': plain(meta.get('Artist', {}).get('value', '')), 'license': license_name,
                'license_url': meta.get('LicenseUrl', {}).get('value', ''),
                'source': info['descriptionurl'], 'url': info.get('thumburl', info['url']),
                'original_url': info['url']})
    except Exception as error:
        result['error'] = str(error)
    print(row['id'], len(result['candidates']), flush=True)
    return result


if __name__ == '__main__':
    pack = json.loads((ROOT / 'nguon_anh_95_dia_diem/poi_image_sources.json').read_text(encoding='utf8'))
    places = json.loads((ROOT / 'src/rag/catalogue.json').read_text(encoding='utf8'))
    missing = {p['id'] for p in places if not p.get('image')}
    path = DATA / 'remaining_pack_image_candidates.json'
    results = json.loads(path.read_text(encoding='utf8')) if path.exists() else []
    done = {r['id'] for r in results if not r.get('error')}
    results = [r for r in results if r['id'] in done]
    with ThreadPoolExecutor(max_workers=1) as pool:
        for row in pool.map(collect, [r for r in pack if r['id'] in missing and r['id'] not in done]):
            results.append(row)
            path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
            time.sleep(3)
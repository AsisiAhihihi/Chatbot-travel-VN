"""Collect gallery photographs for missing destinations. Never auto-publish candidates."""
import json
import time
import urllib.parse
from prepare_destination_images import ROOT, DATA, api, plain

ARTICLES = {'trang-an': 'https://vi.wikipedia.org/wiki/Khu_du_lịch_sinh_thái_Tràng_An'}

if __name__ == '__main__':
    catalogue = json.loads((ROOT / 'src/rag/catalogue.json').read_text(encoding='utf8'))
    target = DATA / 'photo_alternatives.json'
    rows = json.loads(target.read_text(encoding='utf8')) if target.exists() else []
    for place in catalogue:
        if not place.get('coordinates') or place.get('image'):
            continue
        row = {'id': place['id'], 'name': place['name'], 'candidates': []}
        sources = place.get('coordinate_sources', []) + [place.get('coordinate_source', '')]
        article = ARTICLES.get(place['id']) or next((s for s in sources if 'wikipedia.org/wiki/' in s), None)
        try:
            if not article:
                raise ValueError('No verified destination article')
            url = urllib.parse.urlparse(article)
            title = urllib.parse.unquote(url.path.split('/wiki/')[1])
            page = next(iter(api(url.netloc, titles=title, redirects=1, prop='images', imlimit=50)['query']['pages'].values()))
            titles = ['File:' + i['title'].split(':', 1)[-1] for i in page.get('images', []) if i['title'].lower().endswith(('.jpg', '.jpeg', '.png'))]
            if not titles:
                raise ValueError('No photographic files in article')
            pages = api('commons.wikimedia.org', titles='|'.join(titles), prop='imageinfo',
                        iiprop='url|extmetadata', iiurlwidth=800)['query']['pages']
            for item in pages.values():
                if not item.get('imageinfo'):
                    continue
                info = item['imageinfo'][0]
                meta = info.get('extmetadata', {})
                license_name = plain(meta.get('LicenseShortName', {}).get('value', ''))
                if not license_name.startswith(('CC BY', 'CC0', 'Public domain')):
                    continue
                row['candidates'].append({'file': item['title'],
                    'description': plain(meta.get('ImageDescription', {}).get('value', '')),
                    'author': plain(meta.get('Artist', {}).get('value', '')),
                    'license': license_name, 'license_url': meta.get('LicenseUrl', {}).get('value', ''),
                    'source': info['descriptionurl'], 'url': info.get('thumburl', info['url']),
                    'original_url': info['url'], 'article_source': article})
        except Exception as error:
            row['error'] = str(error)
        rows = [r for r in rows if r['id'] != place['id']] + [row]
        target.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        print(place['id'], len(row['candidates']), row.get('error', ''), flush=True)
        time.sleep(8)
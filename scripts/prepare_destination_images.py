"""Collect licensed image candidates from already sourced destination articles.

No search-result guessing: the article must be an existing coordinate source.
Candidates are not published until selected in catalogue_images.json.
"""
import html
import json
import re
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'geography'
PUBLIC = ROOT / 'frontend' / 'public' / 'images' / 'destinations'
HEADERS = {'User-Agent': 'VietnamTravelCatalogue/1.0 (local educational application)'}


def request(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 2:
                raise
            delay = error.headers.get('Retry-After', '')
            time.sleep(max(int(delay) if delay.isdigit() else 30 * (attempt + 1), 30))
    raise RuntimeError('Download did not complete')


def api(host, **parameters):
    return json.loads(request(f'https://{host}/w/api.php?' + urllib.parse.urlencode(
        {'action': 'query', 'format': 'json', **parameters})))


def plain(value):
    return html.unescape(re.sub('<[^>]+>', '', value)).strip()


def main():
    PUBLIC.mkdir(parents=True, exist_ok=True)
    path = DATA / 'image_candidates.json'
    rows = json.loads(path.read_text(encoding='utf8')) if path.exists() else []
    done = {row['id'] for row in rows if row.get('image')}
    catalogue = json.loads((ROOT / 'src/rag/catalogue.json').read_text(encoding='utf8'))
    for place in catalogue:
        if not place['coordinates'] or place['id'] in done:
            continue
        row = {'id': place['id'], 'name': place['name']}
        try:
            sources = place.get('coordinate_sources', []) + [place.get('coordinate_source', '')]
            article = next((s for s in sources if 'wikipedia.org/wiki/' in s), None)
            if not article:
                raise ValueError('No destination article linked to coordinate source')
            url = urllib.parse.urlparse(article)
            title = urllib.parse.unquote(url.path.split('/wiki/')[1])
            pages = api(url.netloc, titles=title, redirects=1, prop='pageimages', piprop='name')['query']['pages']
            page = next(iter(pages.values()))
            filename = page.get('pageimage')
            if not filename:
                raise ValueError('Destination article has no lead photograph')
            info = next(iter(api('commons.wikimedia.org', titles='File:' + filename,
                                prop='imageinfo', iiprop='url|extmetadata', iiurlwidth=800)['query']['pages'].values()))
            image = info['imageinfo'][0]
            meta = image['extmetadata']
            license_name = plain(meta.get('LicenseShortName', {}).get('value', ''))
            if not (license_name.startswith(('CC BY', 'CC0', 'Public domain'))):
                raise ValueError('Unsupported or missing license: ' + license_name)
            description = plain(meta.get('ImageDescription', {}).get('value', ''))
            if not description or not meta.get('Artist', {}).get('value'):
                raise ValueError('Missing description or author')
            remote = image.get('thumburl', image['url'])
            picture = request(remote)
            extension = 'jpg' if picture.startswith(b'\xff\xd8\xff') else 'png' if picture.startswith(b'\x89PNG\r\n\x1a\n') else None
            if not extension:
                raise ValueError('Not a JPEG or PNG photograph')
            if len(picture) > 1500000:
                raise ValueError('Photo exceeds 1.5 MB; requires optimization')
            (PUBLIC / (place['id'] + '.' + extension)).write_bytes(picture)
            row.update(article=article, resolved_title=page.get('title'), file=filename,
                       description=description, image={
                           'url': '/images/destinations/' + place['id'] + '.' + extension,
                           'source': image['descriptionurl'], 'author': plain(meta['Artist']['value']),
                           'license': license_name,
                           'license_url': meta.get('LicenseUrl', {}).get('value', ''),
                           'original_url': image['url'], 'retrieved_on': '2026-10-01',
                            'article_source': article})
        except Exception as error:
            row['error'] = str(error)
        rows = [r for r in rows if r['id'] != place['id']] + [row]
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        print(place['id'], 'candidate' if row.get('image') else row['error'], flush=True)
        time.sleep(8)


if __name__ == '__main__':
    main()
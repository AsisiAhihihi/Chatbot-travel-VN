"""Batch article lookups to reduce Wikimedia requests; candidates still require review."""
import json
import time
import urllib.parse
from prepare_destination_images import ROOT, DATA, PUBLIC, api, plain, request


def main():
    catalogue = json.loads((ROOT / 'src/rag/catalogue.json').read_text(encoding='utf8'))
    path = DATA / 'image_candidates.json'
    rows = {r['id']: r for r in json.loads(path.read_text(encoding='utf8'))}
    pending = [p for p in catalogue if p.get('coordinates') and not p.get('image')]
    groups = {}
    for place in pending:
        if rows.get(place['id'], {}).get('image'):
            continue
        sources = place.get('coordinate_sources', []) + [place.get('coordinate_source', '')]
        article = next((s for s in sources if 'wikipedia.org/wiki/' in s), None)
        if not article:
            continue
        url = urllib.parse.urlparse(article)
        title = urllib.parse.unquote(url.path.split('/wiki/')[1]).replace('_', ' ')
        groups.setdefault(url.netloc, []).append((place, article, title))
    files = []
    for host, entries in groups.items():
        try:
            query = api(host, titles='|'.join(title for _, _, title in entries), redirects=1,
                        prop='pageimages', piprop='name')['query']
            aliases = {a['from']: a['to'] for key in ('normalized', 'redirects') for a in query.get(key, [])}
            pages = {p['title']: p for p in query['pages'].values()}
            for place, article, title in entries:
                visited = set()
                while title in aliases and title not in visited:
                    visited.add(title)
                    title = aliases[title]
                page = pages.get(title, {})
                filename = page.get('pageimage')
                if filename:
                    files.append((place, article, title, filename))
            time.sleep(5)
        except Exception as error:
            print(host, str(error), flush=True)
    if not files:
        print('No new article images available.', flush=True)
        return
    pages = api('commons.wikimedia.org', titles='|'.join('File:' + f for _, _, _, f in files),
                prop='imageinfo', iiprop='url|extmetadata', iiurlwidth=800)['query']['pages']
    by_title = {p['title']: p for p in pages.values()}
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for place, article, title, filename in files:
        row = {'id': place['id'], 'name': place['name'], 'article': article,
               'resolved_title': title, 'file': filename}
        try:
            image = by_title['File:' + filename.replace('_', ' ')]['imageinfo'][0]
            meta = image['extmetadata']
            license_name = plain(meta.get('LicenseShortName', {}).get('value', ''))
            if not license_name.startswith(('CC BY', 'CC0', 'Public domain')):
                raise ValueError('Missing or unsupported license')
            description = plain(meta.get('ImageDescription', {}).get('value', ''))
            author = plain(meta.get('Artist', {}).get('value', ''))
            if not description or not author:
                raise ValueError('Missing description or author')
            picture = request(image.get('thumburl', image['url']))
            ext = 'jpg' if picture.startswith(b'\xff\xd8\xff') else 'png' if picture.startswith(b'\x89PNG') else None
            if not ext or len(picture) > 1500000:
                raise ValueError('Invalid or oversized photograph')
            (PUBLIC / (place['id'] + '.' + ext)).write_bytes(picture)
            row.update(description=description, image={
                'url': '/images/destinations/' + place['id'] + '.' + ext,
                'source': image['descriptionurl'], 'author': author, 'license': license_name,
                'license_url': meta.get('LicenseUrl', {}).get('value', ''),
                'original_url': image['url'], 'article_source': article,
                'retrieved_on': '2026-10-01'})
        except Exception as error:
            row['error'] = str(error)
        rows[place['id']] = row
        path.write_text(json.dumps(list(rows.values()), ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        print(place['id'], 'candidate' if row.get('image') else row.get('error'), flush=True)
        time.sleep(3)


if __name__ == '__main__':
    main()
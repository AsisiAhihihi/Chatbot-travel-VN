"""Save article gallery filenames for human review; no automatic image assignment."""
import json
import time
from research_missing_photo_articles import TITLES
from prepare_destination_images import ROOT, DATA, api

if __name__ == '__main__':
    missing = {p['id'] for p in json.loads((ROOT/'src/rag/catalogue.json').read_text(encoding='utf8')) if not p.get('image')}
    rows = []
    for identifier, title in TITLES.items():
        if identifier not in missing:
            continue
        row = {'id':identifier, 'title':title}
        try:
            pages = api('vi.wikipedia.org', titles=title, redirects=1, prop='images', imlimit=50)['query']['pages']
            page = next(iter(pages.values()))
            row.update(resolved=page.get('title'),files=[i['title'] for i in page.get('images',[]) if i['title'].lower().endswith(('.jpg','.jpeg','.png'))])
        except Exception as error:
            row['error'] = str(error)
        rows.append(row)
        (DATA/'missing_photo_galleries.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(identifier,row,flush=True)
        time.sleep(5)
"""Collect licensed article photographs for manual review, never auto-publish."""
import json
import time
from datetime import date
from urllib.parse import quote
from prepare_destination_images import ROOT, DATA, PUBLIC, api, plain, request


def main():
    places = [p for p in json.loads((ROOT/'src/rag/catalogue.json').read_text(encoding='utf8'))
              if p.get('coordinates') and not p.get('image')]
    output = DATA/'new_map_photo_candidates.json'
    rows = json.loads(output.read_text(encoding='utf8')) if output.exists() else []
    done = {r['id'] for r in rows}
    for offset in range(0, len(places), 15):
        pending = [p for p in places[offset:offset+15] if p['id'] not in done]
        if not pending:
            continue
        try:
            query = api('vi.wikipedia.org', titles='|'.join(p['name'] for p in pending), redirects=1,
                        prop='pageimages', piprop='name')['query']
            aliases = {r['from']: r['to'] for key in ('normalized', 'redirects') for r in query.get(key, [])}
            pages = {p['title']: p for p in query['pages'].values()}
            files = []
            for place in pending:
                title = place['name']
                visited = set()
                while title in aliases and title not in visited:
                    visited.add(title)
                    title = aliases[title]
                filename = pages.get(title, {}).get('pageimage')
                if filename:
                    files.append((place, title, filename))
                else:
                    rows.append({'id': place['id'], 'name': place['name'], 'error': 'No lead photo; needs specific article/gallery lookup'})
            if files:
                infos = api('commons.wikimedia.org', titles='|'.join('File:'+f for _,_,f in files),
                            prop='imageinfo', iiprop='url|extmetadata', iiurlwidth=800)['query']['pages']
                by_title = {p['title']:p for p in infos.values()}
                for place,title,filename in files:
                    row = {'id':place['id'], 'name':place['name'], 'resolved_title':title, 'file':filename}
                    try:
                        info = by_title['File:'+filename.replace('_',' ')]['imageinfo'][0]
                        meta = info.get('extmetadata', {})
                        license_name = plain(meta.get('LicenseShortName',{}).get('value',''))
                        author = plain(meta.get('Artist',{}).get('value',''))
                        description = plain(meta.get('ImageDescription',{}).get('value',''))
                        if not license_name.startswith(('CC BY','CC0','Public domain')) or not author or not description:
                            raise ValueError('Missing supported license, author or description')
                        picture = request(info.get('thumburl',info['url']))
                        ext = 'jpg' if picture.startswith(b'\xff\xd8\xff') else 'png' if picture.startswith(b'\x89PNG') else None
                        if not ext or len(picture)>1500000:
                            raise ValueError('Invalid or oversized photo')
                        PUBLIC.mkdir(parents=True,exist_ok=True)
                        local = PUBLIC/(place['id']+'.'+ext)
                        if local.exists():
                            raise ValueError('Existing image file preserved; manual review required')
                        local.write_bytes(picture)
                        row.update(description=description,image={
                            'url':'/images/destinations/'+local.name,'source':info['descriptionurl'],
                            'author':author,'license':license_name,
                            'license_url':meta.get('LicenseUrl',{}).get('value',''),
                            'original_url':info['url'],'article_source':'https://vi.wikipedia.org/wiki/'+quote(title),
                            'retrieved_on':date.today().isoformat()})
                    except Exception as error:
                        row['error']=str(error)
                    rows.append(row)
                    output.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
                    print(place['id'],'candidate' if row.get('image') else row.get('error'),flush=True)
                    time.sleep(1)
            output.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        except Exception as error:
            print('Batch failed:',error,flush=True)
        time.sleep(3)


if __name__=='__main__':
    main()
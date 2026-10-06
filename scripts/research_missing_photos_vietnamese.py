"""Exact Vietnamese phrase queries; research only, no automatic publication."""
import json
from prepare_destination_images import ROOT, DATA, api, plain

def main():
 catalogue=json.loads((ROOT/'src/rag/catalogue.json').read_text(encoding='utf8'))
 path=DATA/'missing_photo_vietnamese_search.json'
 rows=json.loads(path.read_text(encoding='utf8')) if path.exists() else []
 for place in catalogue:
  if place.get('image') or any(r['id']==place['id'] and not r.get('error') for r in rows):continue
  query='"'+place['name']+'"'
  row={'id':place['id'],'query':query,'candidates':[]}
  try:
   pages=api('commons.wikimedia.org',generator='search',gsrsearch=query,gsrnamespace=6,gsrlimit=12,
             prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=800).get('query',{}).get('pages',{})
   for page in pages.values():
    for info in page.get('imageinfo',[]):
     if not page['title'].lower().endswith(('.jpg','.jpeg','.png')):continue
     m=info.get('extmetadata',{})
     row['candidates'].append({'file':page['title'],'description':plain(m.get('ImageDescription',{}).get('value','')),
      'author':plain(m.get('Artist',{}).get('value','')),'license':plain(m.get('LicenseShortName',{}).get('value','')),
      'license_url':m.get('LicenseUrl',{}).get('value',''),'source':info['descriptionurl'],
      'url':info.get('thumburl',info['url']),'original_url':info['url']})
  except Exception as error:row['error']=str(error)
  rows=[r for r in rows if r['id']!=place['id']]+[row]
  path.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  print(place['id'],[(c['file'],c['description'][:100]) for c in row['candidates']],row.get('error',''),flush=True)

if __name__=='__main__':main()
"""Search restrictive filename aliases, saving provenance for review."""
import json
from prepare_destination_images import DATA, api, plain

QUERIES={
 'ca_mau_poi_03':'intitle:Tan intitle:Hung intitle:temple',
 'can_tho_poi_06':'intitle:Ho intitle:Be intitle:beach',
 'can_tho_poi_07':'intitle:Mua intitle:Xuan',
 'dak_lak_poi_05_b':'intitle:Hòn intitle:Yến',
 'dien_bien_poi_03':'intitle:Mường intitle:Phăng',
 'dong_nai_poi_05':'"Bu Gia Map National Park"',
 'ha_tinh_poi_02':'intitle:Nguyễn intitle:Du intitle:memorial',
 'ha_tinh_poi_04':'"Vu Quang National Park"',
 'khanh_hoa_poi_02':'intitle:Bích intitle:Đầm',
 'lai_chau_poi_01':'intitle:Sin intitle:Suoi',
 'lai_chau_poi_02':'intitle:Sin intitle:Ho intitle:District',
 'lam_dong_poi_03':'intitle:Buor',
 'quang_ngai_poi_02':'intitle:My intitle:Khe intitle:Ngai',
 'son_la_poi_05':'intitle:Ngọc intitle:Chiến',
 'tay_ninh_poi_05':'intitle:Chavi',
 'thanh_pho_ho_chi_minh_poi_06_b':'"Phu An bamboo"',
 'tuyen_quang_poi_02_b':'intitle:Lâm intitle:Bình intitle:landscape',
 'tuyen_quang_poi_03':'intitle:Mỹ intitle:Lâm intitle:spring',
}

def main():
 path=DATA/'missing_photo_alias_search.json'
 rows=json.loads(path.read_text(encoding='utf8')) if path.exists() else []
 for identifier,query in QUERIES.items():
  if any(r['id']==identifier and not r.get('error') for r in rows):continue
  row={'id':identifier,'query':query,'candidates':[]}
  try:
   pages=api('commons.wikimedia.org',generator='search',gsrsearch=query,gsrnamespace=6,gsrlimit=15,
             prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=800).get('query',{}).get('pages',{})
   for page in pages.values():
    for info in page.get('imageinfo',[]):
     if not page['title'].lower().endswith(('.jpg','.jpeg','.png','.webm')):continue
     m=info.get('extmetadata',{})
     row['candidates'].append({'file':page['title'],'description':plain(m.get('ImageDescription',{}).get('value','')),
      'author':plain(m.get('Artist',{}).get('value','')),'license':plain(m.get('LicenseShortName',{}).get('value','')),
      'license_url':m.get('LicenseUrl',{}).get('value',''),'source':info['descriptionurl'],
      'url':info.get('thumburl',info['url']),'original_url':info['url']})
  except Exception as error:row['error']=str(error)
  rows=[r for r in rows if r['id']!=identifier]+[row]
  path.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  print(identifier,[(c['file'],c['description'][:180]) for c in row['candidates']],row.get('error',''),flush=True)

if __name__=='__main__':main()
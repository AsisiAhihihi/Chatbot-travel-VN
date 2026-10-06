"""Collect photograph-only candidates for missing places using exact local names."""
import json
from concurrent.futures import ThreadPoolExecutor
from prepare_destination_images import ROOT, DATA, api, plain

QUERIES = {
 'ca_mau_poi_03': '"Tân Hưng"', 'can_tho_poi_06': '"Hồ Bể"',
 'can_tho_poi_07': '"Mùa Xuân"', 'dak_lak_poi_05_b': '"Hòn Yến"',
 'dien_bien_poi_03': '"Mường Phăng"', 'dong_nai_poi_05': '"Bù Gia Mập"',
 'ha_tinh_poi_02': '"Nguyễn Du"', 'ha_tinh_poi_04': '"Vũ Quang"',
 'khanh_hoa_poi_02': '"Bích Đầm"', 'lai_chau_poi_01': '"Sin Suối Hồ"',
 'lai_chau_poi_02': '"Sìn Hồ"', 'lam_dong_poi_03': '"Buôr"',
 'quang_ngai_poi_02': '"Mỹ Khê"', 'son_la_poi_05': '"Ngọc Chiến"',
 'tay_ninh_poi_05': '"Chavi"', 'thanh_pho_ho_chi_minh_poi_06_b': '"Phú An"',
 'tuyen_quang_poi_02_b': '"Lâm Bình"', 'tuyen_quang_poi_03': '"Mỹ Lâm"',
}

def research(item):
 identifier,query=item
 row={'id':identifier,'query':query,'candidates':[]}
 try:
  pages=api('commons.wikimedia.org',generator='search',gsrsearch=query+' filetype:bitmap',
            gsrnamespace=6,gsrlimit=30,prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=800).get('query',{}).get('pages',{})
  for page in pages.values():
   for info in page.get('imageinfo',[]):
    meta=info.get('extmetadata',{})
    row['candidates'].append({'file':page['title'],'description':plain(meta.get('ImageDescription',{}).get('value','')),
     'author':plain(meta.get('Artist',{}).get('value','')),'license':plain(meta.get('LicenseShortName',{}).get('value','')),
     'license_url':meta.get('LicenseUrl',{}).get('value',''),'source':info['descriptionurl'],
     'url':info.get('thumburl',info['url']),'original_url':info['url']})
 except Exception as error: row['error']=str(error)
 print(identifier,len(row['candidates']),row.get('error',''),flush=True)
 return row

if __name__=='__main__':
 missing={p['id'] for p in json.loads((ROOT/'src/rag/catalogue.json').read_text(encoding='utf8')) if not p.get('image')}
 rows=[]
 with ThreadPoolExecutor(max_workers=2) as pool:
  for row in pool.map(research,[(k,v) for k,v in QUERIES.items() if k in missing]):
   rows.append(row)
   (DATA/'final_exact_photo_candidates.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
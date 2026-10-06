"""Persist targeted English/alias searches for manual subject review."""
import json
import time
from prepare_destination_images import ROOT, DATA, api, plain

QUERIES = {
 'ca_mau_poi_03':'"Tan Hung" "Ca Mau"', 'can_tho_poi_06':'"Ho Be" Vietnam',
 'can_tho_poi_07':'"Mua Xuan" Vietnam', 'dak_lak_poi_05_b':'"Hon Yen"',
 'dien_bien_poi_02':'"De Castries" "bunker"', 'dien_bien_poi_03':'"Muong Phang"',
 'dong_nai_poi_05':'"Bu Gia Map" forest', 'dong_thap_poi_03':'"Sa Dec" flower',
 'gia_lai_poi_01':'"Tnung"', 'gia_lai_poi_03_b':'"Ky Co" beach',
 'ha_tinh_poi_02':'"Nguyen Du" memorial', 'ha_tinh_poi_04':'"Vu Quang" forest',
 'hung_yen_poi_01':'"Pho Hien"', 'hung_yen_poi_03':'"Da Hoa" temple',
 'khanh_hoa_poi_02':'"Bich Dam"', 'lai_chau_poi_01':'"Sin Suoi Ho"',
 'lai_chau_poi_02':'"Sin Ho" town', 'lam_dong_poi_02':'"Ta Dung" lake',
 'lam_dong_poi_03':'"Buon Buor"', 'lam_dong_poi_06':'"Phu Quy" island',
 'lang_son_poi_02':'"Bac Son" valley', 'lao_cai_poi_03':'"Bac Ha" town',
 'lao_cai_poi_05':'"Tram Tau"', 'nghe_an_poi_04':'"Thanh Chuong" tea',
 'ninh_binh_poi_03':'"Hang Mua"', 'phu_tho_poi_02':'"Long Coc" tea',
 'phu_tho_poi_03':'"Tam Dao" town', 'phu_tho_poi_03_b':'"Tay Thien"',
 'phu_tho_poi_05_b':'"Ban Lac"', 'phu_tho_poi_06_b':'"Thac Bo"',
 'quang_ngai_poi_02':'"My Khe" "Quang Ngai"', 'quang_ninh_poi_02':'"Bai Chay" beach',
 'quang_ninh_poi_03':'"Hon Gai"', 'son_la_poi_02':'"Moc Chau"',
 'son_la_poi_04':'"Quynh Nhai"', 'son_la_poi_05':'"Ngoc Chien"',
 'tay_ninh_poi_04':'"Tan Lap" floating', 'tay_ninh_poi_05':'"Chavi" garden',
 'thai_nguyen_poi_01':'"Dinh Hoa" memorial', 'thai_nguyen_poi_04':'"Phuong Hoang" cave',
 'thanh_hoa_poi_04':'"Sam Son" beach', 'thanh_hoa_poi_05':'"Cam Luong" fish',
 'thanh_pho_ho_chi_minh_poi_06_b':'"Phu An" bamboo', 'tuyen_quang_poi_02_b':'"Lam Binh"',
 'tuyen_quang_poi_03':'"My Lam" springs', 'tuyen_quang_poi_06':'"Hoang Su Phi"',
 'vinh_long_poi_02':'"Mang Thit" brick',
}

if __name__ == '__main__':
    path=DATA/'missing_photo_targeted_search.json'
    rows=json.loads(path.read_text(encoding='utf8')) if path.exists() else []
    done={r['id'] for r in rows if not r.get('error')}
    for identifier,query in QUERIES.items():
        if identifier in done: continue
        row={'id':identifier,'query':query,'candidates':[]}
        try:
            pages=api('commons.wikimedia.org',generator='search',gsrsearch=query+' filetype:bitmap',gsrnamespace=6,gsrlimit=8,prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=800).get('query',{}).get('pages',{})
            for p in pages.values():
                for info in p.get('imageinfo',[]):
                    m=info.get('extmetadata',{})
                    row['candidates'].append({'file':p['title'],'description':plain(m.get('ImageDescription',{}).get('value','')),
                        'author':plain(m.get('Artist',{}).get('value','')),'license':plain(m.get('LicenseShortName',{}).get('value','')),
                        'license_url':m.get('LicenseUrl',{}).get('value',''),'source':info['descriptionurl'],
                        'url':info.get('thumburl',info['url']),'original_url':info['url']})
        except Exception as error: row['error']=str(error)
        rows=[r for r in rows if r['id']!=identifier]+[row]
        path.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(identifier,[(c['file'],c['description'][:100]) for c in row['candidates']],row.get('error',''),flush=True)
        time.sleep(8)
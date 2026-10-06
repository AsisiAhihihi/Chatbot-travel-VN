"""Publish reviewed exact-subject photos; leave ambiguous article lead images out."""
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPROVED = {
 'an_giang_poi_02_b','an_giang_poi_05_b','bac_ninh_poi_02','bac_ninh_poi_02_b',
 'bac_ninh_poi_03','bac_ninh_poi_04','bac_ninh_poi_05_b','can_tho_poi_02',
 'can_tho_poi_07_b','da_nang_poi_02','dak_lak_poi_01_b','dak_lak_poi_05',
 'dong_nai_poi_01','gia_lai_poi_04','ha_noi_poi_02','ha_tinh_poi_03',
 'ha_tinh_poi_04_b','hai_phong_poi_01_b','hue_poi_03_b','hue_poi_05',
 'khanh_hoa_poi_01','khanh_hoa_poi_03','khanh_hoa_poi_03_b','khanh_hoa_poi_05',
 'lam_dong_poi_01','lam_dong_poi_01_b','lam_dong_poi_04','lam_dong_poi_05',
 'lam_dong_poi_05_b','lang_son_poi_04','lao_cai_poi_01_b','lao_cai_poi_02',
 'lao_cai_poi_03_b','nghe_an_poi_03','ninh_binh_poi_01_b','ninh_binh_poi_03_b',
 'phu_tho_poi_02_b','phu_tho_poi_06','quang_ngai_poi_01','quang_ngai_poi_05',
 'quang_tri_poi_02','quang_tri_poi_02_b','quang_tri_poi_04_b','son_la_poi_03',
 'thanh_hoa_poi_03','thanh_pho_ho_chi_minh_poi_05','thanh_pho_ho_chi_minh_poi_05_b',
 'thanh_pho_ho_chi_minh_poi_06','tuyen_quang_poi_01','tuyen_quang_poi_04',
 'tuyen_quang_poi_04_b','tuyen_quang_poi_05',
}


def main():
    path=ROOT/'src/rag/catalogue_images.json'
    backup=ROOT/'data/backups'/('images_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True)
    shutil.copy2(path,backup/path.name)
    records={r['id']:r for r in json.loads(path.read_text(encoding='utf8'))}
    candidates=json.loads((ROOT/'data/geography/new_map_photo_candidates.json').read_text(encoding='utf8'))
    added=[]
    for row in candidates:
        if row['id'] not in APPROVED or not row.get('image') or row['id'] in records:
            continue
        image=row['image']
        assert (ROOT/'frontend/public'/image['url'].lstrip('/')).is_file()
        assert image['author'] and image['license'] and image['source']
        records[row['id']]={'id':row['id'],'image':image,'review_note':row['description']}
        added.append(row['id'])
    path.write_text(json.dumps(list(records.values()),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    subprocess.run([sys.executable,str(ROOT/'scripts/build_catalogue.py')],cwd=ROOT,check=True)
    places=json.loads((ROOT/'src/rag/catalogue.json').read_text(encoding='utf8'))
    report={'added':added,'with_images':sum(bool(p.get('image')) for p in places),
            'missing':[{'id':p['id'],'name':p['name']} for p in places if not p.get('image')]}
    (ROOT/'data/geography/new_map_photo_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'added':len(added),'with_images':report['with_images'],'missing':len(report['missing'])}))


if __name__=='__main__':
    main()
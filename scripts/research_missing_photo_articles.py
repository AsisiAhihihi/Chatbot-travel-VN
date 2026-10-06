"""Gather missing-place photo evidence from destination articles, without publishing."""
import json
import time
from prepare_destination_images import ROOT, DATA, api, plain

TITLES = {
 'ca_mau_poi_03': 'Đình Tân Hưng', 'can_tho_poi_06': 'Hồ Bể',
 'can_tho_poi_07': 'Khu du lịch Mùa Xuân', 'dak_lak_poi_05_b': 'Hòn Yến',
 'dien_bien_poi_02': 'Hầm Đờ Cát', 'dien_bien_poi_03': 'Mường Phăng',
 'dong_nai_poi_05': 'Vườn quốc gia Bù Gia Mập', 'dong_thap_poi_03': 'Làng hoa Sa Đéc',
 'gia_lai_poi_01': 'Hồ Tơ Nưng', 'gia_lai_poi_03_b': 'Kỳ Co',
 'ha_tinh_poi_02': 'Khu lưu niệm Nguyễn Du', 'ha_tinh_poi_04': 'Vườn quốc gia Vũ Quang',
 'hung_yen_poi_01': 'Phố Hiến', 'hung_yen_poi_01_b': 'Chùa Chuông (Hưng Yên)',
 'hung_yen_poi_02': 'Chùa Nôm', 'hung_yen_poi_03': 'Đền Chử Đồng Tử',
 'khanh_hoa_poi_02': 'Bích Đầm', 'khanh_hoa_poi_04': 'Hang Rái',
 'khanh_hoa_poi_05_b': 'Tháp Po Klong Garai', 'lai_chau_poi_01': 'Sin Suối Hồ',
 'lai_chau_poi_02': 'Sìn Hồ', 'lam_dong_poi_02': 'Hồ Tà Đùng',
 'lam_dong_poi_03': 'Buôn Buôr', 'lam_dong_poi_06': 'Phú Quý',
 'lang_son_poi_02': 'Bắc Sơn (thị trấn)', 'lao_cai_poi_03': 'Bắc Hà (thị trấn)',
 'lao_cai_poi_05': 'Trạm Tấu (thị trấn)', 'nghe_an_poi_04': 'Thanh Chương',
 'ninh_binh_poi_03': 'Hang Múa', 'phu_tho_poi_02': 'Long Cốc',
 'phu_tho_poi_03': 'Tam Đảo (thị trấn)', 'phu_tho_poi_03_b': 'Tây Thiên',
 'phu_tho_poi_05_b': 'Bản Lác', 'phu_tho_poi_06_b': 'Động Thác Bờ',
 'quang_ngai_poi_02': 'Mỹ Khê (Quảng Ngãi)', 'quang_ninh_poi_02': 'Bãi Cháy',
 'quang_ninh_poi_03': 'Hòn Gai', 'son_la_poi_02': 'Mộc Châu',
 'son_la_poi_04': 'Quỳnh Nhai', 'son_la_poi_05': 'Ngọc Chiến',
 'tay_ninh_poi_04': 'Làng nổi Tân Lập', 'tay_ninh_poi_05': 'Chavi Garden',
 'thai_nguyen_poi_01': 'An toàn khu Định Hóa', 'thai_nguyen_poi_04': 'Hang Phượng Hoàng',
 'thanh_hoa_poi_04': 'Sầm Sơn', 'thanh_hoa_poi_05': 'Suối cá thần Cẩm Lương',
 'thanh_pho_ho_chi_minh_poi_06_b': 'Làng tre Phú An', 'tuyen_quang_poi_02_b': 'Lâm Bình',
 'tuyen_quang_poi_03': 'Suối khoáng Mỹ Lâm', 'tuyen_quang_poi_06': 'Hoàng Su Phì',
 'vinh_long_poi_02': 'Mang Thít',
}


def main():
    catalogue = json.loads((ROOT/'src/rag/catalogue.json').read_text(encoding='utf8'))
    missing = {p['id'] for p in catalogue if not p.get('image')}
    path = DATA/'missing_photo_article_candidates.json'
    rows = json.loads(path.read_text(encoding='utf8')) if path.exists() else []
    done = {r['id'] for r in rows if r.get('candidates')}
    for identifier, title in TITLES.items():
        if identifier not in missing or identifier in done:
            continue
        row = {'id': identifier, 'article_requested': title, 'candidates': []}
        try:
            pages = api('vi.wikipedia.org', titles=title, redirects=1, prop='pageimages', piprop='name')['query']['pages']
            page = next(iter(pages.values()))
            row['article_resolved'] = page.get('title')
            file = page.get('pageimage')
            if file:
                infos = api('commons.wikimedia.org', titles='File:'+file, prop='imageinfo', iiprop='url|extmetadata', iiurlwidth=800)['query']['pages']
                for item in infos.values():
                    for info in item.get('imageinfo', []):
                        meta = info.get('extmetadata', {})
                        row['candidates'].append({'file': item['title'],
                            'description': plain(meta.get('ImageDescription', {}).get('value','')),
                            'author': plain(meta.get('Artist', {}).get('value','')),
                            'license': plain(meta.get('LicenseShortName', {}).get('value','')),
                            'license_url': meta.get('LicenseUrl', {}).get('value',''),
                            'source': info['descriptionurl'], 'url': info.get('thumburl',info['url']),
                            'original_url': info['url']})
        except Exception as error:
            row['error'] = str(error)
        rows = [r for r in rows if r['id'] != identifier] + [row]
        path.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(identifier, row.get('error',[(p['file'],p['license']) for p in row['candidates']]),flush=True)
        time.sleep(5)


if __name__ == '__main__':
    main()
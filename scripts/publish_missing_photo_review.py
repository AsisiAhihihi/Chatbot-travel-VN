"""Publish a manually reviewed selection from saved research evidence."""
import json
import shutil
import subprocess
import sys
from datetime import datetime
from prepare_destination_images import ROOT, DATA, PUBLIC, request

SELECTION = {
 'hung_yen_poi_03': ('File:Den Da Hoa (Den Chu Dong Tu - Tien Dung).jpg', 'Đền Đa Hòa thờ Chử Đồng Tử và Tiên Dung; không phải đền Dạ Trạch'),
 'lam_dong_poi_02': ('File:Sailing over Ta Dung Lake.webm', 'Khung hình từ video hành trình trên hồ Tà Đùng, tháng 1/2024'),
 'gia_lai_poi_03_b': ('File:Ky Co beach, Quy Nhon city, Binh Dinh province, Vietnam.jpg', 'Bãi biển Kỳ Co'),
 'phu_tho_poi_02': ('File:Clean weeds from tea garden - Flickr - Son Hoa Nguyen.jpg', 'Làm cỏ tại đồi chè Long Cốc, ảnh năm 2019'),
 'thai_nguyen_poi_01': ('File:ATK Dinh Hoa.jpg', 'Di tích ATK Định Hóa, ảnh nguồn năm 2007'),
 'nghe_an_poi_04': ('File:Đồi chè Thanh Chương.jpg', 'Đồi chè Thanh Chương, ảnh tháng 6/2022'),
 'hung_yen_poi_01': ('File:Văn miếu Xích Đằng 02.JPG', 'Văn miếu Xích Đằng thuộc không gian di sản Phố Hiến'),
 'khanh_hoa_poi_04': ('File:Hang Rái in Ninh Thuan Province, Vietnam.jpg', 'Cảnh Hang Rái, ảnh năm 2018'),
 'khanh_hoa_poi_05_b': ('File:Po Klong Garai 00.jpg', 'Tháp cổng trong quần thể Po Klong Garai'),
 'gia_lai_poi_01': ('File:Biển Hồ, TP Pleiku, Gia Lai.jpg', 'Cảnh Biển Hồ tại Pleiku'),
 'lam_dong_poi_06': ('File:Chualinhsonphuquy.jpg', 'Chùa Linh Sơn trên đảo Phú Quý; không phải bến tàu'),
 'phu_tho_poi_03': ('File:Đền Bà Chúa Thượng Ngàn Tam Đảo.jpg', 'Đền Bà Chúa Thượng Ngàn tại Tam Đảo, ảnh năm 2013'),
 'phu_tho_poi_03_b': ('File:Đền thờ Thần Thanh Sơn Đại Vương - Tây Thiên, Tam Đảo - panoramio.jpg', 'Đền thờ Thần Thanh Sơn Đại Vương trong khu danh thắng Tây Thiên'),
 'tuyen_quang_poi_06': ('File:Bản Phùng - NKS.jpg', 'Cảnh bản Phùng, Hoàng Su Phì vào mùa lúa chín'),
 'vinh_long_poi_02': ('File:Brick making village in Mang Thit, Vinh Long, Vietnam.jpg', 'Lò gạch tại làng nghề Mang Thít, Vĩnh Long'),
 'dien_bien_poi_02': ('File:Bunker of Colonel de Castries - Dien Bien Phu - Vietnam - 01 (48168749426).jpg', 'Hầm chỉ huy Đờ Cát tại Điện Biên Phủ'),
 'dong_thap_poi_03': ('File:LanghoaSaDec.jpg', 'Hoa được vận chuyển tại làng hoa Sa Đéc dịp Tết 2015'),
 'lang_son_poi_02': ('File:Rice Paddies - Bac Son Valley, Northeast Vietnam - 10 Dec. 2013.jpg', 'Ruộng trong thung lũng Bắc Sơn, ảnh năm 2013'),
 'lao_cai_poi_03': ('File:2007-12-09 Bac Ha market, Flower Hmong girl.jpg', 'Sinh hoạt tại chợ Bắc Hà, ảnh năm 2007'),
 'lao_cai_poi_05': ('File:Trạm Tấu fields.jpg', 'Cảnh ruộng ở địa bàn Trạm Tấu; không phải cơ sở suối khoáng'),
 'ninh_binh_poi_03': ('File:View from Hang Mua.jpg', 'Cảnh nhìn từ điểm ngắm Hang Múa'),
 'phu_tho_poi_05_b': ('File:Cánh đồng bản Lác.jpg', 'Cánh đồng tại bản Lác, Mai Châu'),
 'phu_tho_poi_06_b': ('File:DongThacBo.jpg', 'Lối vào Động Thác Bờ trên hồ Hòa Bình; không phải đền Thác Bờ'),
 'quang_ninh_poi_02': ('File:Bai Chay beach, Ha Long, Vietnam, 20240129 0915 3958.jpg', 'Bãi biển Bãi Cháy, ảnh tháng 1/2024'),
 'quang_ninh_poi_03': ('File:Mặt tiền và hông nhà thờ Hòn Gai.jpg', 'Nhà thờ Hòn Gai trong khu vực Hòn Gai; ảnh không đại diện bến tàu'),
 'son_la_poi_02': ('File:Mộc Châu District, Vietnam (Unsplash).jpg', 'Cảnh quan địa bàn Mộc Châu'),
 'son_la_poi_04': ('File:Quỳnh Nhai - panoramio.jpg', 'Cảnh quan tại Quỳnh Nhai'),
 'tay_ninh_poi_04': ('File:Tháp Quan Sát.jpg', 'Tháp quan sát tại làng nổi Tân Lập'),
 'thai_nguyen_poi_04': ('File:Phuong Hoang Cave, Vo Nhai.jpg', 'Hang Phượng Hoàng tại Võ Nhai, Thái Nguyên'),
 'thanh_hoa_poi_04': ('File:Bãi biển Sầm Sơn.JPG', 'Bãi biển Sầm Sơn, Thanh Hóa'),
 'thanh_hoa_poi_05': ('File:Suoi ca Cam Luong.jpg', 'Cá tại suối Cẩm Lương, Cẩm Thủy'),
}

def main():
    path=ROOT/'src/rag/catalogue_images.json'
    backup=ROOT/'data/backups'/('missing_photo_review_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True)
    shutil.copy2(path,backup/path.name)
    records={r['id']:r for r in json.loads(path.read_text(encoding='utf8'))}
    evidence=json.loads((DATA/'missing_photo_targeted_search.json').read_text(encoding='utf8'))
    report={'added':[],'failed':[]}
    for identifier,(filename,caption) in SELECTION.items():
        if identifier in records:continue
        try:
            photo=next(c for r in evidence if r['id']==identifier for c in r['candidates'] if c['file']==filename)
            assert photo['author'] and photo['description']
            assert photo['license'].startswith(('CC BY','CC0','Public domain'))
            picture=request(photo['url'])
            ext='jpg' if picture.startswith(b'\xff\xd8\xff') else 'png' if picture.startswith(b'\x89PNG\r\n\x1a\n') else None
            assert ext and len(picture)<=6000000,'Invalid or oversized payload'
            destination=PUBLIC/(identifier+'.'+ext)
            destination.write_bytes(picture)
            image={k:photo[k] for k in ('source','author','license','original_url')}
            image.update(url='/images/destinations/'+destination.name,caption=caption,
                         license_url=photo['license_url'] or photo['source'],
                         changes='Bản xem trước từ nguồn; không chỉnh sửa nội dung.',
                         retrieved_on=datetime.now().date().isoformat())
            if filename.endswith('.webm'):
                image['changes']='Ảnh xem trước (khung hình) trích từ video nguồn, không phải ảnh chụp riêng.'
            records[identifier]={'id':identifier,'image':image,'review_note':photo['description']}
            path.write_text(json.dumps(list(records.values()),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            report['added'].append(identifier)
            print(identifier,'published',flush=True)
        except Exception as error:
            report['failed'].append({'id':identifier,'error':str(error)})
            print(identifier,str(error),flush=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/build_catalogue.py')],cwd=ROOT,check=True)
    (DATA/'missing_photo_review_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':main()
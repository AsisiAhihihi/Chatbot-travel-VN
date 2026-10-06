"""Fetch metadata for individually reviewed subjects; never publish search guesses."""
import json
from prepare_destination_images import DATA, api, plain

SUBJECTS = {
 'hung_yen_poi_03': ('Den Da Hoa (Den Chu Dong Tu - Tien Dung).jpg', 'Đền Đa Hòa thờ Chử Đồng Tử và Tiên Dung; không phải đền Dạ Trạch'),
 'lam_dong_poi_02': ('Sailing over Ta Dung Lake.webm', 'Khung hình từ video hành trình trên hồ Tà Đùng, tháng 1/2024'),
 'gia_lai_poi_03_b': ('Ky Co beach, Quy Nhon city, Binh Dinh province, Vietnam.jpg', 'Bãi biển Kỳ Co'),
 'phu_tho_poi_02': ('Clean weeds from tea garden - Flickr - Son Hoa Nguyen.jpg', 'Làm cỏ tại đồi chè Long Cốc, ảnh năm 2019'),
 'thai_nguyen_poi_01': ('ATK Dinh Hoa.jpg', 'Di tích ATK Định Hóa, ảnh nguồn năm 2007'),
 'nghe_an_poi_04': ('Đồi chè Thanh Chương.jpg', 'Đồi chè Thanh Chương, ảnh tháng 6/2022'),
 'hung_yen_poi_01': ('Văn miếu Xích Đằng 02.JPG', 'Văn miếu Xích Đằng thuộc không gian di sản Phố Hiến'),
 'khanh_hoa_poi_04': ('Hang Rái in Ninh Thuan Province, Vietnam.jpg', 'Cảnh Hang Rái, ảnh năm 2018'),
 'khanh_hoa_poi_05_b': ('Po Klong Garai 00.jpg', 'Tháp cổng trong quần thể Po Klong Garai'),
 'gia_lai_poi_01': ('Biển Hồ, TP Pleiku, Gia Lai.jpg', 'Cảnh Biển Hồ tại Pleiku'),
 'lam_dong_poi_06': ('Chualinhsonphuquy.jpg', 'Chùa Linh Sơn trên đảo Phú Quý; không phải bến tàu'),
 'phu_tho_poi_03': ('Đền Bà Chúa Thượng Ngàn Tam Đảo.jpg', 'Đền Bà Chúa Thượng Ngàn tại Tam Đảo, ảnh năm 2013'),
 'phu_tho_poi_03_b': ('Đền thờ Thần Thanh Sơn Đại Vương - Tây Thiên, Tam Đảo - panoramio.jpg', 'Đền thờ Thần Thanh Sơn Đại Vương trong khu danh thắng Tây Thiên'),
}

def main():
 path=DATA/'missing_photo_targeted_search.json'
 rows=json.loads(path.read_text(encoding='utf8'))
 for identifier,(filename,caption) in SUBJECTS.items():
  try:
   page=next(iter(api('commons.wikimedia.org',titles='File:'+filename,prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=800)['query']['pages'].values()))
   info=page['imageinfo'][0]; meta=info['extmetadata']
   candidate={'file':page['title'],'description':plain(meta.get('ImageDescription',{}).get('value','')),
    'author':plain(meta.get('Artist',{}).get('value','')),'license':plain(meta.get('LicenseShortName',{}).get('value','')),
    'license_url':meta.get('LicenseUrl',{}).get('value',''),'source':info['descriptionurl'],
    'url':info.get('thumburl',info['url']),'original_url':info['url']}
   assert candidate['description'] and candidate['author']
   row=next((r for r in rows if r['id']==identifier),None)
   if row is None:
    row={'id':identifier,'candidates':[]};rows.append(row)
   row['candidates']=[c for c in row['candidates'] if c['file']!=candidate['file']]+[candidate]
   path.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
   print(identifier,candidate['license'],candidate['description'][:160],flush=True)
  except Exception as error:
   print(identifier,'ERROR',str(error),flush=True)

if __name__=='__main__':main()
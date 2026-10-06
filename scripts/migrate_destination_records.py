"""Reviewed, repeatable v2 -> v2.1 migration. No geocoding or external facts.

Descriptions below allocate only facts present in the original grouped sections.
Unallocated group prose is retained in the pre-migration backup, not copied to children.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# name | description | experience. This is a data migration, not response templates.
REVIEWED = {
    'an_giang_poi_02': ('Núi Sam|Khu vực hành hương và ngắm cảnh ở Châu Đốc, với các di tích quanh chân núi.|Ngắm cảnh và tìm hiểu di tích trong khu vực.', 'Chùa Tây An|Công trình tôn giáo nổi bật với kiến trúc chùa và không gian thờ tự.|Vãn cảnh chùa, tìm hiểu lịch sử và kiến trúc.'),
    'an_giang_poi_05': ('Phú Quốc|Điểm đến biển đảo với nhiều khu vực, làng chài và cảnh quan đảo.|Khám phá cảnh biển và làng chài theo khu vực lựa chọn.', 'Bãi Sao|Bãi biển ở phần nam đảo Phú Quốc, nổi bật với cát sáng màu và cảnh nước biển.|Dạo biển, chụp ảnh và tắm biển khi điều kiện cho phép.'),
    'bac_ninh_poi_02': ('Chùa Dâu|Chùa gắn với lịch sử Phật giáo vùng Luy Lâu, nổi bật với tháp Hòa Phong.|Thăm chùa, tìm hiểu lịch sử và quan sát kiến trúc.', 'Chùa Bút Tháp|Ngôi chùa nổi bật về kiến trúc, nghệ thuật điêu khắc và tượng Quan Âm.|Thăm cổ tự, quan sát tượng và các chi tiết kiến trúc.'),
    'bac_ninh_poi_03': ('Đình Bảng|Di tích kiến trúc đình làng của vùng văn hóa Kinh Bắc.|Tham quan đình và tìm hiểu kiến trúc làng quê.', 'Hội Lim|Lễ hội gắn với quan họ và sinh hoạt văn hóa Kinh Bắc.|Xem quan họ khi có chương trình hoặc đúng dịp lễ hội.'),
    'bac_ninh_poi_04': ('Chùa Vĩnh Nghiêm|Ngôi chùa gắn với Phật giáo Trúc Lâm và di sản mộc bản.|Vãn cảnh, tìm hiểu di sản và kiến trúc chùa.', 'Chùa Bổ Đà|Cổ tự nổi bật với tường đất và vườn tháp.|Vãn cảnh và quan sát kiến trúc, vườn tháp.'),
    'can_tho_poi_05': ('Khu du lịch Mùa Xuân|Khu du lịch sinh thái có cảnh cây xanh và chim.|Chọn tuyến tham quan được phục vụ, quan sát sinh cảnh.', 'Lung Ngọc Hoàng|Khu bảo tồn đất ngập nước với cảnh rừng và sinh cảnh tự nhiên.|Tìm hiểu sinh cảnh theo tuyến được phép phục vụ.'),
    'da_nang_poi_02': ('Sơn Trà|Bán đảo có rừng và cảnh ven biển.|Ngắm cảnh bán đảo ở các khu vực được phép.', 'Ngũ Hành Sơn|Cụm núi đá với hang động, chùa và điểm ngắm cảnh.|Tham quan tuyến hang, chùa và ngắm cảnh.'),
    'dak_lak_poi_01': ('Buôn Đôn|Vùng gắn với văn hóa cộng đồng và cảnh quan sông Sêrêpốk.|Tìm hiểu làng và văn hóa bản địa.', 'Vườn quốc gia Yok Đôn|Vườn quốc gia có rừng khộp và trải nghiệm quan sát voi.|Chọn chương trình thiên nhiên, quan sát voi khi được phục vụ.'),
    'dak_lak_poi_05': ('Mũi Điện|Mũi biển nổi bật với hải đăng và cảnh bình minh.|Ngắm cảnh biển và bình minh ở khu vực an toàn.', 'Hòn Yến|Cảnh quan đảo đá và vùng bờ.|Ngắm cảnh đảo đá ở khu vực được phép.'),
    'gia_lai_poi_04': ('Eo Gió|Cảnh quan bờ biển với vách đá và lối ngắm biển.|Dạo và ngắm cảnh bờ biển.', 'Kỳ Co|Bãi biển có trải nghiệm nghỉ và ngắm biển riêng.|Dạo bãi biển, chọn hoạt động theo điều kiện phục vụ.'),
    'ha_tinh_poi_04': ('Vườn quốc gia Vũ Quang|Vườn quốc gia có rừng và giá trị bảo tồn, đa dạng sinh học.|Chọn tuyến thiên nhiên được quản lý chấp thuận.', 'Hồ Ngàn Trươi|Hồ chứa ở khu vực lân cận Vũ Quang với cảnh mặt nước.|Ngắm hồ ở vị trí được phép.'),
    'hai_phong_poi_01': ('Cát Bà|Đảo có rừng, làng, bãi biển và vườn quốc gia.|Khám phá cảnh đảo và thiên nhiên theo tuyến được phục vụ.', 'Vịnh Lan Hạ|Vịnh với đảo đá và vùng nước quanh khu vực Cát Bà.|Chọn tour vịnh, kayak hoặc thuyền theo dịch vụ được phép.'),
    'hai_phong_poi_04': ('Côn Sơn|Khu di tích gắn với Nguyễn Trãi, cảnh núi và chùa.|Tham quan di tích, tìm hiểu lịch sử và cảnh núi chùa.', 'Kiếp Bạc|Khu di tích gắn với Trần Hưng Đạo và lịch sử thời Trần.|Tham quan di tích và tìm hiểu lịch sử thời Trần.'),
    'hue_poi_03': ('Lăng Tự Đức|Lăng có cảnh hồ, sân và kiến trúc hòa vào thiên nhiên.|Tham quan lăng, tìm hiểu tiểu sử vua và kiến trúc.', 'Lăng Khải Định|Lăng nổi bật với sự phối hợp phong cách kiến trúc, trang trí và bậc thang.|Tham quan lăng và quan sát các chi tiết mỹ thuật.'),
    'hung_yen_poi_01': ('Phố Hiến|Khu vực di sản của một thương cảng xưa.|Tìm hiểu lịch sử giao thương và di tích trong khu vực.', 'Chùa Chuông|Di tích tôn giáo cụ thể trong khu vực Phố Hiến.|Vãn cảnh và tìm hiểu kiến trúc chùa.'),
    'khanh_hoa_poi_03': ('Vịnh Vĩnh Hy|Vịnh biển với nước, núi và cảnh bờ.|Ngắm vịnh, chọn tour biển được phép tổ chức.', 'Vườn quốc gia Núi Chúa|Vườn quốc gia có hệ sinh thái riêng, cảnh rừng và bảo tồn.|Chọn tuyến thiên nhiên được phép tổ chức.'),
    'khanh_hoa_poi_05': ('Làng gốm Bàu Trúc|Làng gốm Chăm nổi bật với phương pháp chế tác thủ công.|Tìm hiểu nghề truyền thống và cách chế tác gốm.', 'Tháp Po Klong Garai|Cụm tháp Chăm với giá trị di sản kiến trúc.|Tham quan tháp và tìm hiểu kiến trúc Chăm.'),
    'lam_dong_poi_01': ('Đà Lạt|Đô thị cao nguyên nổi bật với hồ, rừng thông và kiến trúc.|Dạo phố, chọn hồ hoặc công trình để tham quan.', 'Bảo Lộc|Điểm đến riêng gắn với vùng chè và cảnh thác.|Khám phá cảnh chè và thác theo tuyến riêng.'),
    'lam_dong_poi_05': ('Dục Thanh|Di tích trường học gắn với thời gian Nguyễn Tất Thành dạy học.|Tham quan và tìm hiểu lịch sử trường học.', 'Tháp Po Sah Inư|Cụm tháp Chăm với nội dung tham quan kiến trúc riêng.|Tham quan và tìm hiểu kiến trúc tháp Chăm.'),
    'lao_cai_poi_01': ('Sa Pa|Điểm đến vùng cao với ruộng bậc thang, bản làng và khí hậu mát.|Khám phá bản làng và cảnh ruộng theo mùa.', 'Fansipan|Ngọn núi có cảnh núi và trải nghiệm lên cao riêng.|Chọn cáp treo hoặc trekking theo điều kiện dịch vụ và thể lực.'),
    'lao_cai_poi_03': ('Bắc Hà|Vùng văn hóa và cảnh quan.|Khám phá cảnh quan và tìm hiểu văn hóa địa phương.', 'Dinh Hoàng A Tưởng|Công trình nổi bật với bố cục kiến trúc và lịch sử gia đình chủ nhân.|Tham quan dinh, tìm hiểu kiến trúc và lịch sử.'),
    'ninh_binh_poi_01': ('Tràng An|Cảnh quan núi đá vôi, hang và di tích, nổi bật với hành trình thuyền theo tuyến.|Đi thuyền, ngắm núi đá, qua hang và tìm hiểu di tích theo tuyến.', 'Tam Cốc|Cảnh quan sông Ngô Đồng giữa núi đá và ruộng.|Đi thuyền trên sông, ngắm ruộng và núi theo mùa.'),
    'ninh_binh_poi_03': ('Hang Múa|Điểm ngắm cảnh từ trên cao với tuyến bậc lên và góc nhìn vùng Tam Cốc.|Lên điểm ngắm cảnh nếu đủ thể lực và điều kiện cho phép.', 'Vườn quốc gia Cúc Phương|Vườn quốc gia có rừng và giá trị bảo tồn.|Chọn tuyến thiên nhiên, tìm hiểu rừng và sinh thái.'),
    'ninh_binh_poi_05': ('Đền Trần|Di tích ở khu vực Nam Định cũ gắn với thời Trần và giá trị tưởng niệm.|Tham quan và tìm hiểu lịch sử thời Trần.', 'Chùa Phổ Minh|Di tích nổi bật với kiến trúc chùa và tháp Phổ Minh.|Vãn cảnh, tìm hiểu kiến trúc và tháp.'),
    'phu_tho_poi_02': ('Đồi chè Long Cốc|Cảnh quan nổi bật với các đồi chè.|Ngắm đồi chè, xin phép khi vào khu canh tác.', 'Vườn quốc gia Xuân Sơn|Vườn quốc gia có rừng và núi đá.|Chọn tuyến sinh thái được phục vụ.'),
    'phu_tho_poi_03': ('Tam Đảo|Điểm nghỉ vùng núi với cảnh thị trấn và rừng.|Dạo thị trấn, ngắm cảnh núi.', 'Tây Thiên|Khu danh thắng tâm linh với di tích và không gian tín ngưỡng.|Vãn cảnh theo tuyến lựa chọn.'),
    'phu_tho_poi_05': ('Mai Châu|Thung lũng có cảnh ruộng, bản làng và văn hóa Thái.|Khám phá cảnh quan thung lũng và tìm hiểu văn hóa địa phương.', 'Bản Lác|Điểm cộng đồng trong vùng Mai Châu với nhà sàn và sinh hoạt nông thôn.|Dạo bản, tìm hiểu đời sống; chọn lưu trú nhà sàn khi hộ dân phục vụ.'),
    'phu_tho_poi_06': ('Hồ Hòa Bình|Hồ chứa có cảnh đảo, núi và cộng đồng ven nước.|Ngắm hồ bằng thuyền theo tuyến được phục vụ.', 'Thác Bờ|Khu vực có điểm tín ngưỡng và hang riêng.|Vãn cảnh hoặc thăm động theo tuyến được phục vụ.'),
    'quang_tri_poi_01': ('Cầu Hiền Lương|Công trình trong cụm di tích gắn với lịch sử chia cắt và thống nhất đất nước.|Tham quan, đọc trưng bày và nghe giới thiệu lịch sử.', 'Sông Bến Hải|Dòng sông gắn với cụm di tích về thời kỳ đất nước bị chia cắt sau năm 1954.|Ngắm cảnh sông và tìm hiểu dấu tích lịch sử theo tuyến.'),
    'thanh_pho_ho_chi_minh_poi_04': ('Bãi Sau|Bãi biển ở Vũng Tàu thường được chọn để nghỉ và tắm biển.|Dạo bãi biển, tắm tại nơi đang cho phép.', 'Bãi Trước|Bãi ven đô thị Vũng Tàu phù hợp dạo và ngắm cảnh.|Dạo ven bờ và ngắm cảnh đô thị, bến.'),
    'thanh_pho_ho_chi_minh_poi_06': ('Chùa Hội Khánh|Di tích tôn giáo có giá trị kiến trúc.|Vãn cảnh và tìm hiểu kiến trúc chùa.', 'Làng tre Phú An|Điểm bảo tồn và tìm hiểu tre với bộ sưu tập, cảnh tre.|Tìm hiểu tre khi điểm mở cho khách.'),
    'tuyen_quang_poi_02': ('Na Hang|Địa bàn trong vùng cảnh quan hồ, núi và rừng Na Hang–Lâm Bình.|Chọn tuyến ngắm hồ được phục vụ tại địa bàn.', 'Lâm Bình|Địa bàn trong vùng hồ, núi và văn hóa cộng đồng Na Hang–Lâm Bình.|Tìm hiểu cộng đồng và chọn tuyến tham quan được phục vụ tại địa bàn.'),
    'tuyen_quang_poi_04': ('Mã Pí Lèng|Đèo có góc nhìn cảnh núi và hẻm vực.|Ngắm địa hình tại điểm hợp lệ; kiểm tra hạn chế từng điểm ngắm.', 'Sông Nho Quế|Dòng sông có cảnh hẻm vực nhìn từ mặt nước.|Đi thuyền khi tuyến được phục vụ.'),
    'tuyen_quang_poi_05': ('Lũng Cú|Điểm đến gắn với cột cờ và cảnh vùng núi.|Thăm cột cờ và ngắm cảnh; không coi chân cột cờ là cực bắc chính xác.', 'Đồng Văn|Vùng cao nguyên có phố cổ, bản và địa chất đặc trưng.|Khám phá phố, bản và cảnh cao nguyên đá theo tuyến.'),
}

PARENTS = {'an_giang_poi_02', 'an_giang_poi_05', 'hung_yen_poi_01',
           'lao_cai_poi_01', 'lao_cai_poi_03', 'phu_tho_poi_05', 'hai_phong_poi_01'}

# Match reviewed names to the actual original IDs, not positional assumptions.
for old, actual in {'bac_ninh_poi_04': 'bac_ninh_poi_05', 'can_tho_poi_05': 'can_tho_poi_07',
                    'gia_lai_poi_04': 'gia_lai_poi_03', 'quang_tri_poi_01': 'quang_tri_poi_02',
                    'thanh_pho_ho_chi_minh_poi_04': 'thanh_pho_ho_chi_minh_poi_05'}.items():
    REVIEWED[actual] = REVIEWED.pop(old)
REVIEWED['quang_tri_poi_04'] = (
    'Vườn quốc gia Phong Nha–Kẻ Bàng|Vùng di sản thiên nhiên với núi đá vôi, rừng và hệ thống hang.|Chọn tuyến sinh thái phù hợp và tìm hiểu cảnh quan, bảo tồn.',
    'Động Phong Nha|Hang động cụ thể trong vùng di sản Phong Nha–Kẻ Bàng.|Chọn tuyến tham quan động và thuyền theo điều kiện phục vụ.')
PARENTS.add('quang_tri_poi_04')


def migrate():
    found = set()
    for path in sorted((ROOT / 'data/raw/vietnam_travel_rag').glob('*.md')):
        text = path.read_text(encoding='utf-8')
        if 'dataset_version: "2.1"' in text:
            found.update(identifier for identifier in REVIEWED
                         if f'`legacy_group_id`: `{identifier}`' in text)
            continue
        def replace(match):
            section = match[0]
            identifier = re.search(r'`place_id`: `([^`]+)`', section)
            if not identifier or identifier[1] not in REVIEWED:
                return section
            original = identifier[1]
            assert ' – ' in section.splitlines()[0], f'Not a combined heading: {original}'
            found.add(original)
            area = re.search(r'^- Tỉnh/thành: (.+)$', section, re.M)[1]
            category = re.search(r'^- Nhóm: (.+)$', section, re.M)[1]
            sources = re.findall(r'^- \[([^\]]+)\]\((https?://[^)]+)\).+$', section, re.M)
            assert sources, original
            blocks = []
            for index, row in enumerate(REVIEWED[original]):
                name, description, experience = row.split('|')
                new_id = original if index == 0 else original + '_b'
                # Separate source lists when two articles were explicitly paired.
                selected = [sources[index]] if len(sources) == 2 else sources
                # Tràng An's two sources describe its heritage; Tam Cốc only keeps
                # the regional article, not an invented standalone reference.
                if original == 'ninh_binh_poi_01':
                    selected = sources if index == 0 else sources[:1]
                aliases = [name]
                short = re.sub(r'^(Chùa |Vườn quốc gia |Vịnh |Lăng |Đồi chè |Làng gốm |Tháp |Cầu |Sông |Hồ )', '', name)
                if short != name and len(short.split()) >= 2:
                    aliases.append(short)
                relationship = f'- `parent_place_id`: `{original}`\n' if index and original in PARENTS else ''
                note = 'Kiểm tra điều kiện tham quan và dịch vụ của đúng địa điểm trước khi đi.'
                if name == 'Fansipan': note = 'Cáp treo và trekking có yêu cầu thể lực, giá và điều kiện riêng; cảnh mây phụ thuộc thời tiết.'
                if name == 'Hội Lim': note = 'Lễ hội và biểu diễn phụ thuộc lịch tổ chức, không có cam kết diễn ra mỗi ngày.'
                if name == 'Tràng An': note = 'Chọn đúng bến và tuyến; vé và dịch vụ cần xác nhận cho ngày đi.'
                if name == 'Hang Múa': note = 'Cân nhắc thể lực khi lên bậc; đây là điểm ngắm cảnh, không phải vườn quốc gia.'
                status = re.search(r'^\*\*Tình trạng có ngày:\*\* (.+)$', section, re.M)
                dated = f'\n**Tình trạng có ngày:** {status[1]}\n' if status and index == 0 else ''
                blocks.append(f'### {name}\n- `place_id`: `{new_id}`\n- `content_type`: `attraction`\n'
                    f'- `legacy_group_id`: `{original}`\n{relationship}- Tỉnh/thành: {area}\n- Nhóm: {category}\n'
                    f'- Tên dùng tìm kiếm: {", ".join(aliases)}.\n'
                    '- `latitude`: `null`; `longitude`: `null`; `image_url`: `null`.\n\n'
                    f'**Giới thiệu — địa điểm có gì?** {description}\n\n'
                    f'**Trải nghiệm gợi ý:** {experience}\n\n**Lưu ý riêng:** {note}\n{dated}\n'
                    '**Nguồn mô tả:**\n' + '\n'.join(f'- [{title}]({url}) — tra cứu 2026-10-01.' for title, url in selected) + '\n\n')
            return ''.join(blocks)
        text = re.sub(r'^### .+\n(?:(?!^#{2,3} ).*\n?)*', replace, text, flags=re.M)
        text = text.replace('dataset_version: "2.0"', 'dataset_version: "2.1"')
        path.write_text(text, encoding='utf-8')
    assert found == set(REVIEWED), f'Unmatched migration IDs: {set(REVIEWED)-found}'
    print(json.dumps({'split_groups': len(found), 'attractions': 174 + len(found)}))


if __name__ == '__main__':
    migrate()
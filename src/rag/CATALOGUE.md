# Danh mục địa điểm từ RAG

`catalogue.json` là dữ liệu sinh tự động dùng chung cho frontend và backend.
`catalogue_overrides.json` giữ 9 bản ghi có tọa độ và nguồn từ danh mục trước.
Không sửa trực tiếp file sinh; chạy từ thư mục gốc:

```powershell
.\.venv\Scripts\python.exe scripts\build_catalogue.py
```

Sau khi sinh, khởi động lại backend; Vite tự nạp lại JSON khi chạy dev.
Không cần ingest lại Chroma nếu chỉ cập nhật danh mục bản đồ.

Hiện có 174 mục có `place_id` từ 34 file Markdown. Ghép 7 mục trùng chính xác
với danh mục cũ thành 176 bản ghi, trong đó 9 bản ghi giữ tọa độ cũ và 167 bản
ghi ban đầu chưa có tọa độ xác minh. Hiện catalogue_locations.json bổ sung 53
vị trí tham chiếu có nguồn: tổng 62 marker, còn 114 mục chưa định vị.
Tràng An–Tam Cốc, Phú Quốc–Bãi Sao và các tiêu đề
gộp khác không được coi là một điểm riêng trùng với danh mục cũ.

Mỗi bản ghi giữ rag_ids, documents, nguồn và ngày tra cứu gốc. Ngày tra cứu
không phải ngày xác nhận giá hoặc địa chỉ. Nhóm Bắc/Trung/Nam là quy ước du lịch
trong catalogue_builder.REGIONS, không phải ranh giới hành chính; Tây Nguyên
thuộc nhóm Trung. Không nhập các dòng quán/khách sạn chưa có place_id vì có
dòng gộp nhiều cơ sở hoặc không đủ thông tin xác định danh tính.

Không suy ra tọa độ từ tên tỉnh. Mục coordinates=null được dùng để trả lời
chat, không dựng marker, không zoom và không nối tuyến qua điểm thiếu tọa độ.
Các thẻ khám phá ban đầu chỉ hiển thị điểm có tọa độ. GET /places trả toàn bộ
danh mục. Tên trùng như Mỹ Khê yêu cầu làm rõ tỉnh trước khi đổi bản đồ.

catalogue_locations.json giữ [kinh độ, vĩ độ], nguồn, độ chính xác nếu có,
ngày lấy dữ liệu và lưu ý điểm tham chiếu. Nguồn là tọa độ trang Wikipedia
tiếng Việt hoặc thuộc tính P625 của Wikidata, không phải đo đạc hiện trường.
data/geography giữ phản hồi API và các ứng viên để kiểm tra lại. Các kết quả
trỏ đến xã/phường/huyện, trang định hướng, nhiều tọa độ mâu thuẫn hoặc tiêu đề
gộp chưa được chấp nhận. Không dùng điểm tham chiếu làm lối vào/bến đón.
scripts/fetch_coordinate_candidates.py chỉ tải ứng viên, không tự ghi marker.

Để thêm vị trí, bổ sung bản ghi override có ID bằng place_id gốc, tọa độ
[kinh độ, vĩ độ], nguồn kiểm chứng riêng cho chính địa điểm, không dùng nguồn
chỉ xác nhận sự tồn tại của địa điểm làm bằng chứng tọa độ. Giữ source,
coordinate_source và mô tả rõ tọa độ đại diện nếu là vùng. Ảnh, thời lượng
không có trong tài liệu thì không tự điền. Kiểm tra kết quả và chạy tests
trước khi đưa override vào sử dụng.
# Phạm vi truy xuất và khoảng trống dữ liệu

Pipeline nhận diện điểm đến từ các section có `place_id`, danh mục alias và metadata tỉnh.
Từng điểm được truy xuất riêng bằng bộ lọc Chroma; ngữ cảnh không mở rộng sang tỉnh khác.
Tên tỉnh/alias lịch sử là phạm vi tìm kiếm, không tạo thêm đề xuất điểm tham quan.

Mặc định danh sách tên là giới thiệu. Lưu trú, hoạt động, giá và lịch trình có ngữ cảnh riêng.
Lịch sử người dùng chỉ được dùng để xác định ý định/địa điểm tiếp nối; câu trả lời cũ không
được đưa vào ngữ cảnh nguồn. Khi câu hỏi “ở đó” có nhiều điểm ứng viên, cần hỏi lại.

SearchResult giữ metadata nguồn, tỉnh, điểm đến, section, URL, ngày tra cứu và trạng thái giá.
Các nguồn ngắn được trả bằng trích xuất dữ kiện để model không tự thêm chi tiết. Đây là
fallback theo dữ liệu truy xuất, không phải câu trả lời mẫu gán riêng cho Hạ Long/Tràng An.
Trường hợp nguồn dài vẫn dùng Ollama; lọc ngữ cảnh và prompt không bảo đảm loại bỏ mọi
hallucination của model. Cần đánh giá lại khi bổ sung tài liệu và với các model khác.

## Dữ liệu cần bổ sung

`quang_ninh.md`: Vịnh Hạ Long chỉ có một câu về tham quan vịnh và đảo đá.
`ninh_binh.md`: Tràng An và Tam Cốc được gộp, chỉ có một câu về núi/sông/thuyền.
Chưa đủ chứng cứ để viết 150–220 từ với 2–3 trải nghiệm riêng mỗi điểm. Cần bổ sung
section mô tả có nguồn và tách rõ hai điểm; không thêm dữ kiện/giá do model đoán.

Các section lưu trú chỉ liệt kê tên cơ sở: không suy ra chất lượng, tiện nghi hoặc khoảng cách.
Nhà Của Mây thuộc mục An Giang, khu núi Cấm theo nguồn trong tài liệu. Nguồn Tripday là
nguồn thứ cấp; hoạt động và giá hiện hành chưa được xác nhận.

## Kiểm chứng

Từ thư mục `D:\Linh tinh\Chatbot`:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\verify_grounding.py
```

Script live dùng index hiện có và tạo `grounding-live.json`. Không cần rebuild index để
áp dụng bộ lọc mới; khi ingest lại, metadata `price_status` được lưu ngay trong từng chunk.
Khởi động lại backend để nhận code mới. Frontend và cấu trúc tọa độ không thay đổi.
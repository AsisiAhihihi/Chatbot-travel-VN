# Dọc miền xanh — bản demo du lịch Việt Nam

React + TypeScript + MapLibre, kết nối pipeline Python qua FastAPI.

## Chạy trên Windows

```powershell
Set-Location 'D:\Linh tinh\Chatbot\frontend'
npm install
Copy-Item .env.example .env
npm run dev
```

Mở địa chỉ Vite in trong terminal (mặc định cổng 5173). Cần mạng để tải bản đồ, font và ảnh Wikimedia. Không cần Ollama để chạy demo.

```powershell
npm run build
npx playwright install chromium
npm test
```

Khi triển khai, cấu hình web server trả index.html cho /mien-bac, /mien-trung và /mien-nam. Lịch sử được giữ khi chuyển trang trong ứng dụng, không lưu qua lần tải lại trình duyệt.

## Dữ liệu và thiết kế

- src/data.ts đọc danh mục chung src/rag/catalogue.json (từ thư mục gốc), gồm 9 địa điểm, mỗi miền 3 điểm; tọa độ theo thứ tự [kinh độ, vĩ độ]. Mỗi điểm giữ liên kết nguồn địa lý và nguồn ảnh/giấy phép Wikimedia Commons.
- Bắc, Trung, Nam là nhóm khám phá du lịch, không phải ranh giới hành chính. Tây Nguyên được quy ước thuộc nhóm Trung. Một số tọa độ đại diện vùng cảnh quan hoặc đảo, không phải cổng vào; mô tả ghi rõ điều này.
- Sáu loại marker được định nghĩa trong src/types.ts. Dữ liệu demo chưa có cơ sở lưu trú.
- Không có ảnh tham chiếu được cung cấp lúc triển khai. Để bổ sung, đặt ảnh vào thư mục public và đặt VITE_OVERVIEW_IMAGE thành đường dẫn công khai của ảnh. Ảnh tổng quan dùng object-fit: contain, không gắn tọa độ hay marker giả lên ảnh.
- Giữ attribution của bản đồ. Ảnh tải lỗi có nội dung thay thế. Không phải mọi ảnh từ dịch vụ bên ngoài đều được kiểm thử tự động.

## Kết nối RAG Python

Để trống VITE_API_BASE_URL để dùng câu trả lời mẫu. Khi có HTTP backend, đặt biến này thành URL gốc và khởi động lại Vite. src/api.ts gửi POST /chat với JSON:

```json
{"question":"Hội An có gì?","history":[{"role":"user","text":"Chào bạn"}]}
```

Hợp đồng trả lời trong src/types.ts:

- answer: văn bản tiếng Việt.
- sources: mảng {title, url} tài liệu nguồn.
- places: mảng Place có id, name, region (bac/trung/nam), category, coordinates, description, source, aliases; duration và image {url, source} tùy chọn.
- map_action: keep (không di chuyển), focus (một điểm), fit (nhiều điểm).
- itinerary: mảng ID theo thứ tự ghé thăm.
- route: null hoặc {kind: illustrative/actual, coordinates: [[kinh độ, vĩ độ]], distance_m?, duration_s?}.

Backend cần đối chiếu tên với danh mục đã xác minh và trả ID ổn định; không dùng tọa độ do mô hình đoán. Nếu mơ hồ, trả câu hỏi làm rõ với map_action=keep. Nếu không có tọa độ tin cậy, dùng coordinates=null và giải thích trong answer. Luôn trả đủ các mảng, kể cả khi rỗng.

HTTP adapter nằm ở src/rag/api.py. Khởi động backend từ thư mục gốc:

```powershell
Set-Location 'D:\Linh tinh\Chatbot'
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
# Chỉ ingest khi chưa có index hoặc khi thay tài liệu; thao tác thay collection.
# .\.venv\Scripts\python.exe scripts\ingest.py
.\.venv\Scripts\python.exe scripts\serve.py
```

Trong frontend/.env.local đặt `VITE_API_BASE_URL=http://127.0.0.1:8000`, rồi khởi động lại Vite. Để dùng demo, bỏ biến này ở mọi file .env hoặc đặt rỗng trong .env.local. Backend cần Ollama chạy và model theo .env (mặc định llama3.2). Lần đầu embedding có thể phải tải model. GET /health chỉ xác nhận HTTP server, không bảo đảm index/Ollama sẵn sàng; POST /chat trả 503 khi RAG lỗi, không tự đổi sang demo.

FRONTEND_ORIGINS trong .env backend cho phép localhost/127.0.0.1:5173; sửa khi dùng cổng hoặc host khác. Cổng backend được đặt qua API_PORT. Khóa bí mật chỉ đặt ở backend; mọi biến VITE_* đều công khai. Frontend hủy/bỏ qua phản hồi lỗi thời, nhưng công việc suy luận đang chạy trên backend có thể vẫn tiếp tục. Backend hiện dành cho local, chưa có xác thực hay giới hạn tốc độ; không public trực tiếp.

Map chỉ nhận tọa độ từ danh mục chung, không lấy từ mô hình. Danh mục sinh từ 34 file RAG hiện có 176 bản ghi: 62 có vị trí (9 cũ + 53 tham chiếu có nguồn), 114 chưa có tọa độ phù hợp. Những nơi chưa có tọa độ vẫn được trả lời nhưng không thêm marker. Chạy scripts/build_catalogue.py từ thư mục gốc để cập nhật; hướng dẫn nguồn và override ở src/rag/CATALOGUE.md. Điểm tham chiếu của hồ/rừng/núi không phải lối vào đã xác nhận. Lịch trình dùng thứ tự các điểm được đối chiếu, chưa tối ưu tuyến; không vẽ tuyến khi thiếu tọa độ. Hội thoại gửi tối đa 20 tin nhắn, mô hình dùng 10 tin gần nhất.

## Bản đồ và định tuyến

- VITE_MAP_STYLE_URL: URL style MapLibre; mặc định dùng OpenFreeMap. Nếu đổi nhà cung cấp, kiểm tra giấy phép, attribution và giới hạn sử dụng.
- VITE_OVERVIEW_IMAGE: ảnh tổng quan tùy chọn, không phải lớp bản đồ địa lý.
- Dịch vụ định tuyến chưa kết nối. Backend cần gọi nhà cung cấp định tuyến, chọn phương tiện và trả geometry, distance_m, duration_s thực tế với kind=actual. Tuyệt đối không gắn nhãn actual cho đường nối thẳng.
- Demo chỉ nối các điểm và hiển thị “Tuyến minh họa · Không phải đường đi thực tế”.

## Phạm vi kiểm thử

## Chia bundle và tải danh mục

TravelMap tải qua React.lazy/Suspense, giữ nền bạc hà và kích thước vùng bản đồ
trong lúc tải. Vite tách maplibre và react-vendor để cache riêng. MapLibre vẫn
có thể vượt ngưỡng cảnh báo 500 kB; không tăng chunkSizeWarningLimit để che cảnh
báo. Vì bản đồ xuất hiện ngay trên trang đầu, thư viện vẫn cần tải sớm; chưa
đo được mức cải thiện thời gian tải thực tế trên thiết bị người dùng.

Danh mục frontend nằm ở public/data/places.json, không còn nhúng metadata
RAG vào JavaScript. predev/prebuild tự xuất JSON từ danh mục backend;
scripts/build_catalogue.py cũng cập nhật file này. JSON chỉ giữ các trường
UI cần dùng và nguồn tọa độ. Khi sửa danh mục trong lúc Vite đang chạy, chạy
`node scripts/export-catalogue.mjs` rồi tải lại trang. Lỗi tải JSON có nút thử
lại riêng, không xóa lịch sử chat hoặc kết quả API đã nhận.

Playwright chạy cùng các luồng ở kích thước desktop và mobile: bốn trang, câu hỏi Hội An, nhiều điểm, lịch trình, reset, chọn tên trong chat, địa danh mơ hồ và không có dữ liệu. Kiểm tra không tràn ngang và chụp ảnh giao diện. Các bài này không chứng minh độ chính xác địa lý, không kiểm thử dịch vụ RAG/định tuyến thật và không xác nhận toàn bộ tile/ảnh bên ngoài đã tải. Build có cảnh báo bundle lớn do thư viện bản đồ; cần tối ưu trước triển khai quy mô lớn.
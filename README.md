# Mây — Chatbot du lịch Việt Nam

**Đồ án môn học: trợ lý du lịch kết hợp RAG và bản đồ tương tác.**

Mây giúp tìm hiểu địa điểm, khám phá tỉnh và vùng miền, tham khảo dịch vụ và gợi ý lịch trình từ dữ liệu du lịch có nguồn. Địa điểm được liên kết với bản đồ để xem vị trí, ảnh và danh sách tham quan.

### [🌿 Trải nghiệm website demo](https://asisiahihihi.github.io/Chatbot-travel-VN/)

> Frontend chạy trên GitHub Pages. Chatbot thật chạy trên máy cá nhân qua Cloudflare Tunnel: máy, backend, Ollama và tunnel phải đang hoạt động. Đây là demo đồ án, không phải dịch vụ 24/7.

## Chức năng

- **Hỏi đáp tiếng Việt:** giới thiệu địa điểm, khám phá tỉnh/miền, so sánh, ăn uống, lưu trú và giá tham khảo.
- **Truy xuất theo ý định:** hỗ trợ nhiều địa điểm, tên không dấu, alias và câu hỏi tiếp nối; hỏi làm rõ tên trùng.
- **Lịch trình sơ bộ:** chia theo ngày, gợi ý khu vực nghỉ đêm và nêu giả định để điều chỉnh.
- **Bản đồ tương tác:** chọn miền, xem popup, zoom, ghim theo nhóm và đánh số các điểm trong lịch trình.
- **Nguồn tham khảo:** câu trả lời kèm nguồn; ảnh có caption, credit và giấy phép khi có.
- **Desktop/mobile:** giao diện kết hợp chatbot, danh sách địa điểm và bản đồ.

### Câu hỏi thử

```text
Hạ Long và Tràng An có gì?
Vĩnh Long có gì?
Gợi ý chuyến đi 3 ngày 2 đêm ở miền Nam
Mỹ Khê có gì?
Giá đi thuyền Tràng An?
```

## Công nghệ

| Thành phần | Công nghệ |
| --- | --- |
| Frontend | React 19, TypeScript, Vite |
| Bản đồ | MapLibre GL, OpenFreeMap, GeoJSON |
| Backend | Python, FastAPI, Uvicorn |
| RAG | LangChain, Chroma, truy xuất kết hợp từ khóa và vector |
| Embedding | `intfloat/multilingual-e5-small` |
| Mô hình ngôn ngữ | Ollama, mặc định `llama3.2` |
| Kiểm thử | Python unittest, Playwright |
| Demo public | GitHub Pages, GitHub Actions, Cloudflare Tunnel |

```text
Người dùng → Frontend React + MapLibre (GitHub Pages)
                         ↓ HTTPS / Cloudflare Tunnel
                     FastAPI (máy cá nhân)
                         ↓
          Nhận diện ý định và phạm vi địa lý
                         ↓
          Truy xuất từ khóa + vector (Chroma)
                         ↓
          Tổng hợp bằng chứng / sinh với Ollama
                         ↓
           Câu trả lời + nguồn + địa điểm bản đồ
```

Tọa độ và ảnh lấy từ danh mục, **không lấy từ nội dung mô hình tự sinh**. Một số ý định như giới thiệu/khám phá được tổng hợp trực tiếp từ bằng chứng có cấu trúc, không phải mọi lượt đều gọi Ollama.

## Dữ liệu và giới hạn

- **34 file Markdown tỉnh/thành**, gồm **209 bản ghi địa điểm** sau khi tách các nhóm gộp.
- **209 điểm có tọa độ tham chiếu:** 206 điểm cho phép marker, 3 điểm chỉ zoom vùng.
- Bản public hiện có **185 ảnh với metadata giấy phép được chấp nhận**; 24 ảnh cần xin phép hoặc thiếu giấy phép được ẩn. Ảnh local không bị xóa.
- Tọa độ tham chiếu không mặc định là cổng vào, bến đón hay vị trí xe chạy đến được. Popup giữ tên vị trí đại diện và ghi chú.
- Tuyến bản đồ là **minh họa**, số km là khoảng cách đường thẳng nối các điểm, **không phải quãng đường đi thực tế**. Chưa có dịch vụ định tuyến giao thông.
- Lịch trình và giá chỉ tham khảo, không phải chuyến đi/báo giá đã xác nhận. Cần kiểm tra giá, lịch tàu, giờ mở cửa và điều kiện thực tế trước khi đi.

Ảnh và dữ liệu có điều kiện sử dụng riêng. Giữ credit và link giấy phép; ghi nguồn không tự thay thế quyền sử dụng. Không coi toàn bộ repo là có chung một giấy phép ảnh/dữ liệu.

## Cấu trúc dự án

```text
Chatbot-travel-VN/
├── .github/workflows/pages.yml  # Build/deploy GitHub Pages
├── data/raw/vietnam_travel_rag/ # Dữ liệu Markdown
├── frontend/
│   ├── public/                 # Danh mục, ảnh, GeoJSON
│   ├── src/                    # Giao diện, bản đồ, kết nối API
│   └── tests/                  # Kiểm thử trình duyệt
├── src/rag/                    # Pipeline RAG, API, metadata
├── scripts/                    # Ingestion và công cụ dữ liệu
├── tests/                      # Kiểm thử Python
├── start-website.cmd            # Chạy local
├── start-public-backend.cmd     # Backend demo public
├── start-public-tunnel.cmd      # Cloudflare Quick Tunnel
└── PUBLIC_WEB.md                # Hướng dẫn public
```

Model, index Chroma, dependencies và các bộ nhập liệu gốc không được commit. Clone mới cần cài dependencies và dựng index. Một số script nghiên cứu/nhập dữ liệu cần bộ nguồn riêng, không cần chạy để dùng website.

## Cài đặt và chạy local

Yêu cầu: **Python 3.10+**, **Node.js 22** (dùng trong workflow), npm, Git và Ollama. Các lệnh dưới đây dùng **Windows PowerShell**.

### 1. Clone và cài backend

```powershell
git clone https://github.com/AsisiAhihihi/Chatbot-travel-VN.git
cd Chatbot-travel-VN
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
ollama pull llama3.2
```

Đảm bảo Ollama đang chạy. Embedding được tải và cache trong lần đầu sử dụng.

### 2. Dựng index

```powershell
.\.venv\Scripts\python.exe scripts/ingest.py
```

Index lưu tại `data/processed`. Sau khi sửa Markdown cần ingest lại; thao tác thay collection hiện tại, nên sao lưu nếu cần khôi phục. Không ingest README, prompt vận hành hoặc thêm JSONL trùng dữ liệu Markdown.

### 3. Cài frontend

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local
```

Trong `frontend/.env.local`, đặt:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

**Để trống biến này sẽ dùng câu trả lời mẫu, không phải RAG thật.** Khởi động lại Vite sau khi đổi cấu hình.

### 4. Khởi động

```powershell
cd ..
.\start-website.cmd
```

- Frontend: `http://127.0.0.1:5173/`
- Backend: `http://127.0.0.1:8000`
- Kiểm tra API: `http://127.0.0.1:8000/health`

Giữ frontend, backend và Ollama hoạt động. Không chạy thêm backend trùng cổng 8000 nếu đã có phiên đang chạy.

## Cấu hình

| Biến | Công dụng / mặc định |
| --- | --- |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | `http://localhost:11434` / `llama3.2` |
| `EMBEDDING_MODEL` | `intfloat/multilingual-e5-small` |
| `RAW_DIR` / `STORE_DIR` | `data/raw` / `data/processed` |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` / `TOP_K` | `800` / `120` / `5` |
| `FRONTEND_ORIGINS` | Origin frontend được CORS cho phép |
| `CHAT_MAX_CONCURRENT` | Số lượt chat đồng thời: `1` |
| `CHAT_REQUESTS_PER_MINUTE` | Hạn mức chung: `10` lượt/phút |
| `PUBLIC_DEPLOY` | `true` để API ẩn ảnh quyền chưa rõ |
| `VITE_API_BASE_URL` | Địa chỉ API; trống là demo |
| `VITE_BASE_PATH` | Pages dùng `/Chatbot-travel-VN/` |
| `VITE_PUBLIC_DEPLOY` | `true` để frontend áp dụng chính sách ảnh public |

Các biến `VITE_*` được đưa vào bản build, không phải nơi lưu secret. Không commit `.env`, token, mật khẩu hoặc private key.

## Public demo

1. Chạy `start-public-backend.cmd` và `start-public-tunnel.cmd` từ thư mục gốc; đảm bảo Ollama hoạt động.
2. Lấy URL HTTPS của Quick Tunnel, đặt vào repository variable **`VITE_API_BASE_URL`** trên GitHub.
3. Chạy workflow **Deploy travel frontend**, hoặc push thay đổi lên nhánh `main`.
4. Kiểm tra website bằng thiết bị dùng mạng khác.

**Quick Tunnel đổi URL khi khởi động lại**, cần cập nhật variable và deploy lại. GitHub Pages chỉ chạy frontend, không chạy FastAPI/Chroma/Ollama. Chỉ tunnel API, không mở trực tiếp Ollama ra Internet.

Xem chi tiết tại [PUBLIC_WEB.md](PUBLIC_WEB.md).

## Kiểm thử và build

Backend, chạy từ thư mục gốc:

```powershell
$env:PYTHONPATH = "$PWD\src"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Frontend:

```powershell
cd frontend
npx playwright install chromium
npm run build
npm test
```

Kiểm thử RAG trực tiếp cần backend, index và Ollama sẵn sàng; bật `$env:RAG_LIVE='1'` trước khi chạy test. Kiểm thử Pages dùng `playwright.public.config.ts`, cần bản public đã build và được phục vụ ở cổng 4173.

## Khi trình bày đồ án

- Bật backend và tunnel trước buổi demo, kiểm tra chat thật từ trang public.
- Không nhầm phản hồi mẫu với RAG thật.
- Chuẩn bị video hoặc phiên local dự phòng nếu mạng/tunnel gặp lỗi.
- Công cụ hỗ trợ tìm hiểu du lịch, không thay thế xác nhận của đơn vị cung cấp dịch vụ.
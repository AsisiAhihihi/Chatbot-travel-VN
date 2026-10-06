# Public demo: GitHub Pages + backend local

Repository: AsisiAhihihi/Chatbot-travel-VN. Frontend base: `/Chatbot-travel-VN/`.

## Một lần đầu
1. Đẩy nhánh `main` lên repo. Trong Settings → Pages → Source chọn **GitHub Actions**.
2. Cài cloudflared cho Windows (bản chính thức Cloudflare). Có thể đặt binary ở `tools/cloudflared.exe`, hoặc cài vào PATH.
3. Đảm bảo Ollama chạy, model hiện có sẵn, và index `data/processed` vẫn nằm trên máy. Không upload model/index lên GitHub.

## Mỗi buổi demo
1. Chạy `start-public-backend.cmd` và giữ cửa sổ mở.
2. Chạy `start-public-tunnel.cmd`. Lấy địa chỉ HTTPS `https://...trycloudflare.com` xuất hiện trong log.
3. Repo → Settings → Secrets and variables → Actions → Variables: đặt **VITE_API_BASE_URL** bằng địa chỉ trên (không thêm `/chat`). Đây là địa chỉ công khai, không phải secret.
4. Actions → Deploy travel frontend → Run workflow (nhánh main). Chờ build/deploy thành công.
5. Mở `https://asisiahihihi.github.io/Chatbot-travel-VN/`, kiểm tra trên mạng di động: chat, ảnh, chuyển miền và tải lại trang.

Quick Tunnel đổi URL mỗi lần khởi động; phải cập nhật variable và deploy lại. Không có SLA, phù hợp demo; khi máy tắt chat không hoạt động. Nếu variable trống frontend hiện demo, không phải RAG thật. CORS chỉ chứa origin `https://asisiahihihi.github.io` (không chứa đường dẫn repo). Ollama không được expose qua tunnel.

## Ảnh và đường dẫn
Bản public bỏ ảnh chưa có giấy phép rõ ràng, cả trong catalogue, artifact và phản hồi API. Bản local không bị xóa ảnh. Các ảnh CC cần tiếp tục giữ attribution/giấy phép trong popup. Repo chỉ chứa ảnh đã có metadata giấy phép; không commit cả các thư mục ảnh nhập liệu.
Điều hướng GitHub Pages dùng hash (`#/mien-nam`) để tải lại không 404. Đường dẫn dữ liệu và ảnh theo Vite BASE_URL.

## Giới hạn demo
API giới hạn mặc định 1 yêu cầu chat đồng thời, tổng 10 lượt/phút cho mọi người. Đây không phải chống DDoS hoặc xác thực. Chạy một process Uvicorn. Không public máy cá nhân lâu dài không giám sát.

## Kiểm tra local bản public
PowerShell tại `frontend`: `$env:VITE_BASE_PATH='/Chatbot-travel-VN/'; $env:VITE_PUBLIC_DEPLOY='true'; npm run build; node scripts/prepare-public.mjs`.
Không đưa `.env`, `tools`, `.venv`, `node_modules`, index, bản sao lưu hoặc file ảnh quyền chưa rõ lên GitHub. Chỉ phục vụ `frontend/dist`, không phục vụ root dự án.
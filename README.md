# Club-Python

Backend Python cho bài toán theo dõi fan club Uma Musume:

- `FastAPI` cho REST API
- `SQL Server` cho dữ liệu
- `manual fallback` khi web ngoài lỗi
- `uma.moe provider` để sync tự động
- `scheduler 24h`

## 1. Cài dependency

```powershell
cd C:\Users\pc\Downloads\Club\Club-Python
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Cấu hình

```powershell
Copy-Item .env.example .env
```

Sửa `.env` cho đúng SQL Server instance của bạn.

## 3. Chạy API

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger:

- `http://127.0.0.1:8000/docs`

## 4. Chạy sync thủ công bằng lệnh

```powershell
python scripts\run_sync.py
python scripts\run_sync.py --member-id 1
```

## 5. Endpoint chính

- `GET /health`
- `GET /api/members`
- `GET /api/members/{member_id}`
- `GET /api/members/{member_id}/history`
- `POST /api/members/import-from-web`
- `POST /api/manual-updates`
- `POST /api/manual-updates/bulk`
- `GET /api/manual-updates`
- `POST /api/sync/run`
- `POST /api/sync/run/{member_id}`
- `GET /api/sync/runs`
- `GET /api/sync/runs/{sync_run_id}`
- `GET /api/reports/current`
- `GET /api/reports/leaderboard?period=monthly`

## Ghi chú

- Provider `uma.moe` hiện parse từ bản text-rendered của trang club để giảm phụ thuộc vào SPA bundle.
- Đây là hướng thực dụng, nhưng vẫn phụ thuộc cấu trúc hiển thị của web ngoài.
- Khi sync web lỗi, admin vẫn dùng `manual-updates` để nhập tay.

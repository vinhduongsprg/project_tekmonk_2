# Farmer Support App

Ứng dụng desktop hỗ trợ nông dân Việt Nam với các chức năng:
- Thời tiết (có cache và chế độ offline)
- Tin tức nông nghiệp (RSS, có cache)
- Bản đồ chọn tỉnh/thành
- Lịch & ghi chú
- Giá nông sản tham khảo (offline)
- Trợ lý AI (offline TF-IDF + online AI)

## Cách chạy ứng dụng
Cách 1: Chạy file run_farmer_app.vbs
Cách 2: Chạy file python farmer_app/app.py

## Dữ liệu
- Cấu hình: `farmer_app/data/config.json`
- Lịch: `farmer_app/data/calendar.json`
- Ghi chú: `farmer_app/data/notes.json`
- Giá: `farmer_app/data/prices.json`
- Tin tức cache: `farmer_app/data/news_cache.json`
- Thời tiết cache: `farmer_app/data/weather_cache.json`
- AI data: `farmer_app/data/ai_data/`

## Cấu hình API
- Thời tiết dùng WeatherAPI:
  - Vào **Cài Đặt → Thời tiết** và nhập `WeatherAPI key`.
- Trợ lý AI (Online AI):
  - Vào **Cài Đặt → Trợ giúp AI** và nhập:
    - API key
    - Base URL
    - Model
  - Hoặc chọn preset (OpenAI / Gemini / DeepSeek nếu có).

**Lưu ý:** Không nên để API key thật trong `config.json` khi nộp bài.

# Farmer Support App

A desktop application designed to support Vietnamese farmers, featuring:
- Weather (with caching and offline mode)
- Agricultural news (via RSS, with caching)
- Map-based province/city selection
- Calendar & notes
- Reference prices for agricultural products (offline)
- AI Assistant (offline TF-IDF + online AI)

## How to run the application
Option 1: Run the `run_farmer_app.vbs` file.
Option 2: Run the command `python farmer_app/app.py`.

## Data
- Configuration: `farmer_app/data/config.json`
- Calendar: `farmer_app/data/calendar.json`
- Notes: `farmer_app/data/notes.json`
- Prices: `farmer_app/data/prices.json`
- News cache: `farmer_app/data/news_cache.json`
- Weather cache: `farmer_app/data/weather_cache.json`
- AI data: `farmer_app/data/ai_data/`

## API Configuration
- Weather (powered by WeatherAPI):
 - Go to **Settings → Weather** and enter your `WeatherAPI key`.
- AI Assistant (Online AI):
 - Go to **Settings → AI Assistant** and enter:
  - API key
  - Base URL
  - Model
 - Alternatively, select a preset (e.g., OpenAI, Gemini, or DeepSeek, if available).
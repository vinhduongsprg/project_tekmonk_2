# Farmer Support Desktop App — Project Plan

## 1. Project Goal

Build a Python desktop application to support farmers in Vietnam by providing:
- Weather information
- Localized agricultural news
- Reference crop prices
- Alerts and notes
- A safe, domain‑restricted AI assistant
- A calendar system for reminders, notes, and task scheduling

The app is designed to be reliable, offline‑friendly, and competition‑safe.

---

## 2. Platform & UI

### UI Framework
PySide6 (Qt for Python)

Reasons:
- Professional desktop UI
- Built‑in calendar widget
- Strong support for multi‑page applications
- Suitable for long‑term maintenance

---

## 3. Application Pages & Features

### 3.1 Home Dashboard
- Weather summary (location‑based)
- Today’s calendar entries (top 5)
- Quick jump to Calendar

### 3.2 Location Selection
- Province selector + interactive map
- Hover/selection effects
- Searchable dropdown
- Saved to `config.json`

### 3.3 Weather
- Current conditions
- Cached for offline use
- Translation via `utils/translation_utils.py`

### 3.4 News
- Multiple RSS sources
- Titles + summaries
- Cached for offline use

### 3.5 Prices
- Local JSON/CSV data
- Manual updates (no API dependency)

### 3.6 Calendar
- Tasks, reminders, alarms, note references
- Repeat rules
- Search
- Notifications

### 3.7 Notes
- Free‑text notes
- Optional date linking to calendar
- Search

### 3.8 AI Assistant
Type:
- Domain‑focused guide (offline)
- Optional online AI (OpenAI‑compatible / Gemini)

Offline retrieval:
- General knowledge: `data/ai_data/general_knowledge/`
- CSV knowledge: `data/ai_data/*.csv`
- TF‑IDF + cosine similarity

Online AI:
- Configurable Base URL + Model
- Presets stored in `data/ai_models.json`

Chat history:
- Saved to `data/chat_history.json`

---

## 4. Data & Update Strategy

| Data Type | Source | Internet | Update Frequency |
|---------|--------|----------|-----------------|
| Weather | WeatherAPI | Yes | Every 30 minutes (configurable) |
| News | RSS feeds | Yes | Every 6-12 hours (cached) |
| Prices | Local JSON | No | Monthly (manual) |
| Calendar | Local JSON | No | Real‑time (user actions) |
| Notes | Local JSON | No | Real‑time (user actions) |
| Settings | Local JSON | No | Real‑time (user actions) |
| AI Knowledge | Local text/CSV | No | Static + manual updates |

---

## 5. Localization
- UI language: Vietnamese
- Weather condition translation at controller layer
- Translation dictionaries in `data/translations/`

---

## 6. Connectivity & Offline Strategy
- Connectivity check every 5 minutes
- Offline indicators shown in UI
- Cached weather/news used when offline

---

## 7. Python Packages
External:
- pyside6
- requests
- feedparser
- scikit‑learn
- svg.path

Built‑in:
- json
- csv
- datetime
- os
- re

---

## 8. File Structure (simplified)
farmer_app/
├── app.py
├── config/
│   └── settings.py
├── ui/
│   ├── main_window.py
│   └── pages/
│       ├── home_page.py
│       ├── location_page.py
│       ├── news_page.py
│       ├── prices_page.py
│       ├── calendar_page.py
│       ├── notes_page.py
│       └── assistant_page.py
├── controllers/
│   ├── weather_controller.py
│   ├── location_controller.py
│   ├── news_controller.py
│   ├── prices_controller.py
│   ├── calendar_controller.py
│   ├── notes_controller.py
│   └── assistant_controller.py
├── services/
│   ├── weather_service.py
│   ├── location_service.py
│   ├── news_service.py
│   ├── prices_service.py
│   ├── calendar_service.py
│   ├── notes_service.py
│   ├── assistant_service.py
│   └── connectivity_service.py
├── data/
│   ├── prices.json
│   ├── calendar.json
│   ├── notes.json
│   ├── weather_cache.json
│   ├── news_cache.json
│   ├── config.json
│   ├── chat_history.json
│   ├── ai_models.json
│   ├── translations/
│   │   ├── weather.json
│   │   └── alerts.json
│   └── ai_data/
│       ├── general_knowledge/
│       │   ├── weather.txt
│       │   ├── crops.txt
│       │   ├── prices.txt
│       │   └── safety_rules.txt
│       └── *.csv
└── docs/
    ├── README.md
    ├── farmer_app_plan.md
    └── data_schema.md

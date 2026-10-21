# Data Schema Documentation

This document describes the structure of all local data used in the Farmer App.

All persistent data is stored in human-readable JSON files to ensure transparency, simplicity, and offline usability.

## 2. Crop Prices (`prices.json`)

### Schema (current app)

```json
{
  "last_updated": "31/12/2025 11:17",
  "items": [
    {
      "name": "L?a IR 50404 (t??i)",
      "category": "L?a g?o",
      "price": "5.300-5.400",
      "unit": "VN?/kg",
      "region": "Nam",
      "updated_at": "27/12/2025",
      "source": "vietnam.vn"
    }
  ]
}
```

## 3. Calendar Data (`calendar.json`)

```json
[
  {
    "id": "entry_20260128_095337",
    "date": "28/01/2026",
    "title": "Bón phân lót",
    "time": "06:30",
    "type": "Task",
    "repeat": "weekly",
    "note": "Bón NPK đợt 1",
    "created_at": "28/01/2026 09:53:37",
    "updated_at": "28/01/2026 09:53:37"
  },
  {
    "id": "entry_20260128_101200",
    "date": "28/01/2026",
    "title": "Tưới nước cho ruộng lúa",
    "time": "17:00",
    "type": "Reminder",
    "repeat": "daily",
    "note": "",
    "created_at": "28/01/2026 10:12:00",
    "updated_at": "28/01/2026 10:12:00"
  },
  {
    "id": "entry_20260129_053000",
    "date": "29/01/2026",
    "title": "Báo động sương muối",
    "time": "05:30",
    "type": "Alarm",
    "repeat": "none",
    "note": "Chuẩn bị che phủ cây",
    "created_at": "28/01/2026 11:20:00",
    "updated_at": "28/01/2026 11:20:00"
  },
  {
    "id": "note_note_20260128_095400",
    "note_id": "note_20260128_095400",
    "date": "28/01/2026",
    "title": "Ghi chú về lúa",
    "time": "",
    "type": "Note",
    "repeat": "none",
    "note": "Lúa xanh, không sâu bệnh.",
    "created_at": "28/01/2026 09:54:00",
    "updated_at": "28/01/2026 09:54:00"
  }
]
```

## 4. Notes Data (`notes.json`)

```json
{
  "notes": [
    {
      "id": "note_20260128_095400",
      "title": "Quan sát lúa",
      "content": "Lúa xanh, không sâu bệnh.",
      "linked_date": "28/01/2026",
      "created_at": "28/01/2026 09:54:00",
      "updated_at": "28/01/2026 09:54:00"
    }
  ],
  "last_updated": "2026-01-28T09:54:00"
}
```

## 5. Weather Cache (`weather_cache.json`)

```json
{
  "cached_at": "2026-01-31T05:11:05.954025+00:00",
  "location": {
    "name": "Province De Hà Tĩnh",
    "region": "",
    "country": "Vietnam"
  },
  "current": {
    "temp_c": 24.1,
    "condition": {
      "text": "Patchy rain nearby",
      "icon": "//cdn.weatherapi.com/weather/64x64/day/176.png",
      "code": 1063
    },
    "wind_kph": 12.2,
    "precip_mm": 0.05,
    "humidity": 64,
    "cloud": 79,
    "uv": 8.9
  },
  "source": "live",
  "age_minutes": 0.0,
  "stale": false
}

```

## 6. AI Data (`data/ai_data/`)

### General Knowledge
- Folder: `data/ai_data/general_knowledge/`
- Files: `weather.txt`, `crops.txt`, `prices.txt`, `safety_rules.txt`

### CSV Knowledge
- Folder: `data/ai_data/`
- CSV files are loaded into offline TF?IDF retrieval.

### Saved Chats (`chat_history.json`)

```json
[
  {
    "id": "chat_20260131_103000",
    "title": "Hỏi về khoai tây",
    "created_at": "31/01/2026 10:30",
    "messages": [
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ]
  }
]
```

### AI Presets (`ai_models.json`)

```json
[
  {
    "id": "openai_default",
    "label": "OpenAI (default)",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini",
    "temperature": 0.3
  }
]
```

## 7. Application Settings (`config.json`)

```json
{
  "location": {
    "province": "H? N?i",
    "region": "Mi?n B?c",
    "coordinates": [21.0285, 105.8542]
  },
  "weather": {
    "api_key": "your_api_key_here",
    "update_interval": 30,
    "units": "metric"
  },
  "news": {
    "update_interval": 6,
    "sources": ["https://example.com/rss"]
  },
  "connectivity": {
    "check_interval": 5
  },
  "ai": {
    "api_key": "your_api_key_here",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini",
    "temperature": 0.3,
    "system_prompt": "B?n l? tr? l? n?ng nghi?p...",
    "preset": "custom"
  },
  "ui": {
    "language": "vi",
    "theme": "light",
    "window_size": [1000, 700],
    "window_position": [100, 100]
  }
}
```

## 8. ID Convention

<type>_<YYYYMMDD>_<HHMMSS>

Examples:
`entry_20260128_095337`
`note_20260128_095400`

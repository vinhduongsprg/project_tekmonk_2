"""
Assistant Service
Provides API-based responses with offline fallback using TF-IDF + cosine similarity.
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
import math
import re
import requests

from config import get_setting


class AssistantService:
    """Service for AI assistant interactions."""

    def __init__(self):
        self.session = requests.Session()
        self._knowledge_entries = None
        self._tfidf_cache = None

    def _build_endpoint(self, base_url: str) -> str:
        url = base_url.rstrip("/")
        if url.endswith("/v1"):
            return f"{url}/chat/completions"
        if url.endswith("/v1/"):
            return f"{url}chat/completions"
        if "/v1" not in url:
            return f"{url}/v1/chat/completions"
        return f"{url}/chat/completions"

    def _build_messages(self, history: List[Dict], user_text: str) -> List[Dict]:
        system_prompt = get_setting(
            "ai.system_prompt",
            "Bạn là trợ lý nông nghiệp. Trả lời ngắn gọn, rõ ràng, ưu tiên an toàn.",
        )
        messages = [{"role": "system", "content": system_prompt}]
        for item in history[-10:]:
            role = item.get("role")
            content = item.get("content")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_text})
        return messages

    def send_message(
        self,
        text: str,
        history: List[Dict],
        prefer_offline: bool = False,
        show_sources: bool = True,
    ) -> Tuple[Optional[str], Optional[str]]:
        if prefer_offline:
            return self._offline_response(text, show_sources=show_sources)

        api_key = get_setting("ai.api_key")
        if not api_key:
            return None, "missing_api_key"

        base_url = get_setting("ai.base_url", "https://api.openai.com/v1")
        model = get_setting("ai.model", "gpt-4o-mini")
        temperature = float(get_setting("ai.temperature", 0.3))

        if self._is_gemini(base_url, model):
            return self._send_gemini(text, history, api_key, base_url, model, temperature)

        endpoint = self._build_endpoint(base_url)
        payload = {
            "model": model,
            "messages": self._build_messages(history, text),
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = self.session.post(endpoint, json=payload, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                return None, "empty_response"
            message = choices[0].get("message", {})
            content = message.get("content")
            if not content:
                return None, "empty_response"
            return content.strip(), None
        except requests.RequestException:
            return None, "request_failed"

    def _is_gemini(self, base_url: str, model: str) -> bool:
        base = (base_url or "").lower()
        name = (model or "").lower()
        return "generativelanguage.googleapis.com" in base or name.startswith("gemini")

    def _send_gemini(
        self,
        text: str,
        history: List[Dict],
        api_key: str,
        base_url: str,
        model: str,
        temperature: float,
    ) -> Tuple[Optional[str], Optional[str]]:
        url = base_url.rstrip("/")
        endpoint = f"{url}/v1beta/models/{model}:generateContent"
        params = {"key": api_key}

        system_prompt = get_setting(
            "ai.system_prompt",
            "Bạn là trợ lý nông nghiệp. Trả lời ngắn gọn, rõ ràng, ưu tiên an toàn.",
        )

        contents = []
        for item in history[-10:]:
            role = item.get("role")
            content = item.get("content")
            if not content:
                continue
            if role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
        contents.append({"role": "user", "parts": [{"text": text}]})

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }

        try:
            response = self.session.post(endpoint, params=params, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return None, "empty_response"
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                return None, "empty_response"
            text_out = parts[0].get("text")
            if not text_out:
                return None, "empty_response"
            return text_out.strip(), None
        except requests.RequestException:
            return None, "request_failed"

    def _offline_response(self, text: str, show_sources: bool = True) -> Tuple[Optional[str], Optional[str]]:
        entries = self._load_knowledge_entries()
        if not entries:
            return None, "no_knowledge"
        scores = self._rank_by_similarity(text, entries)
        if not scores:
            return self._out_of_scope_message(), None

        top_score, top_entry = scores[0]
        if top_score < 0.08:
            return self._out_of_scope_message(), None

        snippets = []
        for score, entry in scores[:3]:
            snippet = self._snippet(entry.get("content", ""))
            title = entry.get("title", "Thông tin")
            source = entry.get("source", "")
            if source.endswith(".csv"):
                line = f"- {snippet}"
            else:
                line = f"- {title}: {snippet}"
            if source and show_sources:
                line += f" ({source})"
            snippets.append(line)
        response = "Thông tin tham khảo (ngoại tuyến):\n" + "\n".join(snippets)
        return response, None

    def _load_knowledge_entries(self) -> List[Dict]:
        if self._knowledge_entries is not None:
            return self._knowledge_entries
        data_dir = Path(__file__).parent.parent / "data" / "ai_data"
        general_dir = data_dir / "general_knowledge"
        entries: List[Dict] = []

        if general_dir.exists():
            for path in sorted(general_dir.glob("*.txt")):
                text = path.read_text(encoding="utf-8", errors="ignore")
                items = self._split_topics(text)
                for idx, item in enumerate(items, start=1):
                    entries.append(
                        {
                            "id": f"{path.stem}_{idx}",
                            "title": item["title"],
                            "content": item["content"],
                            "source": path.name,
                        }
                    )

        entries.extend(self._load_csv_knowledge(data_dir))

        if not entries:
            self._knowledge_entries = []
            return self._knowledge_entries

        self._knowledge_entries = entries
        return self._knowledge_entries

    def _load_csv_knowledge(self, data_dir: Path) -> List[Dict]:
        import csv

        if not data_dir.exists():
            return []

        entries: List[Dict] = []
        csv_files = sorted(data_dir.glob("*.csv"))
        seen = set()
        for path in csv_files:
            try:
                with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as f:
                    reader = csv.DictReader(f)
                    for idx, row in enumerate(reader):
                        text = self._build_csv_text(row)
                        if not text:
                            continue
                        if len(text) < 30:
                            continue
                        normalized = text.lower().strip()
                        if normalized in seen:
                            continue
                        seen.add(normalized)
                        entries.append(
                            {
                                "id": f"{path.stem}_{idx + 1}",
                                "title": path.stem.replace("_", " ").title(),
                                "content": text,
                                "source": path.name,
                            }
                        )
            except Exception:
                continue
        return entries

    def _build_csv_text(self, row: Dict) -> str:
        def _clean(value) -> str:
            if value is None:
                return ""
            value = str(value).strip()
            if not value or value.lower() == "nan":
                return ""
            return value

        # Prefer concise QA-style rows.
        answer = _clean(row.get("answer"))
        question = _clean(row.get("question"))
        if answer:
            if question:
                return f"Hỏi: {question}\nĐáp: {answer}"
            return answer

        # Crop profiles (keep essential fields).
        crop_name = _clean(row.get("crop_name"))
        if crop_name:
            parts = [f"{crop_name}"]
            ideal_temp = _clean(row.get("ideal_temp_C"))
            soil = _clean(row.get("soil_type"))
            ph_min = _clean(row.get("pH_min"))
            ph_max = _clean(row.get("pH_max"))
            season = _clean(row.get("planting_seasons"))
            if ideal_temp:
                parts.append(f"Nhiệt độ: {ideal_temp}°C")
            if soil:
                parts.append(f"Đất: {soil}")
            if ph_min or ph_max:
                parts.append(f"pH: {ph_min}-{ph_max}".strip("-"))
            if season:
                parts.append(f"Thời vụ: {season}")
            return "; ".join([p for p in parts if p])

        # Fallback: include a small subset of informative fields.
        preferred_keys = [
            "name",
            "pest_name",
            "symptoms",
            "dosage_range_kg_per_ha",
            "region",
            "recommendation",
            "notes",
        ]
        parts = []
        for key in preferred_keys:
            val = _clean(row.get(key))
            if val:
                label = key.replace("_", " ")
                parts.append(f"{label}: {val}")
        if parts:
            return " | ".join(parts)

        # Final fallback: first 6 non-empty fields.
        parts = []
        for key, value in row.items():
            val = _clean(value)
            if val:
                parts.append(f"{key}: {val}")
            if len(parts) >= 6:
                break
        return " | ".join(parts)

    def _split_topics(self, text: str) -> List[Dict]:
        items: List[Dict] = []
        current_title = None
        current_lines: List[str] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line.lower().startswith("[topic]"):
                if current_title:
                    items.append(
                        {"title": current_title, "content": "\n".join(current_lines).strip()}
                    )
                current_title = line[len("[topic]") :].strip() or "Chủ đề"
                current_lines = []
            else:
                if line:
                    current_lines.append(line)
        if current_title:
            items.append({"title": current_title, "content": "\n".join(current_lines).strip()})
        if not items and text.strip():
            items.append({"title": "Thông tin", "content": text.strip()})
        return items

    def _rank_by_similarity(self, query: str, entries: List[Dict]):
        tfidf = self._build_tfidf(entries)
        vocab = tfidf["vocab"]
        idf = tfidf["idf"]
        vectors = tfidf["vectors"]
        norms = tfidf["norms"]

        q_vec = self._tfidf_vector(query, vocab, idf)
        q_norm = self._vector_norm(q_vec)
        if q_norm == 0:
            return []

        scores = []
        for idx, entry in enumerate(entries):
            dot = self._dot_product(q_vec, vectors[idx])
            denom = q_norm * norms[idx]
            score = dot / denom if denom else 0.0
            scores.append((score, entry))
        scores.sort(key=lambda x: x[0], reverse=True)
        return scores

    def _build_tfidf(self, entries: List[Dict]):
        if self._tfidf_cache is not None:
            return self._tfidf_cache

        docs = [f"{e.get('title', '')}\n{e.get('content', '')}" for e in entries]
        tokens_list = [self._tokenize(doc) for doc in docs]
        vocab = {}
        df = {}
        for tokens in tokens_list:
            seen = set()
            for token in tokens:
                if token not in vocab:
                    vocab[token] = len(vocab)
                if token not in seen:
                    df[token] = df.get(token, 0) + 1
                    seen.add(token)
        total_docs = len(docs) or 1
        idf = {
            token: math.log((1 + total_docs) / (1 + df_count)) + 1
            for token, df_count in df.items()
        }
        vectors = []
        norms = []
        for tokens in tokens_list:
            vec = self._tfidf_vector_from_tokens(tokens, vocab, idf)
            vectors.append(vec)
            norms.append(self._vector_norm(vec))

        self._tfidf_cache = {"vocab": vocab, "idf": idf, "vectors": vectors, "norms": norms}
        return self._tfidf_cache

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return [t for t in cleaned.split() if len(t) > 1]

    def _tfidf_vector(self, text: str, vocab: Dict, idf: Dict) -> Dict[int, float]:
        tokens = self._tokenize(text)
        return self._tfidf_vector_from_tokens(tokens, vocab, idf)

    def _tfidf_vector_from_tokens(self, tokens: List[str], vocab: Dict, idf: Dict) -> Dict[int, float]:
        tf = {}
        for token in tokens:
            if token in vocab:
                tf[token] = tf.get(token, 0) + 1
        if not tf:
            return {}
        max_tf = max(tf.values())
        vec = {}
        for token, count in tf.items():
            idx = vocab[token]
            tf_norm = count / max_tf
            vec[idx] = tf_norm * idf.get(token, 1.0)
        return vec

    def _vector_norm(self, vec: Dict[int, float]) -> float:
        return math.sqrt(sum(v * v for v in vec.values()))

    def _dot_product(self, a: Dict[int, float], b: Dict[int, float]) -> float:
        if len(a) > len(b):
            a, b = b, a
        return sum(val * b.get(idx, 0.0) for idx, val in a.items())

    def _snippet(self, text: str, max_len: int = 220) -> str:
        if not text:
            return ""
        snippet = text.replace("\n", " ").strip()
        if len(snippet) <= max_len:
            return snippet
        return snippet[: max_len - 3].rstrip() + "..."

    def _out_of_scope_message(self) -> str:
        return (
            "Xin lỗi, tôi chưa có thông tin phù hợp trong dữ liệu nội bộ. "
            "Bạn nên tham khảo khuyến cáo của cơ quan nông nghiệp địa phương."
        )

"""
rag_pipeline.py
Mẫu pipeline RAG (Retrieval-Augmented Generation) bằng Python.
Ghi chú: mã mẫu này chứa phần tạo embeddings bằng sentence-transformers và FAISS local.
- Các bước chính:
  1) Đọc CSV dữ liệu (kịch bản: crops, pests, fertilizer, buyers ...)
  2) Tạo embeddings cho từng đoạn văn (mỗi bản ghi 1 document)
  3) Lưu index FAISS + metadata
  4) Hàm truy vấn: nhận câu hỏi, lấy top-k documents, kết hợp prompt system + passages, gọi LLM để trả lời.
Chú ý: bạn cần cài python packages: sentence-transformers, faiss-cpu, transformers hoặc OpenAI SDK (nếu dùng GPT)
Tất cả comment đều bằng tiếng Việt.

"""

import os
import pandas as pd

# THƯ VIỆN embeddings & faiss
# pip install sentence-transformers faiss-cpu
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json

# Hàm load dữ liệu CSV (các file nằm cùng thư mục data)
def load_csvs(data_dir="data"):
    files = ["crops_expanded_by_province.csv","pests_expanded_by_province.csv","fertilizer_expanded.csv","buyers_expanded.csv","qa_training_vietnamese.csv"]
    docs = []
    for f in files:
        fp = os.path.join(data_dir, f)
        if os.path.exists(fp):
            df = pd.read_csv(fp, encoding="utf-8-sig")
            for i, row in df.iterrows():
                # Chọn trường tạo văn bản: ghép một số cột quan trọng
                text_parts = []
                for col in ["crop_name","crop_id","pest_name","symptoms","dosage_range_kg_per_ha","name","question","answer"]:
                    if col in row and pd.notna(row[col]):
                        text_parts.append(str(row[col]))
                text = " | ".join(text_parts)
                docs.append({"id": f"{f}__{i}", "text": text, "meta": row.to_dict()})
    return docs

# Tạo embeddings và index FAISS
def build_faiss_index(docs, model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", dim=384):
    # model_name có thể đổi, mặc định là model đa ngôn ngữ nhẹ
    model = SentenceTransformer(model_name)
    texts = [d["text"] for d in docs]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    # Chuẩn hóa embeddings (tùy chọn)
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])  # inner product after normalize = cosine similarity
    index.add(embeddings)
    return index, embeddings, model

# Lưu index và metadata
def save_index(index, docs, index_path="faiss.index", meta_path="meta.json"):
    faiss.write_index(index, index_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

# Tải index & meta
def load_index(index_path="faiss.index", meta_path="meta.json"):
    index = faiss.read_index(index_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        docs = json.load(f)
    return index, docs

# Truy vấn: lấy top-k documents cho câu hỏi
def retrieve(query, index, docs, model, top_k=5):
    q_emb = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(q_emb)
    D, I = index.search(q_emb, top_k)
    results = []
    for score, idx in zip(D[0], I[0]):
        results.append({"score": float(score), "doc": docs[idx]})
    return results

# Ví dụ kết hợp với LLM: tạo prompt (ở đây chỉ là ví dụ; gọi LLM bên ngoài)
def build_generation_prompt(system_prompt, query, retrieved_docs):
    passages = "\n\n".join([f"- {d['doc']['text']}" for d in retrieved_docs])
    prompt = f"""{system_prompt}

Thông tin tham khảo (dẫn nguồn): 
{passages}

Hỏi: {query}

Trả lời ngắn gọn, rõ ràng, bằng tiếng Việt, nếu không chắc, đưa nguồn tham khảo và gợi ý gửi ảnh/ mẫu đất.
"""
    return prompt

# Hàm main mẫu để chạy toàn bộ pipeline (cần chỉnh đường dẫn)
def main(data_dir="/mnt/data", save_dir="/mnt/data/rag_index"):
    os.makedirs(save_dir, exist_ok=True)
    docs = load_csvs(data_dir)
    print(f"Đọc {len(docs)} văn bản để index.")
    index, embeddings, model = build_faiss_index(docs)
    save_index(index, docs, os.path.join(save_dir, "faiss.index"), os.path.join(save_dir, "meta.json"))
    print("Đã xây dựng và lưu FAISS index vào", save_dir)
    # Ví dụ truy vấn
    q = "Lúa bị rầy nâu phải xử lý thế nào?"
    res = retrieve(q, index, docs, model, top_k=5)
    for r in res:
        print("Score:", r["score"], "Doc excerpt:", r["doc"]["text"][:200])

if __name__ == "__main__":
    main()

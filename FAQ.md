# FAQ: Enterprise Chunking, Splitting & Ingestion Pipeline (Vector Embeddings)

This document answers common questions about **chunking**, **splitting**, **PDF/DOCX/PPT ingestion**, **table/image handling**, and **enterprise-grade RAG pipelines**, presented in a clear **Q&A / FAQ format**.  
Animation and visual steps are included as **ASCII animations / flow diagrams** for easy viewing in Markdown.

---

## 📌 **FAQ Table of Contents**

1. What is chunking and why is it required?
2. What are the different types of chunking?
3. How are tables chunked inside PDFs?
4. How are images chunked inside PDFs?
5. How are DOCX files chunked?
6. How are PPT/PPTX files chunked?
7. How are tables handled differently from text?
8. How does OCR work in the pipeline?
9. How is multimodal embedding done?
10. What does an end-to-end ingestion pipeline look like?
11. How does permission-aware chunking work?
12. What metadata is added to each chunk?
13. What chunk sizes are recommended?
14. What happens during retrieval?
15. Can this be scaled to millions of documents?

---

# 🧩 **1. What is chunking and why is it required?**

Chunking means **splitting a large document into smaller, meaning-preserving pieces** before embedding into a vector database.

### Why?

- Embedding models have limited token capacity
- Smaller chunks improve retrieval accuracy
- It reduces hallucinations in RAG
- Allows fine-grained permissions at chunk level
- Helps scale enterprise search efficiently

---

# 🧱 **2. What are the different types of chunking?**

### ✔ **Fixed-size chunking**

Splits by fixed tokens (e.g., 500 tokens).

### ✔ **Recursive chunking**

Split by:  
**paragraph → sentence → tokens** (fallback).

### ✔ **Sliding window overlapping**

Chunk A overlaps with chunk B by ~10–20% of tokens.

### ✔ **Semantic chunking**

Split where semantic similarity drops.

### ✔ **Section-based chunking**

Use H1/H2/H3 headings or slide sections.

### ✔ **Table-aware chunking**

Serialize tables separately.

### ✔ **Image-aware chunking**

Extract OCR text + image embedding.

---

# 📊 **3. How are tables chunked inside PDFs?**

Tables are detected using:

- AWS Textract (recommended)
- PDFPlumber
- LlamaParse
- LayoutParser

### Chunks are created as:

- Table-row groups
- Serialized table blocks
- With preserved structure (rows, columns, headers)

### Example:

```
Row1: Year | Revenue | Cost
Row2: 2023 | $10M    | $4M
Row3: 2024 | $14M    | $5M
```

Tables are _never merged with paragraphs_.

---

# 🖼 **4. How are images chunked inside PDFs?**

Images are processed using:

- OCR (Textract or pytesseract)
- Image embeddings (CLIP/Bedrock Titan)

### Image Chunk =

- OCR text
- Bounding boxes
- Image embedding
- Source metadata

---

# 📄 **5. How are DOCX files chunked?**

DOCX provides clean structure:

- Heading detection (H1, H2, H3)
- Paragraph grouping under sections
- Table extraction
- Image OCR + caption binding

All structural blocks become separate chunks.

---

# 📽 **6. How are PPT/PPTX files chunked?**

PowerPoint slides are object-based, so chunking happens per-slide:

```
Slide 1
 ├── Title text
 ├── Bullets
 ├── Image + OCR
 └── Diagram + caption
```

One slide = one chunk  
(or multiple if > 800 tokens)

---

# 📐 **7. How are tables handled differently from text?**

Text → smooth sentence-based chunking  
Tables → structured, row-group chunking

Tables keep:

- Column associations
- Headers
- Cell meanings

This avoids misleading retrieval.

---

# 🔍 **8. How does OCR work in the pipeline?**

OCR is used when:

- PDF is scanned
- Images contain text
- PPT images include diagrams

OCR output becomes searchable text.

---

# 🧬 **9. How is multimodal embedding done?**

Two vectors are produced:

- Text embedding (OCR text)
- Image embedding (CLIP/Titan)

The system can:

- Concatenate them
- Store separately
- Use weighted fusion

---

# 🏗 **10. What does an end-to-end ingestion pipeline look like?**

### **ASCII Animation: Ingestion Flow**

```
[ Upload ] → [ Storage ] → [ Preprocess ] → [ Chunk ] → [ Embed ] → [ Pinecone ]
      |            |                |             |          |             |
      v            v                v             v          v             v
   User       S3 Bucket       Layout Parser   Hybrid Split  Vector     RAG Layer
                                                   ↓
                                           Table | Text | Image
```

### **Sequence (Animation Style)**

```
Step 1 → User uploads file
Step 2 → S3 triggers event
Step 3 → Preprocessor extracts:
            - text
            - images
            - tables
Step 4 → Chunker creates:
            - paragraph-chunks
            - table-chunks
            - image-chunks
Step 5 → Embedder creates vectors
Step 6 → Pinecone stores (vector + metadata)
Step 7 → RAG retrieves chunks intelligently
```

---

# 🔐 **11. How does permission-aware chunking work?**

Each chunk stores permissions:

```
permissions: ["team:finance", "role:manager"]
```

At query time, RAG filters out unauthorized chunks.

---

# 🏷 **12. What metadata is added to each chunk?**

Example metadata:

```
{
  "chunk_id": "uuid",
  "document_id": "doc-123",
  "type": "table|paragraph|image",
  "page": 4,
  "section": "1.2 Overview",
  "permissions": ["finance"],
  "source": "PDF"
}
```

---

# 📏 **13. What chunk sizes are recommended?**

- 300–800 tokens → ideal
- 50–150 tokens → overlap
- Table chunks: ~200–800 tokens serialized
- Slide chunks: one per slide unless very long

---

# 🔎 **14. What happens during retrieval?**

1. Query → embed
2. Vector search retrieves top-k chunks
3. Reranking (optional)
4. Pass chunks into RAG LLM
5. LLM composes final answer

---

# 🚀 **15. Can this scale to millions of documents?**

Yes — if your pipeline includes:

- Async queue (SQS/Kafka)
- Horizontal workers
- Pinecone pod autoscaling
- Metadata-based filtering
- Chunk-level permission enforcement

This design supports **enterprise-grade search**.

---

# 🎬 **ASCII Animation: Chunking Visualization**

```
PDF Page:
+----------------------+
| Paragraph 1          |
| Paragraph 2          |
| [Image Diagram]      |
| [Table]              |
+----------------------+

         |
         v

Chunker:
[Para1]  [Para2]  [Image-OCR]  [Table-Block]

         |
         v

Embedder:
Vec(P1)  Vec(P2)  Vec(IMG)  Vec(TABLE)

         |
         v

Pinecone Storage:
[Vector + Metadata]
```

---

# 📦 **Downloadable README**

This file is saved as **README_FAQ.md** and can be downloaded directly.

---

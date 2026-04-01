# 📦 Scripts Module

This folder contains operational CLI scripts for managing and running
the Carbon Registry RAG System.

These scripts are designed for:

- Milvus collection management
- Single project ingestion
- Batch ingestion
- Project reprocessing
- Retrieval testing
- Operational debugging

All scripts are CLI-based and production-ready.

---

# 🏗 System Context

The scripts interact with the following layers:

- ingestion/ → PDF processing
- embeddings/ → E5 embedding generation
- vectordb/ → Milvus vector storage
- pipelines/ → Orchestration logic

Embedding Model:

- `intfloat/multilingual-e5-large`
- Dimension: 1024
- Metric: COSINE
- Index: HNSW

---

# 📜 Available Scripts

---

## 1️⃣ rebuild_index.py

Rebuilds the Milvus collection from scratch.

This will:

- Drop existing collection
- Recreate schema
- Recreate HNSW index
- Load collection

⚠️ **WARNING**  
This deletes all existing vectors.

### Usage

```bash
python scripts/rebuild_index.py
```

---

## 2️⃣ ingest_project.py

Ingests a single project PDF into Milvus.

### Pipeline:

```bash
PDF → Sentence Split → Chunk → E5 Embed → Insert into Milvus
```

### Required Parameters

- pid : Project ID
- file : PDF filename (must exist in data/pdfs)

### Usage

```bash
python scripts/ingest_project.py \
    --pid 1493 \
    --file project_1493.pdf
```

---

## 3️⃣ batch_ingest_folder.py

Batch ingests all PDF files inside a given folder.

Expected filename format:

```bash
 <project_document>.pdf
```

### Required Parameters

- path : Folder containing PDFs

### Optional Parameters

- batch_size : Embedding batch size (default=32)

Usage

```bash
python scripts/batch_ingest_folder.py \
    --path data/pdfs \
    --batch_size 32 \
    --reset False
```

### What It Does

For each PDF:

- Extracts PID from filename
- Runs ingestion pipeline
- Generates embeddings
- Inserts into Milvus
- Continues on failure (safe batch execution)

---

## 4️⃣ reprocess_project.py

Deletes all vectors associated with a given PID
and re-ingests the project.

Useful when:

- You updated ingestion logic
- You improved cleaning
- You changed embedding model
- You fixed chunking issues

### Required Parameters

- pid
- file

Usage

```bash
python scripts/reprocess_project.py \
    --pid 1493 \
    --file project_1493.pdf
```

---

## 5️⃣ run_retrieval.py

Runs semantic search directly from CLI.

Supports optional PID filtering.

### Required Parameters

--query

### Optional Parameters

--pid : Restrict search to specific project
--top_k : Number of results (default=5)

Usage

```bash
python scripts/run_retrieval.py \
    --query "local employment benefits" \
    --pid 1493 \
    --top_k 5
```

### Output

Returns:

- Similarity score
- PID
- Page number
- Content preview

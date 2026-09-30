# 🎓 University PDF RAG Chatbot

A simple **Retrieval-Augmented Generation (RAG)** chatbot that answers questions based on a university PDF document. Built with Python, Hugging Face, and Qdrant Cloud.

---

## 📖 What is RAG?

**RAG = Retrieval-Augmented Generation**

Instead of relying only on a language model's training data, RAG first **retrieves** relevant information from your own documents and then **generates** an answer based on that retrieved context. This means the chatbot answers **only** from your PDF — no hallucinations.

---

## 🏗️ How This Project Works

```
                 UNIVERSITY PDF
                       |
                       v
                  PyMuPDF (text extraction)
                       |
                       v
                  Text Chunks (500 chars, 100 overlap)
                       |
                       v
          Hugging Face Embedding API (BAAI/bge-small-en-v1.5)
                       |
                       v
                 Vector Embeddings
                       |
                       v
                 QDRANT CLOUD (stored)
                       |
                       |
User Question ---------+
       |
       v
Hugging Face Embedding API
       |
       v
Query Vector
       |
       v
Qdrant Similarity Search
       |
       v
Top 5 Relevant Chunks
       |
       v
Context + User Question
       |
       v
Hugging Face Qwen LLM (Qwen2.5-3B-Instruct)
       |
       v
Final Answer
       |
       v
Gradio UI
```

---

## 📁 Project Structure

```
rag-pdf-chatbot/
│
├── documents/
│   └── university_rules.pdf    ← Your PDF goes here
│
├── ingest.py                   ← PDF → chunks → embeddings → Qdrant Cloud
├── rag.py                      ← Question → search → LLM → answer
├── app.py                      ← Gradio web chatbot UI
├── requirements.txt            ← Python dependencies
├── .env.example                ← Template for environment variables
├── .env                        ← Your actual secrets (not committed to git)
├── .gitignore                  ← Files to exclude from git
└── README.md                   ← This file
```

---

## 🚀 Setup Guide (Windows)

### Step 1: Create a Virtual Environment

Open **Command Prompt** or **PowerShell** in the project folder:

```bash
cd rag-pdf-chatbot
python -m venv venv
```

### Step 2: Activate the Virtual Environment

```bash
venv\Scripts\activate
```

You should see `(venv)` at the start of your command line.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Get a Hugging Face Token

1. Go to [https://huggingface.co/](https://huggingface.co/)
2. Sign up / Log in
3. Go to **Settings → Access Tokens**
4. Click **"New token"**
5. Give it a name, select **"Read"** permission
6. Click **"Generate"**
7. Copy the token (starts with `hf_...`)

### Step 5: Create a Qdrant Cloud Cluster

1. Go to [https://cloud.qdrant.io/](https://cloud.qdrant.io/)
2. Sign up (free tier available)
3. Click **"Create Cluster"**
4. Choose **Free** tier
5. Pick any region
6. After creation, you'll see:
   - **Cluster URL** (like `https://abc123-xyz.aws.cloud.qdrant.io:6333`)
   - **API Key** (click "Get API Key")
7. Copy both values

### Step 6: Configure .env

1. Copy the example file:

```bash
copy .env.example .env
```

2. Open `.env` in a text editor and fill in your values:

```
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxx
QDRANT_URL=https://your-cluster-url:6333
QDRANT_API_KEY=your_qdrant_api_key_here
```

> ⚠️ **Never share your `.env` file or commit it to git!**

### Step 7: Place Your PDF

Put your university PDF file in the `documents/` folder and name it:

```
documents/university_rules.pdf
```

---

## ▶️ Running the Project

### 1. Ingest the PDF (run once, or when you change the PDF)

```bash
python ingest.py
```

**Expected output:**
```
============================================================
   RAG PDF Chatbot — Ingestion Pipeline
============================================================
✅ Environment variables loaded successfully.
📄 Opening PDF: documents\university_rules.pdf
   ✅ Extracted text from X page(s).
   ✅ Created Y text chunk(s)
🔢 Generating embeddings using: BAAI/bge-small-en-v1.5
   ... embedded Y/Y chunks
☁️  Connecting to Qdrant Cloud ...
   ✅ Collection 'university_docs' created
   ✅ All vectors stored in Qdrant Cloud successfully!
🔍 Running test search: "What are the rules for students?"
📋 Top 3 results:
   ...
============================================================
   ✅ Ingestion complete! You can now run: python rag.py
============================================================
```

### 2. Test in Terminal (optional)

```bash
python rag.py
```

Type questions and press Enter. Type `quit` to exit.

**Expected output:**
```
============================================================
   University PDF RAG Chatbot — Terminal Mode
============================================================
Type your question and press Enter.

❓ You: What is the attendance requirement?

⏳ Searching and generating answer ...

🤖 Answer:
According to the document (Page X), the attendance requirement is ...

📚 Sources used:
   • Page X  (university_rules.pdf) — relevance: 0.85
```

### 3. Launch the Web UI

```bash
python app.py
```

**Expected output:**
```
🚀 Starting University PDF RAG Chatbot ...
   Open the URL below in your browser.

Running on local URL:  http://0.0.0.0:7860
```

Open **http://127.0.0.1:7860** in your browser.

---

## ❗ Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `HF_TOKEN is missing` | Make sure your `.env` file has a valid `HF_TOKEN` |
| `QDRANT_URL is missing` | Add your Qdrant Cloud URL to `.env` |
| `PDF file not found` | Place your PDF at `documents/university_rules.pdf` |
| `Connection refused (Qdrant)` | Check your `QDRANT_URL` and `QDRANT_API_KEY` |
| `Model not found` | Make sure you have a valid HF token with read access |
| `No extractable text` | Your PDF might be a scanned image; use a text-based PDF |
| `pip install fails` | Make sure your venv is activated and Python ≥ 3.9 |

---

## 🧰 Technologies Used

| Technology | Purpose |
|-----------|---------|
| **Python** | Main language |
| **PyMuPDF** | PDF text extraction |
| **Hugging Face Hub** | Embedding API + LLM API |
| **BAAI/bge-small-en-v1.5** | Embedding model (hosted) |
| **Qwen/Qwen2.5-72B-Instruct** | LLM for answer generation (hosted) |
| **Qdrant Cloud** | Vector database for similarity search |
| **Gradio** | Web chatbot interface |
| **python-dotenv** | Environment variable management |

---

## 📄 License

This project is for educational purposes.

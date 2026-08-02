<p align="center">
  <img src="E:\Trellis\apps\banner.png" alt="Trellis" width="100%" />
</p>

<p align="center">
  <strong>Compliance answers you can trace, not guess.</strong>
</p>

<p align="center">
  Trellis turns messy, multi-format enterprise compliance documents into a connected knowledge graph — so your team gets accurate, cited answers instead of hallucinated ones.
</p>

<br />

## The Problem

Standard AI search tools chunk documents in isolation and lose the relationships between pieces of information. In compliance — where a single wrong answer means regulatory risk — that's unacceptable.

## How Trellis Works

Trellis ingests PDFs, audio recordings, CSV tables, and network schematics, then builds an actual knowledge graph. When you ask a question, it doesn't just retrieve text — it traverses entity relationships across every source and grounds every claim with a traceable citation.

```
Documents → Extraction → Knowledge Graph → Query → Cited Answer
   PDF          ↓            Entities          ↓        ↓
   Audio     Gemini AI      Relationships    Graph    [source: Page 4]
   CSV          ↓            Embeddings     Traversal  [source: 02:15]
   Diagrams  Structured       pgvector       2-hop     Verified ✓
```

<br />

## Tech Stack

| Layer        | Technology                                                     |
| ------------ | -------------------------------------------------------------- |
| **Frontend** | Next.js 16, React 19, Tailwind CSS, Zustand, React Force Graph |
| **Backend**  | FastAPI, LangGraph, LangChain                                  |
| **Database** | Supabase PostgreSQL + pgvector                                 |
| **LLMs**     | Google Gemini, Groq                                            |
| **Auth**     | Supabase Auth                                                  |

<br />

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Supabase project

### 1. Database

Run `apps/backend/schema.sql` in the Supabase SQL Editor.

### 2. Backend

```bash
cd apps/backend
python -m venv venv && .\venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

```bash
uvicorn main:app --reload
```

### 3. Frontend

```bash
cd apps/frontend
npm install
npm run dev
```

Open `http://localhost:3000`

<br />

## Project Structure

```
apps/
├── backend/
│   ├── main.py                 # FastAPI server & endpoints
│   ├── query_pipeline.py       # GraphRAG query engine
│   ├── pdf_extractor.py        # PDF entity extraction
│   ├── audio_extractor.py      # Audio transcription & extraction
│   ├── table_extractor.py      # CSV/XLSX extraction
│   ├── dedup_entities.py       # Cross-format entity deduplication
│   ├── schema.sql              # Database DDL + pgvector RPCs
│   └── ingest.py               # CLI ingestion utility
│
├── frontend/
│   ├── app/                    # Next.js app router pages
│   ├── components/             # React components
│   ├── hooks/                  # Custom React hooks
│   ├── store/                  # Zustand state management
│   └── types/                  # TypeScript type definitions
```

<br />

## License

MIT

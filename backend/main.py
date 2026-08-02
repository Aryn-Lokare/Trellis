import os
import uuid
import logging
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

from query_pipeline import build_query_graph
from extractor import get_supabase_client

logger = logging.getLogger("compliance-graphrag-api")

app = FastAPI(
    title="compliance-grag-backend",
    description="Backend for the Multi-Modal Knowledge Graph Synthesis for Enterprise Compliance",
    version="0.1.0",
)

# Set up CORS middleware to allow communication with frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


# Instantiate the compiled LangGraph query pipeline
query_graph = build_query_graph()

# ---------------------------------------------------------------------------
#  Status mapping helpers
# ---------------------------------------------------------------------------

STATUS_MAP = {
    "pending": "extracting",
    "processing": "extracting",
    "processed": "completed",
    "completed": "completed",
    "failed": "failed",
}


def _map_status(db_status: str) -> str:
    return STATUS_MAP.get(db_status, db_status)


def _infer_doc_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in [".mp3", ".wav", ".m4a", ".ogg", ".aac", ".flac"]:
        return "audio"
    if ext in [".csv", ".xlsx", ".xls", ".tsv"]:
        return "table"
    return "pdf"


# ---------------------------------------------------------------------------
#  Background ingestion worker
# ---------------------------------------------------------------------------


def _process_ingestion_background(
    doc_id: str, local_filepath: str, doc_type: str, filename: str
):
    """Runs the full ingestion pipeline in the background after /upload returns."""
    from pdf_extractor import extract_entities_from_pdf
    from audio_extractor import extract_entities_from_audio
    from table_extractor import normalize_table, extract_entities_from_table
    from dedup_entities import deduplicate_entities
    from backfill_entity_embeddings import backfill_embeddings

    supabase = get_supabase_client()
    try:
        if doc_type == "pdf":
            import pypdf

            reader = pypdf.PdfReader(local_filepath)
            pages_data = []
            full_text_parts = []
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                pages_data.append({"page_num": idx + 1, "text": page_text})
                full_text_parts.append(page_text)
            full_text = "\f".join(full_text_parts)

            supabase.table("documents").update(
                {
                    "raw_text": full_text,
                    "extraction_metadata": {"pages": pages_data},
                }
            ).eq("id", doc_id).execute()

            extract_entities_from_pdf(doc_id)

        elif doc_type == "audio":
            import google.generativeai as genai

            api_key = os.environ.get("GEMINI_API_KEY")
            genai.configure(api_key=api_key)
            audio_file = genai.upload_file(path=local_filepath)
            model = genai.GenerativeModel("gemini-2.0-flash")
            prompt = (
                "Transcribe this audio file completely. For every significant topic, speaker change, or 30-second interval, "
                "output a timestamp in brackets like '[00:15]' or '[01:30]' followed by the transcribed text. "
                "Maintain chronological order."
            )
            res = model.generate_content([audio_file, prompt])
            transcript_text = res.text
            try:
                audio_file.delete()
            except Exception:
                pass

            supabase.table("documents").update(
                {
                    "raw_text": transcript_text,
                    "extraction_metadata": {"transcript_engine": "gemini-2.0-flash"},
                }
            ).eq("id", doc_id).execute()

            extract_entities_from_audio(doc_id)

        elif doc_type == "table":
            from ingest import upload_to_supabase_storage

            remote_path = f"tables/{filename}"
            storage_path = upload_to_supabase_storage(
                supabase, local_filepath, remote_path
            )

            supabase.table("documents").update(
                {
                    "storage_path": storage_path,
                }
            ).eq("id", doc_id).execute()

            normalize_table(doc_id)
            extract_entities_from_table(doc_id)

        # Mark complete
        supabase.table("documents").update({"status": "processed"}).eq(
            "id", doc_id
        ).execute()
        deduplicate_entities()
        backfill_embeddings()
        logger.info(f"Ingestion complete for doc {doc_id}")

    except Exception as e:
        logger.error(f"Ingestion failed for doc {doc_id}: {e}", exc_info=True)
        supabase.table("documents").update(
            {
                "status": "failed",
                "error_message": str(e),
            }
        ).eq("id", doc_id).execute()

    finally:
        if os.path.exists(local_filepath):
            try:
                os.remove(local_filepath)
            except Exception:
                pass


# ---------------------------------------------------------------------------
#  Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health_check():
    """Verify backend is running and healthy."""
    return {
        "status": "healthy",
        "service": "compliance-graphrag-backend",
        "database": "unverified",
    }


@app.post("/upload")
async def upload_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    type: Optional[str] = Form(None),
):
    """Accept a file upload, persist a pending document row, and queue ingestion."""
    supabase = get_supabase_client()
    filename = file.filename or f"upload-{uuid.uuid4()}"
    doc_type = type if type in ("pdf", "audio", "table") else _infer_doc_type(filename)

    # Insert pending row
    res = (
        supabase.table("documents")
        .insert(
            {
                "filename": filename,
                "doc_type": doc_type,
                "status": "pending",
            }
        )
        .execute()
    )
    doc_id = res.data[0]["id"]

    # Save to temp folder
    temp_dir = os.path.join(os.path.dirname(__file__), "temp_uploads")
    os.makedirs(temp_dir, exist_ok=True)
    local_path = os.path.join(temp_dir, f"{doc_id}_{filename}")
    content = await file.read()
    with open(local_path, "wb") as f:
        f.write(content)

    background_tasks.add_task(
        _process_ingestion_background, doc_id, local_path, doc_type, filename
    )

    return {"id": doc_id, "filename": filename, "type": doc_type, "status": "pending"}


@app.get("/documents")
def list_documents():
    """Return all ingested documents."""
    supabase = get_supabase_client()
    res = (
        supabase.table("documents")
        .select("id, filename, doc_type, created_at, status")
        .order("created_at", desc=True)
        .execute()
    )
    docs = []
    for d in res.data or []:
        docs.append(
            {
                "id": d["id"],
                "filename": d["filename"],
                "type": d.get("doc_type", "pdf"),
                "created_at": d.get("created_at", ""),
                "status": _map_status(d.get("status", "completed")),
            }
        )
    return docs


@app.get("/document/{doc_id}")
def get_document(doc_id: str):
    """Return document metadata plus its extracted entities and relationships."""
    supabase = get_supabase_client()

    doc_res = supabase.table("documents").select("*").eq("id", doc_id).execute()
    if not doc_res.data:
        return {"error": "Document not found"}
    doc = doc_res.data[0]

    ents = (
        supabase.table("entities")
        .select("id, name, type, source_doc_id, source_span, source_location")
        .eq("source_doc_id", doc_id)
        .execute()
    )
    rels = (
        supabase.table("relationships")
        .select(
            "id, source_entity_id, target_entity_id, relation_type, source_doc_id, source_span, source_location"
        )
        .eq("source_doc_id", doc_id)
        .execute()
    )

    return {
        "id": doc["id"],
        "filename": doc.get("filename"),
        "type": doc.get("doc_type", "pdf"),
        "created_at": doc.get("created_at", ""),
        "status": _map_status(doc.get("status", "completed")),
        "content_text": doc.get("raw_text", ""),
        "extracted_entities": [
            {
                "id": e["id"],
                "name": e["name"],
                "type": e["type"],
                "source_doc_id": e["source_doc_id"],
                "source_span": e.get("source_span", ""),
            }
            for e in (ents.data or [])
        ],
        "extracted_relationships": [
            {
                "id": r["id"],
                "source_entity_id": r["source_entity_id"],
                "target_entity_id": r["target_entity_id"],
                "relationship_type": r["relation_type"],
                "source_doc_id": r["source_doc_id"],
                "source_span": r.get("source_span", ""),
            }
            for r in (rels.data or [])
        ],
    }


@app.get("/document/{doc_id}/status")
def get_document_status(doc_id: str):
    """Return live ingestion status for a document (polled by the frontend progress bar)."""
    supabase = get_supabase_client()
    doc_res = (
        supabase.table("documents")
        .select("id, filename, doc_type, status, error_message")
        .eq("id", doc_id)
        .execute()
    )
    if not doc_res.data:
        return {
            "document_id": doc_id,
            "filename": "Unknown",
            "type": "pdf",
            "status": "failed",
            "progress_percent": 0,
        }
    doc = doc_res.data[0]
    mapped = _map_status(doc.get("status", "pending"))

    progress = {
        "extracting": 50,
        "completed": 100,
        "failed": 100,
        "queued": 10,
        "parsing": 30,
    }.get(mapped, 25)

    # Count extracted data
    ent_count = len(
        (
            supabase.table("entities")
            .select("id")
            .eq("source_doc_id", doc_id)
            .execute()
        ).data
        or []
    )
    rel_count = len(
        (
            supabase.table("relationships")
            .select("id")
            .eq("source_doc_id", doc_id)
            .execute()
        ).data
        or []
    )

    return {
        "document_id": doc["id"],
        "filename": doc.get("filename", "Unknown"),
        "type": doc.get("doc_type", "pdf"),
        "status": mapped,
        "progress_percent": progress,
        "error": doc.get("error_message"),
        "extracted_entities_count": ent_count,
        "extracted_relationships_count": rel_count,
    }


@app.get("/graph")
def get_graph():
    """Return the full knowledge graph for the explorer UI."""
    supabase = get_supabase_client()

    ents = (
        supabase.table("entities")
        .select("id, name, type, source_doc_id, source_span")
        .execute()
    )
    rels = (
        supabase.table("relationships")
        .select(
            "id, source_entity_id, target_entity_id, relation_type, source_doc_id, source_span"
        )
        .execute()
    )

    nodes = [
        {
            "id": e["id"],
            "name": e["name"],
            "type": e["type"],
            "source_doc_id": e.get("source_doc_id", ""),
            "source_span": e.get("source_span", ""),
        }
        for e in (ents.data or [])
    ]
    edges = [
        {
            "id": r["id"],
            "source_entity_id": r["source_entity_id"],
            "target_entity_id": r["target_entity_id"],
            "relationship_type": r["relation_type"],
            "source_doc_id": r.get("source_doc_id", ""),
            "source_span": r.get("source_span", ""),
        }
        for r in (rels.data or [])
    ]
    return {"nodes": nodes, "edges": edges}


@app.post("/query")
def query_endpoint(req: QueryRequest):
    """Execute the GraphRAG query pipeline and return answer + citations + subgraph."""
    try:
        initial_state = {
            "question": req.question,
            "question_embedding": None,
            "seed_entity_ids": [],
            "subgraph": {"entities": [], "relationships": []},
            "synthesized_context": "",
            "raw_answer": "",
            "verified_answer": "",
            "citations": [],
            "status": "pending",
            "error_message": None,
        }

        final_state = query_graph.invoke(initial_state)

        # ---- Map citations to frontend schema ----
        raw_citations = final_state.get("citations") or []
        frontend_citations = []
        for idx, cit in enumerate(raw_citations):
            fn = cit.get("filename") or ""
            doc_type = "pdf"
            if fn.endswith((".csv", ".xlsx", ".xls")):
                doc_type = "table"
            elif fn.endswith((".wav", ".mp3", ".m4a", ".ogg")):
                doc_type = "audio"
            frontend_citations.append(
                {
                    "id": f"cit-{idx}",
                    "citation_index": idx + 1,
                    "source_doc_id": cit.get("source_doc_id") or "",
                    "source_span": cit.get("location") or "",
                    "snippet": cit.get("excerpt") or "",
                    "document_filename": fn,
                    "document_type": doc_type,
                }
            )

        # ---- Map subgraph to frontend schema ----
        sg = final_state.get("subgraph") or {"entities": [], "relationships": []}
        nodes = []
        for e in sg.get("entities", []):
            nodes.append(
                {
                    "id": e.get("entity_id") or e.get("id") or "",
                    "name": e.get("entity_name") or e.get("name") or "",
                    "type": e.get("entity_type") or e.get("type") or "",
                    "source_doc_id": e.get("entity_source_doc_id")
                    or e.get("source_doc_id")
                    or "",
                    "source_span": e.get("entity_source_span")
                    or e.get("source_span")
                    or e.get("entity_source_location")
                    or "",
                }
            )
        edges = []
        for r in sg.get("relationships", []):
            edges.append(
                {
                    "id": r.get("id") or str(uuid.uuid4()),
                    "source_entity_id": r.get("source_entity_id") or "",
                    "target_entity_id": r.get("target_entity_id") or "",
                    "relationship_type": r.get("relation_type") or "",
                    "source_doc_id": r.get("source_doc_id") or "",
                    "source_span": r.get("source_span") or "",
                }
            )

        return {
            "answer": final_state.get("verified_answer")
            or final_state.get("raw_answer")
            or "",
            "citations": frontend_citations,
            "subgraph": {"nodes": nodes, "edges": edges},
            "status": final_state.get("status") or "success",
            "f1_score": final_state.get("f1_score") or 0.0,
        }
    except Exception as e:
        return {
            "answer": f"Error running query pipeline: {str(e)}",
            "citations": [],
            "subgraph": {"nodes": [], "edges": []},
            "status": "failed",
            "f1_score": 0.0,
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

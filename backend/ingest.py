"""
Compliance Knowledge Graph Ingestion Utility.

Allows users to ingest real PDFs, audio files, and tables (CSV/XLSX),
automatically runs format-specific extraction, performs entity deduplication,
and backfills embeddings.
"""

import os
import sys
import argparse
import logging
import uuid
import mimetypes
from dotenv import load_dotenv

import google.generativeai as genai
from supabase import Client

# Import modular extractors and helpers
from extractor import get_supabase_client
from pdf_extractor import extract_entities_from_pdf
from audio_extractor import extract_entities_from_audio
from table_extractor import normalize_table, extract_entities_from_table
from dedup_entities import deduplicate_entities
from backfill_entity_embeddings import backfill_embeddings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ingest-pipeline")


def upload_to_supabase_storage(supabase: Client, local_path: str, remote_path: str) -> str:
    """Uploads a local file to Supabase Storage in the 'documents' bucket."""
    bucket_name = "documents"
    logger.info(f"Uploading {local_path} to Supabase storage bucket '{bucket_name}' path '{remote_path}'...")
    
    with open(local_path, "rb") as f:
        file_bytes = f.read()

    # Determine mime-type
    mime_type, _ = mimetypes.guess_type(local_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    supabase.storage.from_(bucket_name).upload(
        path=remote_path,
        file=file_bytes,
        file_options={"content-type": mime_type, "x-upsert": "true"}
    )
    
    return f"{bucket_name}/{remote_path}"


def ingest_pdf(supabase: Client, filepath: str) -> str:
    """Parses PDF pages, writes to documents table, and runs PDF extraction."""
    import pypdf
    logger.info(f"Ingesting PDF: {filepath}")
    
    reader = pypdf.PdfReader(filepath)
    pages_data = []
    full_text_parts = []
    
    for idx, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        pages_data.append({
            "page_num": idx + 1,
            "text": page_text
        })
        full_text_parts.append(page_text)
        
    full_text = "\f".join(full_text_parts) # Use form-feed as page separator

    filename = os.path.basename(filepath)
    
    res = supabase.table("documents").insert({
        "filename": filename,
        "doc_type": "pdf",
        "raw_text": full_text,
        "extraction_metadata": {"pages": pages_data},
        "status": "pending"
    }).execute()
    
    doc_id = res.data[0]["id"]
    logger.info(f"Created document record: {doc_id}")
    
    # Run extractor
    logger.info("Executing PDF entity and relationship extraction...")
    extract_entities_from_pdf(doc_id)
    return doc_id


def ingest_audio(supabase: Client, filepath: str) -> str:
    """Uploads audio to Gemini, transcribes with timestamps, and runs audio extraction."""
    logger.info(f"Ingesting Audio: {filepath}")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY for audio transcription.")
        
    genai.configure(api_key=api_key)
    
    logger.info("Uploading audio file to Gemini File API...")
    audio_file = genai.upload_file(path=filepath)
    logger.info(f"Gemini uploaded file: {audio_file.name}")
    
    # Request transcription with timestamp markers
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = (
        "Transcribe this audio file completely. For every significant topic, speaker change, or 30-second interval, "
        "output a timestamp in brackets like '[00:15]' or '[01:30]' followed by the transcribed text. "
        "Maintain chronological order."
    )
    
    logger.info("Generating transcript via Gemini...")
    res = model.generate_content([audio_file, prompt])
    transcript_text = res.text
    logger.info("Transcription completed.")
    
    # Clean up Gemini File API storage
    try:
        audio_file.delete()
    except Exception:
        pass

    filename = os.path.basename(filepath)
    
    doc_res = supabase.table("documents").insert({
        "filename": filename,
        "doc_type": "audio",
        "raw_text": transcript_text,
        "extraction_metadata": {"transcript_engine": "gemini-2.5-flash"},
        "status": "pending"
    }).execute()
    
    doc_id = doc_res.data[0]["id"]
    logger.info(f"Created document record: {doc_id}")
    
    # Run extractor
    logger.info("Executing Audio entity and relationship extraction...")
    extract_entities_from_audio(doc_id)
    return doc_id


def ingest_table(supabase: Client, filepath: str) -> str:
    """Uploads CSV/XLSX to Supabase storage, writes document record, and runs table extraction."""
    logger.info(f"Ingesting Table: {filepath}")
    filename = os.path.basename(filepath)
    
    # Verify file is readable as tabular
    import pandas as pd
    if filepath.endswith(".csv"):
        pd.read_csv(filepath)
    else:
        pd.read_excel(filepath)
        
    remote_path = f"tables/{filename}"
    storage_path = upload_to_supabase_storage(supabase, filepath, remote_path)
    
    doc_res = supabase.table("documents").insert({
        "filename": filename,
        "doc_type": "table",
        "storage_path": storage_path,
        "status": "pending"
    }).execute()
    
    doc_id = doc_res.data[0]["id"]
    logger.info(f"Created document record: {doc_id}")
    
    # Run normalization first to parse CSV into markdown text in the DB
    logger.info("Normalizing table data...")
    normalize_table(doc_id)
    
    # Run extractor
    logger.info("Executing Table entity and relationship extraction...")
    extract_entities_from_table(doc_id)
    return doc_id


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Ingest compliance documents into GraphRAG.")
    parser.add_argument("--file", required=True, help="Path to local file to ingest")
    parser.add_argument("--type", required=True, choices=["pdf", "audio", "table"], help="Document type")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
        
    supabase = get_supabase_client()
    
    try:
        # Step 1: Ingest document and run extraction
        if args.type == "pdf":
            doc_id = ingest_pdf(supabase, args.file)
        elif args.type == "audio":
            doc_id = ingest_audio(supabase, args.file)
        elif args.type == "table":
            doc_id = ingest_table(supabase, args.file)
            
        logger.info(f"Successfully processed and extracted document {doc_id}.")
        
        # Step 2: Update status to processed
        supabase.table("documents").update({"status": "processed"}).eq("id", doc_id).execute()
        
        # Step 3: Run Cross-Format Entity Deduplication
        logger.info("Running Cross-Format Entity Deduplication (FR8)...")
        dedup_summary = deduplicate_entities()
        logger.info(f"Deduplication complete: {dedup_summary}")
        
        # Step 4: Run Entity Embeddings Backfill
        logger.info("Running Entity Embeddings Backfill...")
        backfill_embeddings()
        logger.info("Embeddings backfill complete.")
        
        print("\n" + "=" * 80)
        print("INGESTION PIPELINE RUN COMPLETE")
        print(f"  Ingested File: {args.file}")
        print(f"  Document ID:   {doc_id}")
        print(f"  Deduplicated:  {dedup_summary.get('entities_removed', 0)} duplicate entities merged")
        print("=" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

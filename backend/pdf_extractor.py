import logging
import uuid
from typing import Dict, List, Tuple, Any, Optional
from extractor import get_supabase_client, get_gemini_model, extract_chunk_entities, merge_entities

logger = logging.getLogger("compliance-graphrag-pdf-extractor")

def chunk_text_by_pages(
    raw_text: str, extraction_metadata: Optional[Dict[str, Any]]
) -> List[Tuple[str, str]]:
    """
    Chunks raw_text by page if metadata has page boundaries,
    falls back to form-feed splitting, and then to character-based splitting (~1500 tokens).
    Returns a list of tuples: (chunk_text, page_identifier_label).
    """
    chunks = []
    
    # 1. Try to extract pages from Docling-style extraction_metadata
    if extraction_metadata and isinstance(extraction_metadata, dict):
        pages = extraction_metadata.get("pages")
        if isinstance(pages, list) and len(pages) > 0:
            logger.info("Found page boundaries in extraction_metadata. Chunking by page.")
            for p in pages:
                if not isinstance(p, dict):
                    continue
                page_num = (
                    p.get("page_num")
                    or p.get("page_no")
                    or p.get("number")
                    or p.get("page")
                )
                text = p.get("text") or p.get("content") or p.get("raw_text")
                if text and text.strip():
                    label = f"Page {page_num}" if page_num else "Page Unknown"
                    chunks.append((text.strip(), label))
            if chunks:
                return chunks

    # 2. Try to split by form-feed character (\f)
    if "\f" in raw_text:
        logger.info("Found form-feed markers in raw_text. Chunking by form-feed.")
        raw_pages = raw_text.split("\f")
        for idx, page in enumerate(raw_pages):
            if page.strip():
                chunks.append((page.strip(), f"Page {idx + 1}"))
        if chunks:
            return chunks

    # 3. Fallback: Chunk by characters
    logger.info("No page boundaries or form-feed markers found. Falling back to token-equivalent character chunking.")
    chunk_size = 6000
    overlap = 500
    text_len = len(raw_text)

    start = 0
    chunk_num = 1
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk_text = raw_text[start:end].strip()
        if chunk_text:
            chunks.append((chunk_text, f"Chunk {chunk_num}"))
        start += chunk_size - overlap
        chunk_num += 1

    return chunks

def extract_entities_from_pdf(document_id: str) -> dict:
    """
    Primary orchestration function:
    1. Fetches raw_text and extraction_metadata from Supabase.
    2. Chunks text by page or fallback.
    3. Calls LLM with retry validation for each chunk.
    4. Merges entities with exact name/type matching.
    5. Resolves relationship names to unique entity database IDs.
    6. Writes extracted structures into database.
    """
    supabase = get_supabase_client()

    logger.info(f"Fetching document {document_id} from database...")
    doc_res = (
        supabase.table("documents")
        .select("id, doc_type, raw_text, extraction_metadata")
        .eq("id", document_id)
        .execute()
    )
    if not doc_res.data:
        raise ValueError(f"Document with ID {document_id} not found.")

    doc = doc_res.data[0]

    # Scope check: PDF only
    if doc.get("doc_type") != "pdf":
        logger.warning(
            f"Document {document_id} has type '{doc.get('doc_type')}', which is not 'pdf'. Skipping."
        )
        return {"status": "skipped", "reason": "Not a PDF document"}

    raw_text = doc.get("raw_text") or ""
    metadata = doc.get("extraction_metadata")

    if not raw_text.strip():
        logger.warning(
            f"Document {document_id} has empty raw_text. Nothing to extract."
        )
        return {"status": "skipped", "reason": "Empty raw_text"}

    # Chunk text
    chunks = chunk_text_by_pages(raw_text, metadata)
    logger.info(f"Total chunks to process: {len(chunks)}")

    # Initialize Gemini model
    model = get_gemini_model()

    raw_entities = []
    raw_relationships = []

    # Extract from each chunk
    for chunk_text, location in chunks:
        logger.info(f"Extracting from {location}...")
        extracted_data = extract_chunk_entities(model, chunk_text, location)

        raw_entities.extend(extracted_data.get("entities", []))
        raw_relationships.extend(extracted_data.get("relationships", []))

    logger.info(
        f"Extracted {len(raw_entities)} raw entities and {len(raw_relationships)} raw relationships."
    )

    # 1. Merge entities by (name, type)
    merged_entities_map = merge_entities(raw_entities)
    logger.info(f"Deduplicated to {len(merged_entities_map)} unique entities.")

    # Generate IDs for merged entities and prepare database payloads
    db_entities = []
    entity_id_map = {}  # Map (lower_name) -> entity_uuid

    for (name, ent_type), data in merged_entities_map.items():
        entity_uuid = str(uuid.uuid4())
        entity_id_map[name.lower()] = entity_uuid

        spans_str = ", ".join(list(data["source_spans"]))
        locs_str = ", ".join(sorted(list(data["source_locations"])))

        db_entities.append(
            {
                "id": entity_uuid,
                "name": data["name"],
                "type": data["type"],
                "source_doc_id": document_id,
                "source_span": spans_str,
                "source_location": locs_str,
                "embedding": None,
            }
        )

    # 2. Resolve relationship names to entity UUIDs
    db_relationships = []
    unresolved_count = 0

    for rel in raw_relationships:
        source_name = rel["source_entity"].strip().lower()
        target_name = rel["target_entity"].strip().lower()

        source_uuid = entity_id_map.get(source_name)
        target_uuid = entity_id_map.get(target_name)

        if not source_uuid or not target_uuid:
            logger.warning(
                f"Could not resolve relationship entity names: '{rel['source_entity']}' -> '{rel['target_entity']}'. Skipping."
            )
            unresolved_count += 1
            continue

        db_relationships.append(
            {
                "id": str(uuid.uuid4()),
                "source_entity_id": source_uuid,
                "target_entity_id": target_uuid,
                "relation_type": rel["relation_type"],
                "source_doc_id": document_id,
                "source_span": rel["source_span"],
                "source_location": rel["source_location"],
            }
        )

    # 3. Write data to Supabase
    if db_entities:
        logger.info(f"Writing {len(db_entities)} entities to database...")
        supabase.table("entities").insert(db_entities).execute()

    if db_relationships:
        logger.info(f"Writing {len(db_relationships)} relationships to database...")
        supabase.table("relationships").insert(db_relationships).execute()

    return {
        "status": "success",
        "processed_chunks": len(chunks),
        "entities_extracted": len(db_entities),
        "relationships_extracted": len(db_relationships),
        "unresolved_relationships_skipped": unresolved_count,
    }

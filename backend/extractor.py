import os
import json
import logging
import uuid
import io
from typing import Dict, List, Tuple, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
import google.generativeai as genai
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("compliance-graphrag-extractor")

# Load environment variables
load_dotenv()

# Allowed entity and relationship types
ALLOWED_ENTITY_TYPES = {
    "person",
    "organization",
    "regulation",
    "system",
    "financial_instrument",
    "date_or_deadline",
    "location",
}

ALLOWED_RELATION_TYPES = {
    "employs",
    "supplies_to",
    "regulated_by",
    "violates",
    "flagged_for",
    "located_at",
    "reports_to",
    "party_to",
    "occurred_on",
}

# The system prompt to guide Gemini's extraction behavior
SYSTEM_PROMPT = """You are an expert enterprise compliance analyst and knowledge graph builder.
Your task is to analyze the provided compliance text chunk and extract entities and relationships.

TAXONOMY:
Only extract entities and relationships matching the following types. Do not invent any new types.

Entity Types:
1. person: Individual human beings.
2. organization: Companies, vendors, regulatory bodies, agencies, institutions.
3. regulation: Specific laws, acts, compliance standards, policies (e.g., SOX, GDPR, Section 404).
4. system: IT systems, software, databases, servers, applications, networks.
5. financial_instrument: Stocks, bonds, securities, derivatives, credit facilities, bank accounts.
6. date_or_deadline: Specific dates (YYYY-MM-DD or readable formats), deadlines.
7. location: Physical addresses, cities, countries, data centers.

Relationship Types:
1. employs: Organization -> Person (Organization employs Person)
2. supplies_to: Organization -> Organization (Organization supplies goods/services to Organization)
3. regulated_by: Organization/System -> Regulation (Organization/System is regulated by Regulation)
4. violates: Person/Organization/System -> Regulation (Person/Organization/System violates Regulation)
5. flagged_for: Person/Organization/System -> Regulation (Person/Organization/System is flagged under a Regulation/issue)
6. located_at: Organization/System/Person -> Location (Organization/System/Person is located at Location)
7. reports_to: Person -> Person, or Organization -> Organization (Person reports to Person, or subsidiary Organization reports to parent Organization)
8. party_to: Person/Organization -> Regulation/Agreement/Financial Instrument (Person/Organization is a party to an agreement or financial instrument)
9. occurred_on: Event/Violation/Action -> Date (An event, violation, or action occurred on a Date)

RULES:
1. Groundedness: Extract only entities and relationships that are explicitly mentioned in the text. Do not extrapolate, assume, or infer.
2. Name Consistency: The 'source_entity' and 'target_entity' names in the relationships array must match exactly (case, spelling) the 'name' field of an entity in the entities array.
3. Source Span: The 'source_span' field must contain the exact words from the text representing the entity or showing the relationship.
4. Source Location: Record the page number or section provided in the context (e.g. "Page X").
5. Format: Output ONLY a valid JSON object matching the schema below. No markdown wrapping except a raw JSON block if requested.

OUTPUT SCHEMA:
{
  "entities": [
    {
      "name": "Entity Name",
      "type": "person | organization | regulation | system | financial_instrument | date_or_deadline | location",
      "source_span": "exact substring",
      "source_location": "Page X"
    }
  ],
  "relationships": [
    {
      "source_entity": "Entity Name",
      "target_entity": "Entity Name",
      "relation_type": "employs | supplies_to | regulated_by | violates | flagged_for | located_at | reports_to | party_to | occurred_on",
      "source_span": "sentence or substring showing the connection",
      "source_location": "Page X"
    }
  ]
}

EXAMPLE:
Text: "On June 15, 2026, ACME Corp's primary database server, DB-PROD-01, located in Frankfurt, was audited by compliance officer Sarah Jenkins. The audit flagged the server for violating the GDPR data residency requirements."
JSON Output:
{
  "entities": [
    {"name": "Sarah Jenkins", "type": "person", "source_span": "Sarah Jenkins", "source_location": "Page 1"},
    {"name": "ACME Corp", "type": "organization", "source_span": "ACME Corp", "source_location": "Page 1"},
    {"name": "DB-PROD-01", "type": "system", "source_span": "DB-PROD-01", "source_location": "Page 1"},
    {"name": "Frankfurt", "type": "location", "source_span": "Frankfurt", "source_location": "Page 1"},
    {"name": "GDPR", "type": "regulation", "source_span": "GDPR", "source_location": "Page 1"},
    {"name": "June 15, 2026", "type": "date_or_deadline", "source_span": "June 15, 2026", "source_location": "Page 1"}
  ],
  "relationships": [
    {"source_entity": "ACME Corp", "target_entity": "Sarah Jenkins", "relation_type": "employs", "source_span": "ACME Corp's... compliance officer Sarah Jenkins", "source_location": "Page 1"},
    {"source_entity": "DB-PROD-01", "target_entity": "Frankfurt", "relation_type": "located_at", "source_span": "DB-PROD-01, located in Frankfurt", "source_location": "Page 1"},
    {"source_entity": "DB-PROD-01", "target_entity": "GDPR", "relation_type": "violates", "source_span": "flagged the server for violating the GDPR data residency requirements", "source_location": "Page 1"},
    {"source_entity": "DB-PROD-01", "target_entity": "June 15, 2026", "relation_type": "occurred_on", "source_span": "On June 15, 2026, ACME Corp's primary database server, DB-PROD-01... was audited", "source_location": "Page 1"}
  ]
}"""


def get_supabase_client() -> Client:
    """Initialize and return Supabase client using environment variables."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError(
            "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in environment variables."
        )
    return create_client(url, key)


def get_gemini_model() -> genai.GenerativeModel:
    """Initialize and return Gemini generative model configured with the system instruction."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY in environment variables.")
    genai.configure(api_key=api_key)
    # Using gemini-2.5-flash as the primary, cost-effective multimodal model
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash", system_instruction=SYSTEM_PROMPT
    )


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
        # Look for typical page fields: 'pages', 'page_cells', or similar layouts
        pages = extraction_metadata.get("pages")
        if isinstance(pages, list) and len(pages) > 0:
            logger.info(
                "Found page boundaries in extraction_metadata. Chunking by page."
            )
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

    # 2. Try to split by form-feed character (\f) which is standard for PDF-to-text converters
    if "\f" in raw_text:
        logger.info("Found form-feed markers in raw_text. Chunking by form-feed.")
        raw_pages = raw_text.split("\f")
        for idx, page in enumerate(raw_pages):
            if page.strip():
                chunks.append((page.strip(), f"Page {idx + 1}"))
        if chunks:
            return chunks

    # 3. Fallback: Chunk by characters (~1500 tokens is roughly 6000-8000 characters)
    # Using 6000 characters chunk size with 500 characters overlap
    logger.info(
        "No page boundaries or form-feed markers found. Falling back to token-equivalent character chunking."
    )
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


def validate_extraction_response(data: Dict[str, Any]) -> List[str]:
    """
    Validates the LLM json response against the required schema.
    Returns a list of errors. If empty, the response is valid.
    """
    errors = []

    if not isinstance(data, dict):
        return ["Response is not a JSON object/dictionary."]

    if "entities" not in data or not isinstance(data["entities"], list):
        errors.append("Missing or invalid 'entities' list.")
    else:
        for idx, entity in enumerate(data["entities"]):
            if not isinstance(entity, dict):
                errors.append(f"Entity at index {idx} is not an object.")
                continue

            # Check required fields
            for field in ["name", "type", "source_span", "source_location"]:
                if field not in entity or entity[field] is None:
                    errors.append(f"Entity at index {idx} is missing field '{field}'.")

            # Validate entity type
            ent_type = entity.get("type")
            if ent_type and ent_type not in ALLOWED_ENTITY_TYPES:
                errors.append(
                    f"Entity '{entity.get('name')}' uses invalid type '{ent_type}'. Must be one of: {', '.join(ALLOWED_ENTITY_TYPES)}"
                )

    if "relationships" not in data or not isinstance(data["relationships"], list):
        errors.append("Missing or invalid 'relationships' list.")
    else:
        for idx, rel in enumerate(data["relationships"]):
            if not isinstance(rel, dict):
                errors.append(f"Relationship at index {idx} is not an object.")
                continue

            # Check required fields
            for field in [
                "source_entity",
                "target_entity",
                "relation_type",
                "source_span",
                "source_location",
            ]:
                if field not in rel or rel[field] is None:
                    errors.append(
                        f"Relationship at index {idx} is missing field '{field}'."
                    )

            # Validate relation type
            rel_type = rel.get("relation_type")
            if rel_type and rel_type not in ALLOWED_RELATION_TYPES:
                errors.append(
                    f"Relationship index {idx} (source: '{rel.get('source_entity')}') uses invalid relation_type '{rel_type}'. Must be one of: {', '.join(ALLOWED_RELATION_TYPES)}"
                )

    return errors


def extract_chunk_entities(
    model: genai.GenerativeModel,
    chunk_text: str,
    location_label: str,
    user_instruction: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calls the LLM on a specific text chunk and returns the validated JSON data.
    Implements a single-retry mechanism on schema/type failures.
    """
    instruction_part = f"\n{user_instruction}\n" if user_instruction else ""
    prompt = f"Source Location Context: {location_label}\n{instruction_part}\nText to analyze:\n{chunk_text}"

    # Call Gemini model
    try:
        response = model.generate_content(
            prompt, generation_config={"response_mime_type": "application/json"}
        )
        response_text = response.text.strip()
        data = json.loads(response_text)
    except Exception as e:
        logger.error(
            f"Failed to fetch or parse JSON from LLM: {str(e)}. Retrying with warning."
        )
        return retry_extract_chunk(
            model,
            prompt,
            f"The response was not valid JSON or threw an exception: {str(e)}",
        )

    # Validate output
    errors = validate_extraction_response(data)
    if not errors:
        return data

    # Retry once with error feedback
    error_msg = "; ".join(errors)
    logger.warning(f"Schema validation failed on first attempt: {error_msg}. Retrying.")
    return retry_extract_chunk(
        model,
        prompt,
        f"Your previous response was invalid for the following reasons: {error_msg}",
    )


def retry_extract_chunk(
    model: genai.GenerativeModel, original_prompt: str, error_feedback: str
) -> Dict[str, Any]:
    """Helper to perform the single-retry LLM call with error feedback."""
    retry_prompt = f"{original_prompt}\n\n---\nCRITICAL RECORRECTION:\n{error_feedback}\n\nOnly return a valid JSON object complying exactly with the taxonomy and output schema rules."

    try:
        response = model.generate_content(
            retry_prompt, generation_config={"response_mime_type": "application/json"}
        )
        response_text = response.text.strip()
        data = json.loads(response_text)

        # Second validation
        errors = validate_extraction_response(data)
        if errors:
            logger.error(
                f"Retry validation failed. Skipping chunk. Errors: {'; '.join(errors)}"
            )
            return {"entities": [], "relationships": []}

        return data
    except Exception as e:
        logger.error(f"Retry attempt threw exception: {str(e)}. Skipping chunk.")
        return {"entities": [], "relationships": []}


def merge_entities(
    entities_list: List[Dict[str, Any]],
) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """
    Merges entities by name and type exactly (case and strip normalized).
    Aggregates source_span (unique list or first) and source_location.
    Preserves chronological order of locations.
    """
    merged: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for entity in entities_list:
        name = entity["name"].strip()
        ent_type = entity["type"].strip()
        loc = entity["source_location"].strip()
        span = entity["source_span"].strip()

        key = (name, ent_type)
        if key not in merged:
            merged[key] = {
                "name": name,
                "type": ent_type,
                "source_spans": {span},
                "source_locations": [loc],
            }
        else:
            merged[key]["source_spans"].add(span)
            if loc not in merged[key]["source_locations"]:
                merged[key]["source_locations"].append(loc)

    return merged


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

    # Fetch PDF doc from database
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

        # We record the mapping by lowercase name for robust relationship matching
        entity_id_map[name.lower()] = entity_uuid

        # Prepare list fields
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
                "embedding": None,  # Left NULL for now
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


def format_time_string(seconds: float) -> str:
    """Formats float seconds into a HH:MM:SS or MM:SS string."""
    sec = int(seconds)
    hours = sec // 3600
    minutes = (sec % 3600) // 60
    secs = sec % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def format_timestamp_range(start: float, end: float) -> str:
    """Formats start and end seconds into a range string."""
    return f"{format_time_string(start)} - {format_time_string(end)}"


def chunk_audio_by_timestamps(
    raw_text: str, extraction_metadata: Optional[Dict[str, Any]]
) -> List[Tuple[str, str]]:
    """
    Chunks raw_text by timestamp ranges:
    1. Checks extraction_metadata for segments with start/end timestamps and groups them into ~2-min intervals.
    2. Checks raw_text for timestamp patterns (e.g. [00:02:15] or [2:15]) using regex, and chunks by grouping.
    3. Falls back to token-equivalent character chunking (6000 chars) with timestamp labels.
    """
    chunks = []

    # 1. Try grouping Whisper/Gemini segment metadata
    if extraction_metadata and isinstance(extraction_metadata, dict):
        segments = extraction_metadata.get("segments")
        if isinstance(segments, list) and len(segments) > 0:
            logger.info(
                "Found segments in extraction_metadata. Chunking by time intervals."
            )
            current_chunk_text = []
            chunk_start = None

            for seg in segments:
                if not isinstance(seg, dict):
                    continue
                start = seg.get("start")
                end = seg.get("end")
                text = seg.get("text")
                if text is None or start is None or end is None:
                    continue

                if chunk_start is None:
                    chunk_start = float(start)

                # Exceeds ~2 minutes (120 seconds) chunk size
                if len(current_chunk_text) > 0 and (float(end) - chunk_start) > 120.0:
                    time_label = format_timestamp_range(
                        chunk_start, float(seg.get("start"))
                    )
                    chunks.append((" ".join(current_chunk_text).strip(), time_label))
                    current_chunk_text = [text]
                    chunk_start = float(start)
                else:
                    current_chunk_text.append(text)

            if current_chunk_text and chunk_start is not None:
                last_end = float(segments[-1].get("end", chunk_start + 120.0))
                time_label = format_timestamp_range(chunk_start, last_end)
                chunks.append((" ".join(current_chunk_text).strip(), time_label))

            if chunks:
                return chunks

    # 2. Try parsing inline timestamp markers via regex (e.g., [00:01:15], (1:15), [02:30])
    import re

    matches = list(
        re.finditer(r"(?:\[|\()(\d{1,2}:\d{2}(?::\d{2})?)(?:\]|\))", raw_text)
    )
    if matches:
        logger.info("Found timestamp markers in raw_text. Chunking by timestamps.")

        def parse_timestamp_to_seconds(ts_str: str) -> float:
            parts = list(map(int, ts_str.split(":")))
            if len(parts) == 3:
                return float(parts[0] * 3600 + parts[1] * 60 + parts[2])
            elif len(parts) == 2:
                return float(parts[0] * 60 + parts[1])
            return 0.0

        segments = []
        for idx, match in enumerate(matches):
            ts_str = match.group(1)
            start_pos = match.end()
            end_pos = (
                matches[idx + 1].start() if idx + 1 < len(matches) else len(raw_text)
            )
            segment_text = raw_text[start_pos:end_pos].strip()

            segments.append(
                {
                    "timestamp": ts_str,
                    "seconds": parse_timestamp_to_seconds(ts_str),
                    "text": segment_text,
                }
            )

        current_chunk_text = []
        chunk_start_ts = None
        chunk_start_secs = 0.0

        for seg in segments:
            if chunk_start_ts is None:
                chunk_start_ts = seg["timestamp"]
                chunk_start_secs = seg["seconds"]

            if (
                len(current_chunk_text) > 0
                and (seg["seconds"] - chunk_start_secs) > 120.0
            ):
                time_label = f"{chunk_start_ts} - {seg['timestamp']}"
                chunks.append((" ".join(current_chunk_text).strip(), time_label))
                current_chunk_text = [f"[{seg['timestamp']}] {seg['text']}"]
                chunk_start_ts = seg["timestamp"]
                chunk_start_secs = seg["seconds"]
            else:
                current_chunk_text.append(f"[{seg['timestamp']}] {seg['text']}")

        if current_chunk_text and chunk_start_ts is not None:
            last_ts = segments[-1]["timestamp"]
            time_label = f"{chunk_start_ts} - {last_ts}"
            chunks.append((" ".join(current_chunk_text).strip(), time_label))

        if chunks:
            return chunks

    # 3. Fallback: default character-based chunking (~1500 tokens / 3 mins duration)
    logger.info(
        "No timestamp markers or segments found. Falling back to default character chunking."
    )
    chunk_size = 6000
    overlap = 500
    text_len = len(raw_text)

    start = 0
    chunk_num = 1
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk_text = raw_text[start:end].strip()
        if chunk_text:
            start_min = (chunk_num - 1) * 3
            end_min = chunk_num * 3
            time_label = f"{start_min:02d}:00 - {end_min:02d}:00"
            chunks.append((chunk_text, time_label))
        start += chunk_size - overlap
        chunk_num += 1

    return chunks


def extract_entities_from_audio(document_id: str) -> dict:
    """
    Primary orchestration function for audio transcripts:
    1. Fetches raw_text and extraction_metadata from Supabase.
    2. Chunks text by timestamp ranges.
    3. Calls LLM with retry validation for each chunk, requesting timestamp-scoped locations.
    4. Merges duplicate entities, listing the chronological first mention timestamp first.
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

    # Scope check: Audio only
    if doc.get("doc_type") != "audio":
        logger.warning(
            f"Document {document_id} has type '{doc.get('doc_type')}', which is not 'audio'. Skipping."
        )
        return {"status": "skipped", "reason": "Not an audio document"}

    raw_text = doc.get("raw_text") or ""
    metadata = doc.get("extraction_metadata")

    if not raw_text.strip():
        logger.warning(
            f"Document {document_id} has empty raw_text. Nothing to extract."
        )
        return {"status": "skipped", "reason": "Empty raw_text"}

    # Chunk text
    chunks = chunk_audio_by_timestamps(raw_text, metadata)
    logger.info(f"Total chunks to process: {len(chunks)}")

    # Initialize Gemini model
    model = get_gemini_model()

    raw_entities = []
    raw_relationships = []

    user_instruction = (
        "This text is a transcript of an audio recording. "
        "source_location should be the approximate timestamp (e.g. '4:32' or '00:04:32') "
        "closest to where each entity or relationship is mentioned, based on the timestamp markers "
        "present in the transcript. If no timestamp markers are present for a given excerpt, "
        "use the nearest preceding timestamp marker."
    )

    # Extract from each chunk
    for chunk_text, location in chunks:
        logger.info(f"Extracting from {location}...")
        extracted_data = extract_chunk_entities(
            model, chunk_text, location, user_instruction
        )

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
        # Lists in merge_entities preserve the order of addition (chronological)
        locs_str = ", ".join(data["source_locations"])

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

def download_from_supabase_storage(supabase: Client, storage_path: str) -> bytes:
    """Downloads object from Supabase Storage, trying to guess the bucket from the path."""
    bucket = "documents"
    path = storage_path
    
    if "/" in storage_path:
        parts = storage_path.split("/", 1)
        possible_bucket = parts[0]
        possible_path = parts[1]
        try:
            res = supabase.storage.from_(possible_bucket).download(possible_path)
            return res
        except Exception:
            pass
            
    return supabase.storage.from_(bucket).download(path)

def clean_and_normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans a dataframe by:
    1. Skipping fully empty rows/columns.
    2. Shifting the header row if the first few rows look like headers.
    3. Stripping whitespace from headers and values.
    """
    df = df.dropna(how='all')
    df = df.dropna(axis=1, how='all')
    
    if df.empty:
        return df
        
    has_unnamed = any(str(col).startswith("Unnamed:") for col in df.columns) or all(isinstance(col, int) for col in df.columns)
    
    if has_unnamed and len(df) > 0:
        for idx in range(min(5, len(df))):
            row_vals = df.iloc[idx]
            non_null_count = row_vals.notnull().sum()
            if non_null_count > 0.5 * len(df.columns):
                new_header = [str(val).strip() for val in row_vals]
                df.columns = new_header
                df = df.iloc[idx + 1:]
                break
    else:
        df.columns = [str(col).strip() for col in df.columns]
        
    df = df.dropna(how='all')
    
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(lambda x: str(x).strip() if pd.notnull(x) else x)
            
    return df

def dataframe_to_markdown(df: pd.DataFrame) -> str:
    """Converts a pandas DataFrame to a markdown table string."""
    if df.empty:
        return ""
    headers = list(df.columns)
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        val_strs = []
        for col in headers:
            val = row[col]
            if pd.isnull(val):
                val_strs.append("")
            else:
                val_strs.append(str(val).replace('\n', ' ').replace('|', '\\|').strip())
        lines.append("| " + " | ".join(val_strs) + " |")
    return "\n".join(lines)

def chunk_markdown_table(markdown_text: str) -> List[Tuple[str, str]]:
    """
    Chunks markdown table text by row ranges (50 data rows per chunk).
    Each chunk preserves the table headers.
    Returns a list of tuples: (chunk_markdown, location_label).
    """
    chunks = []
    sheets = markdown_text.split("### Sheet: ")
    
    for sheet_part in sheets:
        if not sheet_part.strip():
            continue
            
        lines = sheet_part.strip().split("\n")
        sheet_name = None
        header_idx = -1
        sep_idx = -1
        
        for idx, line in enumerate(lines):
            cleaned = line.strip()
            if cleaned.startswith("|") and cleaned.endswith("|"):
                if header_idx == -1:
                    header_idx = idx
                elif sep_idx == -1 and "---" in cleaned:
                    sep_idx = idx
                    break
                    
        if header_idx == -1 or sep_idx == -1:
            continue
            
        header_line = lines[header_idx]
        sep_line = lines[sep_idx]
        
        if header_idx > 0:
            possible_name = lines[0].replace("###", "").strip()
            if possible_name:
                sheet_name = possible_name
                
        data_lines = lines[sep_idx + 1:]
        data_lines = [l for l in data_lines if l.strip().startswith("|")]
        
        if not data_lines:
            continue
            
        chunk_size = 50
        for i in range(0, len(data_lines), chunk_size):
            slice_lines = data_lines[i : i + chunk_size]
            chunk_table = [header_line, sep_line] + slice_lines
            chunk_text = "\n".join(chunk_table)
            
            start_row = i + 1
            end_row = min(i + chunk_size, len(data_lines))
            
            if sheet_name:
                loc_label = f"sheet: {sheet_name}, rows {start_row} to {end_row}"
            else:
                loc_label = f"rows {start_row} to {end_row}"
                
            chunks.append((chunk_text, loc_label))
            
    return chunks

def normalize_table(document_id: str) -> dict:
    """
    Downloads CSV/XLSX table from Supabase Storage, cleans it with pandas,
    converts it to a markdown table, and stores it in the documents table.
    """
    supabase = get_supabase_client()
    
    try:
        doc_res = supabase.table("documents").select("id, filename, doc_type, storage_path").eq("id", document_id).execute()
        if not doc_res.data:
            raise ValueError(f"Document with ID {document_id} not found.")
        doc = doc_res.data[0]
        
        if doc.get("doc_type") != "table":
            raise ValueError(f"Document {document_id} has type '{doc.get('doc_type')}', which is not 'table'.")
            
        storage_path = doc.get("storage_path")
        filename = doc.get("filename") or ""
        
        if not storage_path:
            raise ValueError(f"Document {document_id} has no storage_path.")
            
        logger.info(f"Downloading table file '{storage_path}' from storage...")
        file_bytes = download_from_supabase_storage(supabase, storage_path)
        
        is_excel = filename.lower().endswith(('.xlsx', '.xls')) or storage_path.lower().endswith(('.xlsx', '.xls'))
        
        markdown_text = ""
        row_count = 0
        column_names = []
        sheet_names = []
        
        if is_excel:
            xls = pd.ExcelFile(io.BytesIO(file_bytes))
            sheet_names = xls.sheet_names
            sheets_data = []
            
            for sheet in sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet)
                df_clean = clean_and_normalize_dataframe(df)
                if df_clean.empty:
                    continue
                    
                row_count += len(df_clean)
                column_names.extend(list(df_clean.columns))
                
                md_table = dataframe_to_markdown(df_clean)
                sheets_data.append(f"### Sheet: {sheet}\n\n{md_table}")
                
            markdown_text = "\n\n".join(sheets_data)
            column_names = list(set(column_names))
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))
            df_clean = clean_and_normalize_dataframe(df)
            
            row_count = len(df_clean)
            column_names = list(df_clean.columns)
            markdown_text = dataframe_to_markdown(df_clean)
            
        if not markdown_text.strip():
            raise ValueError("The parsed table is empty (contained no readable data/rows).")
            
        metadata = {
            "row_count": row_count,
            "column_names": column_names,
            "sheet_names": sheet_names
        }
        
        supabase.table("documents").update({
            "raw_text": markdown_text,
            "extraction_metadata": metadata,
            "status": "processed",
            "error_message": None
        }).eq("id", document_id).execute()
        
        return {
            "status": "success",
            "row_count": row_count,
            "column_names": column_names,
            "sheet_names": sheet_names
        }
        
    except Exception as e:
        logger.error(f"Failed to normalize table {document_id}: {str(e)}", exc_info=True)
        try:
            supabase.table("documents").update({
                "status": "failed",
                "error_message": str(e)
            }).eq("id", document_id).execute()
        except Exception as update_err:
            logger.error(f"Failed to update document failure status: {str(update_err)}")
        return {
            "status": "failed",
            "error": str(e)
        }

def extract_entities_from_table(document_id: str) -> dict:
    """
    Primary orchestration function for tables:
    1. Fetches normalized markdown representation from documents table.
    2. Chunks by row ranges (50 rows per chunk) preserving headers.
    3. Calls LLM with same-row relationship context and column descriptions.
    4. Merges entities and writes to entities and relationships tables.
    """
    supabase = get_supabase_client()
    
    logger.info(f"Fetching document {document_id} from database...")
    doc_res = supabase.table("documents").select("id, doc_type, raw_text, extraction_metadata, status, error_message").eq("id", document_id).execute()
    if not doc_res.data:
        raise ValueError(f"Document with ID {document_id} not found.")
        
    doc = doc_res.data[0]
    
    if doc.get("doc_type") != "table":
        logger.warning(f"Document {document_id} has type '{doc.get('doc_type')}', which is not 'table'. Skipping.")
        return {"status": "skipped", "reason": "Not a table document"}
        
    if doc.get("status") == "failed":
        logger.warning(f"Document {document_id} has failed parsing status. Skipping extraction.")
        return {"status": "skipped", "reason": f"Table parsing failed earlier: {doc.get('error_message')}"}
        
    raw_text = doc.get("raw_text") or ""
    metadata = doc.get("extraction_metadata") or {}
    columns = metadata.get("column_names") or []
    
    if not raw_text.strip():
        logger.warning(f"Document {document_id} has empty raw_text. Nothing to extract.")
        return {"status": "skipped", "reason": "Empty raw_text"}
        
    chunks = chunk_markdown_table(raw_text)
    logger.info(f"Total chunks to process: {len(chunks)}")
    
    model = get_gemini_model()
    
    raw_entities = []
    raw_relationships = []
    
    cols_str = ", ".join(columns)
    user_instruction = (
        "This text is a structured markdown table. The column headers in the table are: "
        f"{cols_str}.\n"
        "Please reason about what each column represents before extracting (e.g., columns with name-like headers "
        "imply person or organization entities, regulation-like headers imply regulation entities, etc.).\n"
        "source_location should be the specific row index (e.g., 'row 14' or 'sheet: SheetName, row 14') "
        "where each entity or relationship is located.\n"
        "Unlike prose where proximity does not imply relationship, co-occurrence of entities in the same table row "
        "is a strong indicator of relationships. Extract relationships between entities on the same row if the "
        "columns imply a logical connection (e.g. if a row links a vendor to a status or system, they are related)."
    )
    
    for chunk_text, location in chunks:
        logger.info(f"Extracting from {location}...")
        extracted_data = extract_chunk_entities(model, chunk_text, location, user_instruction)
        
        raw_entities.extend(extracted_data.get("entities", []))
        raw_relationships.extend(extracted_data.get("relationships", []))
        
    logger.info(f"Extracted {len(raw_entities)} raw entities and {len(raw_relationships)} raw relationships.")
    
    merged_entities_map = merge_entities(raw_entities)
    logger.info(f"Deduplicated to {len(merged_entities_map)} unique entities.")
    
    db_entities = []
    entity_id_map = {}
    
    for (name, ent_type), data in merged_entities_map.items():
        entity_uuid = str(uuid.uuid4())
        entity_id_map[name.lower()] = entity_uuid
        
        spans_str = ", ".join(list(data["source_spans"]))
        locs_str = ", ".join(data["source_locations"])
        
        db_entities.append({
            "id": entity_uuid,
            "name": data["name"],
            "type": data["type"],
            "source_doc_id": document_id,
            "source_span": spans_str,
            "source_location": locs_str,
            "embedding": None
        })
        
    db_relationships = []
    unresolved_count = 0
    
    for rel in raw_relationships:
        source_name = rel["source_entity"].strip().lower()
        target_name = rel["target_entity"].strip().lower()
        
        source_uuid = entity_id_map.get(source_name)
        target_uuid = entity_id_map.get(target_name)
        
        if not source_uuid or not target_uuid:
            logger.warning(f"Could not resolve relationship entity names: '{rel['source_entity']}' -> '{rel['target_entity']}'. Skipping.")
            unresolved_count += 1
            continue
            
        db_relationships.append({
            "id": str(uuid.uuid4()),
            "source_entity_id": source_uuid,
            "target_entity_id": target_uuid,
            "relation_type": rel["relation_type"],
            "source_doc_id": document_id,
            "source_span": rel["source_span"],
            "source_location": rel["source_location"]
        })
        
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
        "unresolved_relationships_skipped": unresolved_count
    }

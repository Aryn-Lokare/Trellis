import logging
import uuid
import re
from typing import Dict, List, Tuple, Any, Optional
from extractor import get_supabase_client, get_gemini_model, extract_chunk_entities, merge_entities

logger = logging.getLogger("compliance-graphrag-audio-extractor")

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
            logger.info("Found segments in extraction_metadata. Chunking by time intervals.")
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
    logger.info("No timestamp markers or segments found. Falling back to default character chunking.")
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

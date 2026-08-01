import os
import json
import logging
import uuid
from typing import Dict, List, Tuple, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
import google.generativeai as genai

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
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
    "location"
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
    "occurred_on"
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
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in environment variables.")
    return create_client(url, key)

def get_gemini_model() -> genai.GenerativeModel:
    """Initialize and return Gemini generative model configured with the system instruction."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY in environment variables.")
    genai.configure(api_key=api_key)
    # Using gemini-2.5-flash as the primary, cost-effective multimodal model
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT
    )

def chunk_text_by_pages(raw_text: str, extraction_metadata: Optional[Dict[str, Any]]) -> List[Tuple[str, str]]:
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
            logger.info("Found page boundaries in extraction_metadata. Chunking by page.")
            for p in pages:
                if not isinstance(p, dict):
                    continue
                page_num = p.get("page_num") or p.get("page_no") or p.get("number") or p.get("page")
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
        start += (chunk_size - overlap)
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
                errors.append(f"Entity '{entity.get('name')}' uses invalid type '{ent_type}'. Must be one of: {', '.join(ALLOWED_ENTITY_TYPES)}")

    if "relationships" not in data or not isinstance(data["relationships"], list):
        errors.append("Missing or invalid 'relationships' list.")
    else:
        for idx, rel in enumerate(data["relationships"]):
            if not isinstance(rel, dict):
                errors.append(f"Relationship at index {idx} is not an object.")
                continue
                
            # Check required fields
            for field in ["source_entity", "target_entity", "relation_type", "source_span", "source_location"]:
                if field not in rel or rel[field] is None:
                    errors.append(f"Relationship at index {idx} is missing field '{field}'.")
                    
            # Validate relation type
            rel_type = rel.get("relation_type")
            if rel_type and rel_type not in ALLOWED_RELATION_TYPES:
                errors.append(f"Relationship index {idx} (source: '{rel.get('source_entity')}') uses invalid relation_type '{rel_type}'. Must be one of: {', '.join(ALLOWED_RELATION_TYPES)}")

    return errors

def extract_chunk_entities(model: genai.GenerativeModel, chunk_text: str, location_label: str) -> Dict[str, Any]:
    """
    Calls the LLM on a specific text chunk and returns the validated JSON data.
    Implements a single-retry mechanism on schema/type failures.
    """
    prompt = f"Source Location Context: {location_label}\n\nText to analyze:\n{chunk_text}"
    
    # Call Gemini model
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        response_text = response.text.strip()
        data = json.loads(response_text)
    except Exception as e:
        logger.error(f"Failed to fetch or parse JSON from LLM: {str(e)}. Retrying with warning.")
        return retry_extract_chunk(model, prompt, f"The response was not valid JSON or threw an exception: {str(e)}")

    # Validate output
    errors = validate_extraction_response(data)
    if not errors:
        return data

    # Retry once with error feedback
    error_msg = "; ".join(errors)
    logger.warning(f"Schema validation failed on first attempt: {error_msg}. Retrying.")
    return retry_extract_chunk(model, prompt, f"Your previous response was invalid for the following reasons: {error_msg}")

def retry_extract_chunk(model: genai.GenerativeModel, original_prompt: str, error_feedback: str) -> Dict[str, Any]:
    """Helper to perform the single-retry LLM call with error feedback."""
    retry_prompt = f"{original_prompt}\n\n---\nCRITICAL RECORRECTION:\n{error_feedback}\n\nOnly return a valid JSON object complying exactly with the taxonomy and output schema rules."
    
    try:
        response = model.generate_content(
            retry_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        response_text = response.text.strip()
        data = json.loads(response_text)
        
        # Second validation
        errors = validate_extraction_response(data)
        if errors:
            logger.error(f"Retry validation failed. Skipping chunk. Errors: {'; '.join(errors)}")
            return {"entities": [], "relationships": []}
            
        return data
    except Exception as e:
        logger.error(f"Retry attempt threw exception: {str(e)}. Skipping chunk.")
        return {"entities": [], "relationships": []}

def merge_entities(entities_list: List[Dict[str, Any]]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """
    Merges entities by name and type exactly (case and strip normalized).
    Aggregates source_span (unique list or first) and source_location.
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
                "source_locations": {loc}
            }
        else:
            merged[key]["source_spans"].add(span)
            merged[key]["source_locations"].add(loc)
            
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
    doc_res = supabase.table("documents").select("id, doc_type, raw_text, extraction_metadata").eq("id", document_id).execute()
    if not doc_res.data:
        raise ValueError(f"Document with ID {document_id} not found.")
        
    doc = doc_res.data[0]
    
    # Scope check: PDF only
    if doc.get("doc_type") != "pdf":
        logger.warning(f"Document {document_id} has type '{doc.get('doc_type')}', which is not 'pdf'. Skipping.")
        return {"status": "skipped", "reason": "Not a PDF document"}
        
    raw_text = doc.get("raw_text") or ""
    metadata = doc.get("extraction_metadata")
    
    if not raw_text.strip():
        logger.warning(f"Document {document_id} has empty raw_text. Nothing to extract.")
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

    logger.info(f"Extracted {len(raw_entities)} raw entities and {len(raw_relationships)} raw relationships.")

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
        
        db_entities.append({
            "id": entity_uuid,
            "name": data["name"],
            "type": data["type"],
            "source_doc_id": document_id,
            "source_span": spans_str,
            "source_location": locs_str,
            "embedding": None  # Left NULL for now
        })

    # 2. Resolve relationship names to entity UUIDs
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
        "unresolved_relationships_skipped": unresolved_count
    }

import logging
import uuid
import os
import mimetypes
from typing import Dict, List, Tuple, Any, Optional
import google.generativeai as genai
from extractor import get_supabase_client, get_gemini_model, extract_chunk_entities, merge_entities
from table_extractor import download_from_supabase_storage

logger = logging.getLogger("compliance-graphrag-schematic-extractor")

def normalize_schematic(document_id: str) -> dict:
    """
    Downloads diagram image from Supabase Storage, calls Gemini 2.5 Flash
    multimodal vision to generate a detailed text description, and updates the document record.
    """
    supabase = get_supabase_client()
    
    try:
        # Fetch document record
        doc_res = supabase.table("documents").select("id, filename, doc_type, storage_path").eq("id", document_id).execute()
        if not doc_res.data:
            raise ValueError(f"Document with ID {document_id} not found.")
        doc = doc_res.data[0]
        
        if doc.get("doc_type") != "schematic":
            raise ValueError(f"Document {document_id} has type '{doc.get('doc_type')}', which is not 'schematic'.")
            
        storage_path = doc.get("storage_path")
        filename = doc.get("filename") or ""
        
        if not storage_path:
            raise ValueError(f"Document {document_id} has no storage_path.")
            
        logger.info(f"Downloading schematic image '{storage_path}' from storage...")
        file_bytes = download_from_supabase_storage(supabase, storage_path)
        
        # Detect mime type
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "image/png"  # fallback default
            
        logger.info("Calling Gemini 2.5 Flash vision capability to describe image...")
        
        # Configure genai with API key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY in environment variables.")
        genai.configure(api_key=api_key)
        
        # We instantiate a clean model (without custom system prompt/taxonomy filters)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = (
            "You are an expert compliance auditor and system architect. "
            "Analyze this system architecture diagram or data flow diagram. "
            "Write a detailed, structured textual description summarizing all systems, databases, user roles, "
            "external entities, locations, regulations, and their direct data flow connections. "
            "Ensure you explicitly list the source components, destination components, and the purpose "
            "of each connection so that a text-based extraction model can reconstruct the knowledge graph."
        )
        
        image_part = {
            "mime_type": mime_type,
            "data": file_bytes
        }
        
        response = model.generate_content([image_part, prompt])
        description = response.text
        
        if not description or not description.strip():
            raise ValueError("Gemini 2.5 Flash returned an empty description for the image.")
            
        logger.info("Successfully received description from Gemini 2.5 Flash.")
        
        metadata = {
            "image_type": mime_type,
            "char_count": len(description),
            "engine": "gemini-2.5-flash"
        }
        
        # Save to database
        supabase.table("documents").update({
            "raw_text": description,
            "extraction_metadata": metadata,
            "status": "processed",
            "error_message": None
        }).eq("id", document_id).execute()
        
        return {
            "status": "success",
            "description_length": len(description),
            "engine": "gemini-2.5-flash"
        }
        
    except Exception as e:
        logger.error(f"Failed to normalize schematic {document_id}: {str(e)}", exc_info=True)
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

def extract_entities_from_schematic(document_id: str) -> dict:
    """
    Primary orchestration function for schematics:
    1. Fetches textual description from documents table.
    2. Calls LLM with schematic user instructions.
    3. Merges entities and writes to entities and relationships tables.
    """
    supabase = get_supabase_client()
    
    logger.info(f"Fetching document {document_id} from database...")
    doc_res = supabase.table("documents").select("id, doc_type, raw_text, extraction_metadata, status, error_message").eq("id", document_id).execute()
    if not doc_res.data:
        raise ValueError(f"Document with ID {document_id} not found.")
        
    doc = doc_res.data[0]
    
    if doc.get("doc_type") != "schematic":
        logger.warning(f"Document {document_id} has type '{doc.get('doc_type')}', which is not 'schematic'. Skipping.")
        return {"status": "skipped", "reason": "Not a schematic document"}
        
    if doc.get("status") == "failed":
        logger.warning(f"Document {document_id} has failed parsing status. Skipping extraction.")
        return {"status": "skipped", "reason": f"Schematic parsing failed earlier: {doc.get('error_message')}"}
        
    raw_text = doc.get("raw_text") or ""
    
    if not raw_text.strip():
        logger.warning(f"Document {document_id} has empty raw_text. Nothing to extract.")
        return {"status": "skipped", "reason": "Empty raw_text"}
        
    # Since it is a textual description of a single diagram, we process the entire text as 1 chunk.
    chunks = [(raw_text, "diagram")]
    
    model = get_gemini_model()
    
    raw_entities = []
    raw_relationships = []
    
    user_instruction = (
        "This text is a description of a system architecture or data flow diagram. "
        "source_location should be 'diagram' or the specific section name if mentioned. "
        "Pay close attention to systems, databases, networks, companies, locations, and their data connections "
        "(e.g. data flows, dependency connections)."
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

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
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash", system_instruction=SYSTEM_PROMPT
    )


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

            for field in ["name", "type", "source_span", "source_location"]:
                if field not in entity or entity[field] is None:
                    errors.append(f"Entity at index {idx} is missing field '{field}'.")

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

    errors = validate_extraction_response(data)
    if not errors:
        return data

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


# Re-export modular components for backward compatibility
from pdf_extractor import chunk_text_by_pages, extract_entities_from_pdf
from audio_extractor import (
    format_time_string,
    format_timestamp_range,
    chunk_audio_by_timestamps,
    extract_entities_from_audio,
)
from table_extractor import (
    download_from_supabase_storage,
    clean_and_normalize_dataframe,
    dataframe_to_markdown,
    chunk_markdown_table,
    normalize_table,
    extract_entities_from_table,
)

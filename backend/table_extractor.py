import logging
import uuid
import io
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from supabase import Client
from extractor import get_supabase_client, get_gemini_model, extract_chunk_entities, merge_entities

logger = logging.getLogger("compliance-graphrag-table-extractor")

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

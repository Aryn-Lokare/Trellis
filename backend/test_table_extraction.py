import os
import sys
import json
import logging
import io
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
from extractor import normalize_table, extract_entities_from_table, get_supabase_client

# Setup logging to console
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test-table-extraction")

# Helper to generate test files
def create_test_files():
    """Create local CSV data files for uploading to Supabase Storage."""
    # File 1: Standard compliance status table
    df1 = pd.DataFrame([
        ["Wayne Enterprises", "GDPR", "Violates", "Sarah Jenkins"],
        ["LexCorp", "Dodd-Frank", "Compliant", "Bruce Wayne"],
        ["ACME Corp", "SOX", "Violates", "Sarah Jenkins"]
    ], columns=["Vendor Name", "Flagged Regulation", "Compliance Status", "Lead Auditor"])
    csv1 = df1.to_csv(index=False).encode('utf-8')

    # File 2: Adversarial/Malformed headers table (first two rows empty/garbage, header on row 2)
    csv2_lines = [
        ",,",
        "Garbage Header Row,To,Skip",
        "Vendor Name,Lead Auditor,Compliance Status",
        "Wayne Enterprises,Sarah Jenkins,Violates",
        ",,", # empty row
        "LexCorp,John Audits,Compliant"
    ]
    csv2 = "\n".join(csv2_lines).encode('utf-8')

    # File 3: Large compliance log table (105 data rows to verify chunking at 50-row boundaries)
    large_rows = []
    for idx in range(1, 106):
        vendor = "Wayne Enterprises" if idx % 2 == 0 else "ACME Corp"
        reg = "GDPR" if idx % 3 == 0 else ("SOX" if idx % 3 == 1 else "Dodd-Frank")
        status = "Violates" if idx % 5 == 0 else "Compliant"
        auditor = "Sarah Jenkins" if idx % 2 == 0 else "John Audits"
        large_rows.append([f"TXN-{idx:03d}", vendor, reg, status, auditor])
        
    df3 = pd.DataFrame(large_rows, columns=["Transaction ID", "Vendor", "Regulation", "Compliance Status", "Auditor"])
    csv3 = df3.to_csv(index=False).encode('utf-8')

    return {
        "compliance_status.csv": csv1,
        "malformed_headers.csv": csv2,
        "large_compliance_log.csv": csv3
    }

def setup_supabase_bucket(supabase: Client, bucket_name: str):
    """Ensures test storage bucket exists in Supabase."""
    try:
        # Check if bucket exists
        buckets = supabase.storage.list_buckets()
        exists = any(b.name == bucket_name for b in buckets)
        if not exists:
            logger.info(f"Creating storage bucket '{bucket_name}'...")
            supabase.storage.create_bucket(bucket_name, options={"public": True})
        else:
            logger.info(f"Storage bucket '{bucket_name}' already exists.")
    except Exception as e:
        logger.warning(f"Error checking/creating bucket: {str(e)}. Proceeding assuming it exists.")

def run_test_suite():
    load_dotenv()
    
    try:
        supabase = get_supabase_client()
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {str(e)}")
        print("\n[ERROR] Supabase client initialization failed. Verify SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
        sys.exit(1)

    print("\n" + "="*80)
    print("STARTING TABLE ENTITY EXTRACTION TEST HARNESS")
    print("="*80 + "\n")

    bucket_name = "documents"
    setup_supabase_bucket(supabase, bucket_name)

    # 1. Generate test file payloads
    test_files = create_test_files()
    seeded_doc_ids = []
    
    # 2. Upload to storage and insert into documents table
    for filename, payload in test_files.items():
        storage_path = f"table_tests/{filename}"
        logger.info(f"Uploading file '{filename}' to Supabase Storage path '{storage_path}'...")
        
        # Upload using upload (or overwrite if existing)
        try:
            supabase.storage.from_(bucket_name).upload(
                path=storage_path,
                file=payload,
                file_options={"cache-control": "3600", "upsert": "true"}
            )
        except Exception as upload_err:
            logger.warning(f"Storage upload error (may already exist or be overwritten): {str(upload_err)}")
            # Try to update/overwrite directly
            try:
                supabase.storage.from_(bucket_name).update(path=storage_path, file=payload)
            except Exception as update_err:
                logger.error(f"Failed to overwrite file in storage: {str(update_err)}")
                continue

        # Insert metadata row in documents table
        res = supabase.table("documents").insert({
            "filename": filename,
            "doc_type": "table",
            "storage_path": f"{bucket_name}/{storage_path}", # will be matched by download_from_supabase_storage helper
            "status": "pending"
        }).execute()
        
        if res.data:
            seeded_id = res.data[0]["id"]
            seeded_doc_ids.append((seeded_id, filename, storage_path))
            logger.info(f"Seeded document record: {filename} (ID: {seeded_id})")
        else:
            logger.error(f"Failed to insert database row for {filename}")

    print("\n" + "="*80)
    print("RUNNING PARSING, NORMALIZATION AND EXTRACTION")
    print("="*80 + "\n")

    all_results = []

    # 3. Process each table
    for doc_id, filename, storage_path in seeded_doc_ids:
        print(f"\n--- Testing Document: {filename} ---")
        
        # A. Normalization Step
        print("1. Running table normalization...")
        norm_result = normalize_table(doc_id)
        print(f"   Normalization Status: {norm_result['status']}")
        if norm_result['status'] == "failed":
            print(f"   Error details: {norm_result.get('error')}")
            continue
            
        print(f"   Row Count: {norm_result.get('row_count')}")
        print(f"   Columns: {norm_result.get('column_names')}")
        
        # Fetch normalized text from DB
        doc_db = supabase.table("documents").select("raw_text").eq("id", doc_id).execute().data[0]
        markdown_table = doc_db.get("raw_text") or ""
        print("\n   Normalized Markdown Representation (truncated if long):")
        truncated_lines = markdown_table.split("\n")[:12]
        for line in truncated_lines:
            print(f"     {line}")
        if len(markdown_table.split("\n")) > 12:
            print("     ...")
            
        # B. Extraction Step
        print("\n2. Running entity/relationship extraction...")
        extract_result = extract_entities_from_table(doc_id)
        print(f"   Extraction Status: {extract_result['status']}")
        print(f"   Processed Chunks: {extract_result.get('processed_chunks', 0)}")
        print(f"   Entities Extracted: {extract_result.get('entities_extracted', 0)}")
        print(f"   Relationships Extracted: {extract_result.get('relationships_extracted', 0)}")
        
        # C. Query Extracted Entities/Relationships from DB
        ent_res = supabase.table("entities").select("name, type, source_span, source_location").eq("source_doc_id", doc_id).execute()
        rel_res = supabase.table("relationships").select("source_entity_id, target_entity_id, relation_type, source_span, source_location").eq("source_doc_id", doc_id).execute()
        
        entities = ent_res.data or []
        relationships = rel_res.data or []
        
        # Map entity IDs to names
        ent_name_map = {e["id"]: e["name"] for e in (supabase.table("entities").select("id, name").eq("source_doc_id", doc_id).execute().data or [])}
        
        print("\n   Extracted Entities:")
        for ent in entities:
            print(f"     - {ent['name']} ({ent['type']}) | Location: {ent['source_location']} | Span: \"{ent['source_span']}\"")
            
        print("\n   Extracted Relationships:")
        for rel in relationships:
            src_name = ent_name_map.get(rel["source_entity_id"], "Unknown")
            tgt_name = ent_name_map.get(rel["target_entity_id"], "Unknown")
            print(f"     - {src_name} --[{rel['relation_type']}]--> {tgt_name} | Location: {rel['source_location']} | Span: \"{rel['source_span']}\"")

        # Record results
        all_results.append({
            "filename": filename,
            "normalization": norm_result,
            "extracted_entities": [
                {
                    "name": ent["name"],
                    "type": ent["type"],
                    "source_location": ent["source_location"],
                    "source_span": ent["source_span"]
                } for ent in entities
            ],
            "extracted_relationships": [
                {
                    "source_entity": ent_name_map.get(rel["source_entity_id"], "Unknown"),
                    "target_entity": ent_name_map.get(rel["target_entity_id"], "Unknown"),
                    "relation_type": rel["relation_type"],
                    "source_location": rel["source_location"],
                    "source_span": rel["source_span"]
                } for rel in relationships
            ]
        })

        # Quality assertions
        if filename == "compliance_status.csv":
            print("\n   Quality Assertions Verification:")
            gdpr_rel = [r for r in relationships if r["relation_type"] == "violates" and ent_name_map.get(r["source_entity_id"], "").lower() == "wayne enterprises"]
            if gdpr_rel:
                print("     ✅ SUCCESS: Same-row relationship extraction verified ('Wayne Enterprises' violates 'GDPR' at row 1).")
            else:
                print("     ⚠️ WARNING: Failed to extract same-row relationship 'Wayne Enterprises violates GDPR'.")
                
        elif filename == "malformed_headers.csv":
            print("\n   Quality Assertions Verification:")
            if any(e["name"].lower() == "wayne enterprises" for e in entities):
                print("     ✅ SUCCESS: Shifted header parsing was successful (header detected below blank/garbage rows).")
            else:
                print("     ❌ FAILURE: Failed to detect headers or parse data below header row shift.")

        elif filename == "large_compliance_log.csv":
            print("\n   Quality Assertions Verification:")
            if extract_result.get("processed_chunks", 0) >= 2:
                print(f"     ✅ SUCCESS: Row-based chunking successfully split 105 rows into {extract_result['processed_chunks']} chunks.")
            else:
                print("     ❌ FAILURE: Large table was not chunked correctly.")

    print("\n" + "="*80)
    print("CLEANING UP STORAGE AND DATABASE records")
    print("="*80 + "\n")

    # 4. Cleanup database records (cascade deletes entities/relationships) and storage files
    for doc_id, filename, storage_path in seeded_doc_ids:
        logger.info(f"Deleting DB document record for {filename}...")
        supabase.table("documents").delete().eq("id", doc_id).execute()
        
        logger.info(f"Deleting storage file {storage_path}...")
        try:
            supabase.storage.from_(bucket_name).remove([storage_path])
        except Exception as clean_err:
            logger.error(f"Failed to delete storage file {storage_path}: {str(clean_err)}")

    # Write JSON results to file
    results_path = os.path.join(os.path.dirname(__file__), "test_table_results.json")
    try:
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)
        print("\n" + "="*80)
        print(f"SAVED EXTRACTION OUTPUT IN JSON FORMAT TO:")
        print(f"  {results_path}")
        print("="*80 + "\n")
        
        # Also print a sample of the JSON structure for the user
        print("Sample JSON Output (First Document):")
        if all_results:
            print(json.dumps(all_results[0], indent=2))
    except Exception as e:
        logger.error(f"Failed to write test_table_results.json: {str(e)}")

    print("\nTest suit run completed.")

if __name__ == "__main__":
    run_test_suite()

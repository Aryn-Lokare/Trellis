import os
import sys
import json
import logging
from io import BytesIO
from dotenv import load_dotenv
from supabase import create_client, Client
from PIL import Image, ImageDraw, ImageFont
from extractor import normalize_schematic, extract_entities_from_schematic, get_supabase_client

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test-schematic-extraction")

def draw_test_diagram() -> bytes:
    """Generates an image of a system architecture flowchart using Pillow."""
    logger.info("Drawing synthetic test architecture diagram...")
    # Create white canvas
    img = Image.new("RGB", (800, 450), color="white")
    draw = ImageDraw.Draw(img)
    
    # Try to load a simple font or default to bitmap font
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    # Draw Frankfurt Data Center Box
    draw.rectangle([450, 50, 750, 150], outline="black", width=3)
    draw.text((470, 90), "Location:\nFrankfurt Data Center", fill="black", font=font)

    # Draw Database Server Box (DB-PROD-01)
    draw.rectangle([50, 180, 350, 280], outline="black", width=3)
    draw.text((70, 220), "IT System:\nDB-PROD-01 (Database)", fill="black", font=font)

    # Draw Regulation Box (GDPR Compliance Boundary)
    draw.rectangle([450, 300, 750, 400], outline="black", width=3)
    draw.text((470, 340), "Regulation:\nGDPR Data Residency Rule", fill="black", font=font)

    # Draw connecting lines
    # DB-PROD-01 -> Frankfurt Data Center
    draw.line([350, 200, 450, 120], fill="blue", width=3)
    draw.text((370, 140), "located_at", fill="blue", font=font)

    # DB-PROD-01 -> GDPR Compliance Boundary
    draw.line([350, 260, 450, 330], fill="red", width=3)
    draw.text((370, 300), "violates", fill="red", font=font)

    # Save to bytes
    out_buf = BytesIO()
    img.save(out_buf, format="PNG")
    return out_buf.getvalue()

def setup_supabase_bucket(supabase: Client, bucket_name: str):
    """Ensures test storage bucket exists in Supabase."""
    try:
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
    print("STARTING SCHEMATIC DIAGRAM ENTITY EXTRACTION TEST HARNESS")
    print("="*80 + "\n")

    bucket_name = "documents"
    setup_supabase_bucket(supabase, bucket_name)

    # 1. Generate local diagram payload
    image_payload = draw_test_diagram()
    filename = "test_architecture_flow.png"
    storage_path = f"schematic_tests/{filename}"
    
    # 2. Upload file to Supabase Storage
    logger.info(f"Uploading file '{filename}' to Supabase Storage path '{storage_path}'...")
    try:
        supabase.storage.from_(bucket_name).upload(
            path=storage_path,
            file=image_payload,
            file_options={"cache-control": "3600", "upsert": "true"}
        )
    except Exception as upload_err:
        logger.warning(f"Storage upload warning: {str(upload_err)}. Attempting to overwrite.")
        try:
            supabase.storage.from_(bucket_name).update(path=storage_path, file=image_payload)
        except Exception as update_err:
            logger.error(f"Failed to overwrite file in storage: {str(update_err)}")
            sys.exit(1)

    # 3. Create document record in documents table
    doc_id = None
    try:
        res = supabase.table("documents").insert({
            "filename": filename,
            "doc_type": "schematic",
            "storage_path": f"{bucket_name}/{storage_path}",
            "status": "pending"
        }).execute()
        if res.data:
            doc_id = res.data[0]["id"]
            logger.info(f"Seeded document record: {filename} (ID: {doc_id})")
        else:
            raise ValueError("Empty response on DB insertion")
    except Exception as db_err:
        logger.error(f"Failed to seed document in database: {str(db_err)}")
        sys.exit(1)

    print("\n" + "="*80)
    print("RUNNING MULTIMODAL INGESTION & KNOWLEDGE GRAPH EXTRACTION")
    print("="*80 + "\n")

    all_results = []

    try:
        # A. Normalization (Vision Description)
        print("1. Running diagram image normalization (Qwen2.5-VL-32B)...")
        norm_result = normalize_schematic(doc_id)
        print(f"   Normalization Status: {norm_result['status']}")
        if norm_result['status'] == "failed":
            print(f"   Error details: {norm_result.get('error')}")
            sys.exit(1)
            
        print(f"   Description length: {norm_result.get('description_length')} characters")
        
        # Fetch description text from database
        doc_db = supabase.table("documents").select("raw_text").eq("id", doc_id).execute().data[0]
        description_text = doc_db.get("raw_text") or ""
        print("\n   Qwen2.5-VL System Diagram Description:")
        print("-"*80)
        print(description_text)
        print("-"*80)

        # B. Extraction (Graph Synthesis)
        print("\n2. Running entity/relationship extraction (Gemini)...")
        extract_result = extract_entities_from_schematic(doc_id)
        print(f"   Extraction Status: {extract_result['status']}")
        print(f"   Entities Extracted: {extract_result.get('entities_extracted', 0)}")
        print(f"   Relationships Extracted: {extract_result.get('relationships_extracted', 0)}")
        
        # C. Query Extracted Graph from DB
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
            "description_text": description_text,
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

        # Quality Assertions
        print("\n   Quality Assertions Verification:")
        has_prod_db = any("db-prod-01" in ent["name"].lower() for ent in entities)
        has_frankfurt = any("frankfurt" in ent["name"].lower() for ent in entities)
        has_gdpr = any("gdpr" in ent["name"].lower() for ent in entities)
        
        if has_prod_db and has_frankfurt and has_gdpr:
            print("     ✅ SUCCESS: All core node entities extracted correctly (DB-PROD-01, Frankfurt, GDPR).")
        else:
            print("     ⚠️ WARNING: Some target diagram node entities were missed.")

        has_location_rel = any(r["relation_type"] == "located_at" for r in relationships)
        has_violation_rel = any(r["relation_type"] == "violates" for r in relationships)
        
        if has_location_rel and has_violation_rel:
            print("     ✅ SUCCESS: System relationships extracted correctly (located_at, violates).")
        else:
            print("     ⚠️ WARNING: Failed to capture all flowchart relationships.")

    except Exception as run_err:
        logger.error(f"Error during test suite run: {str(run_err)}", exc_info=True)

    print("\n" + "="*80)
    print("CLEANING UP STORAGE AND DATABASE records")
    print("="*80 + "\n")

    # 4. Clean up resources
    if doc_id:
        logger.info(f"Deleting DB document record for {filename}...")
        supabase.table("documents").delete().eq("id", doc_id).execute()
        
    logger.info(f"Deleting storage file {storage_path}...")
    try:
        supabase.storage.from_(bucket_name).remove([storage_path])
    except Exception as clean_err:
        logger.error(f"Failed to delete storage file {storage_path}: {str(clean_err)}")

    # Write JSON results to file
    results_path = os.path.join(os.path.dirname(__file__), "test_schematic_results.json")
    try:
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)
        print("\n" + "="*80)
        print(f"SAVED EXTRACTION OUTPUT IN JSON FORMAT TO:")
        print(f"  {results_path}")
        print("="*80 + "\n")
        
        # Print first document results preview
        print("Sample JSON Output:")
        if all_results:
            print(json.dumps(all_results[0], indent=2))
    except Exception as e:
        logger.error(f"Failed to write test_schematic_results.json: {str(e)}")

    print("\nTest suite run completed.")

if __name__ == "__main__":
    run_test_suite()

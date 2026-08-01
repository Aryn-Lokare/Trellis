import os
import sys
import json
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from extractor import extract_entities_from_audio, get_supabase_client

# Setup logging to console
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test-audio-extraction")

# Sample mock documents simulating audio transcript text and segment metadata
TEST_DOCUMENTS = [
    {
        "filename": "compliance_call_wayne.wav",
        "doc_type": "audio",
        "raw_text": "[00:01:15] Operator: Wayne Enterprises conference call. Welcome, CEO Bruce Wayne. [00:01:40] Bruce Wayne: Thank you. Today we're reviewing our relationship with Gotham City National Bank. They are a party to our Credit Agreement A-102. [00:02:10] Operator: Understood. [00:08:40] Bruce Wayne: Also, Wayne Enterprises employs Sarah Jenkins as our compliance lead. We want to ensure Wayne Enterprises complies with the Dodd-Frank Act.",
        "extraction_metadata": {
            "segments": [
                {
                    "start": 75.0,
                    "end": 100.0,
                    "text": "Wayne Enterprises conference call. Welcome, CEO Bruce Wayne."
                },
                {
                    "start": 100.0,
                    "end": 130.0,
                    "text": "Thank you. Today we're reviewing our relationship with Gotham City National Bank. They are a party to our Credit Agreement A-102."
                },
                {
                    "start": 130.0,
                    "end": 140.0,
                    "text": "Understood."
                },
                {
                    "start": 520.0,
                    "end": 560.0,
                    "text": "Also, Wayne Enterprises employs Sarah Jenkins as our compliance lead. We want to ensure Wayne Enterprises complies with the Dodd-Frank Act."
                }
            ]
        }
    },
    {
        "filename": "casual_lunch_smalltalk.wav",
        "doc_type": "audio",
        "raw_text": "[00:00:10] Operator: Hi, how are you? [00:00:15] John: Doing well. Did you see the game last night? [00:00:30] Operator: Yes, it was amazing! What are you planning for lunch today? [00:00:45] John: Probably just getting a sandwich from the deli down the street.",
        "extraction_metadata": {
            "segments": [
                {
                    "start": 10.0,
                    "end": 15.0,
                    "text": "Hi, how are you?"
                },
                {
                    "start": 15.0,
                    "end": 30.0,
                    "text": "Doing well. Did you see the game last night?"
                },
                {
                    "start": 30.0,
                    "end": 45.0,
                    "text": "Yes, it was amazing! What are you planning for lunch today?"
                },
                {
                    "start": 45.0,
                    "end": 60.0,
                    "text": "Probably just getting a sandwich from the deli down the street."
                }
            ]
        }
    },
    {
        "filename": "verbal_commitments_audit.wav",
        "doc_type": "audio",
        "raw_text": "[00:01:20] Manager: We have a compliance gap on our database server, DB-PROD-01, which is located in Frankfurt. [00:01:45] Sarah Jenkins: Yes, we violate the GDPR data residency guidelines there. We will resolve it. I commit that Wayne Enterprises will get that system GDPR compliant by next Friday, August 7, 2026.",
        "extraction_metadata": {
            "segments": [
                {
                    "start": 80.0,
                    "end": 105.0,
                    "text": "We have a compliance gap on our database server, DB-PROD-01, which is located in Frankfurt."
                },
                {
                    "start": 105.0,
                    "end": 150.0,
                    "text": "Yes, we violate the GDPR data residency guidelines there. We will resolve it. I commit that Wayne Enterprises will get that system GDPR compliant by next Friday, August 7, 2026."
                }
            ]
        }
    }
]

EXPECTED_OUTPUTS = {
    "compliance_call_wayne.wav": {
        "description": "Standard board call transcript. Wayne Enterprises mentioned at 1:15 and 8:40.",
        "expected_entities": ["Wayne Enterprises (organization)", "Bruce Wayne (person)", "Gotham City National Bank (organization)", "Credit Agreement A-102 (financial_instrument)", "Sarah Jenkins (person)", "Dodd-Frank Act (regulation)"],
        "expected_relationships": ["Wayne Enterprises employs Bruce Wayne", "Wayne Enterprises party_to Credit Agreement A-102", "Gotham City National Bank party_to Credit Agreement A-102", "Wayne Enterprises employs Sarah Jenkins", "Wayne Enterprises regulated_by Dodd-Frank Act"]
    },
    "casual_lunch_smalltalk.wav": {
        "description": "Adversarial test - casual chit-chat containing no compliance details.",
        "expected_entities": [],
        "expected_relationships": []
    },
    "verbal_commitments_audit.wav": {
        "description": "Verbal commitments and compliance action items call.",
        "expected_entities": ["DB-PROD-01 (system)", "Frankfurt (location)", "Sarah Jenkins (person)", "GDPR (regulation)", "Wayne Enterprises (organization)", "August 7, 2026 (date_or_deadline)"],
        "expected_relationships": ["DB-PROD-01 located_at Frankfurt", "DB-PROD-01 violates GDPR", "Wayne Enterprises employs Sarah Jenkins", "Wayne Enterprises violates GDPR", "GDPR regulated_by August 7, 2026"]
    }
}

def verify_tables_exist(supabase: Client) -> bool:
    """Check if required tables exist in Supabase by running a test select query."""
    try:
        supabase.table("documents").select("id").limit(1).execute()
        supabase.table("entities").select("id").limit(1).execute()
        supabase.table("relationships").select("id").limit(1).execute()
        return True
    except Exception as e:
        logger.error(f"Table verification failed: {str(e)}")
        return False

def run_test_suite():
    load_dotenv()
    
    try:
        supabase = get_supabase_client()
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {str(e)}")
        print("\n[ERROR] Supabase client initialization failed. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env.")
        sys.exit(1)
        
    if not verify_tables_exist(supabase):
        print("\n" + "="*80)
        print("[CRITICAL ERROR] Database tables do not exist or are not accessible.")
        print("Please run the SQL commands in apps/backend/schema.sql in your Supabase SQL Editor first!")
        print("="*80 + "\n")
        sys.exit(1)

    print("\n" + "="*80)
    print("STARTING HACKATHON AUDIO ENTITY EXTRACTION TEST HARNESS")
    print("="*80 + "\n")

    seeded_doc_ids = []
    all_results = []
    
    # 1. Seed the test mock documents
    logger.info("Seeding mock Audio documents in Supabase...")
    for doc in TEST_DOCUMENTS:
        res = supabase.table("documents").insert({
            "filename": doc["filename"],
            "doc_type": doc["doc_type"],
            "raw_text": doc["raw_text"],
            "extraction_metadata": doc["extraction_metadata"]
        }).execute()
        
        if res.data:
            seeded_id = res.data[0]["id"]
            seeded_doc_ids.append((seeded_id, doc["filename"]))
            logger.info(f"Seeded document: {doc['filename']} (ID: {seeded_id})")
        else:
            logger.error(f"Failed to seed {doc['filename']}")
            
    print("\n" + "="*80)
    print("RUNNING EXTRACTION WORKFLOWS")
    print("="*80 + "\n")

    # 2. Run extractor on each seeded document
    for doc_id, filename in seeded_doc_ids:
        print(f"\n--- Testing Document: {filename} ---")
        expected = EXPECTED_OUTPUTS[filename]
        print(f"Description: {expected['description']}")
        
        # Run the extraction function
        try:
            result = extract_entities_from_audio(doc_id)
            print(f"Extraction Status: {result['status']}")
            print(f"Processed Chunks: {result.get('processed_chunks', 0)}")
            print(f"Entities Extracted: {result.get('entities_extracted', 0)}")
            print(f"Relationships Extracted: {result.get('relationships_extracted', 0)}")
            print(f"Relationships Skipped (unresolved): {result.get('unresolved_relationships_skipped', 0)}")
            
            # Fetch extracted entities from database
            ent_res = supabase.table("entities").select("name, type, source_span, source_location").eq("source_doc_id", doc_id).execute()
            rel_res = supabase.table("relationships").select("source_entity_id, target_entity_id, relation_type, source_span, source_location").eq("source_doc_id", doc_id).execute()
            
            entities = ent_res.data or []
            relationships = rel_res.data or []
            
            # Map entity IDs to names for printing relationships
            ent_name_map = {e["id"]: e["name"] for e in (supabase.table("entities").select("id, name").eq("source_doc_id", doc_id).execute().data or [])}

            print("\nExtracted Entities:")
            for ent in entities:
                print(f"  - {ent['name']} ({ent['type']}) | Timestamp Location: {ent['source_location']} | Span: \"{ent['source_span']}\"")
                
            print("\nExtracted Relationships:")
            for rel in relationships:
                src_name = ent_name_map.get(rel["source_entity_id"], "Unknown")
                tgt_name = ent_name_map.get(rel["target_entity_id"], "Unknown")
                print(f"  - {src_name} --[{rel['relation_type']}]--> {tgt_name} | Location: {rel['source_location']} | Span: \"{rel['source_span']}\"")
                
            # Store formatted output in results list
            doc_result = {
                "document": filename,
                "description": expected["description"],
                "extracted_entities": [
                    {
                        "name": ent["name"],
                        "type": ent["type"],
                        "source_span": ent["source_span"],
                        "source_location": ent["source_location"]
                    } for ent in entities
                ],
                "extracted_relationships": [
                    {
                        "source_entity": ent_name_map.get(rel["source_entity_id"], "Unknown"),
                        "target_entity": ent_name_map.get(rel["target_entity_id"], "Unknown"),
                        "relation_type": rel["relation_type"],
                        "source_span": rel["source_span"],
                        "source_location": rel["source_location"]
                    } for rel in relationships
                ]
            }
            all_results.append(doc_result)
                
            # Manual comparison
            print("\nManual Quality Comparison Evaluation:")
            print(f"  Expected Entities: {expected['expected_entities']}")
            print(f"  Expected Relationships: {expected['expected_relationships']}")
            
            # Print a quick check
            missing_entities = [item for item in expected['expected_entities'] if not any(item.split(" (")[0].lower() in ent['name'].lower() for ent in entities)]
            spurious_entities = [ent['name'] for ent in entities if not any(ent['name'].lower() in item.lower() for item in expected['expected_entities'])]
            
            print(f"  Status Check:")
            if not expected['expected_entities'] and not entities:
                print("    ✅ SUCCESS: Adversarial test correctly returned empty entity sets.")
            else:
                if missing_entities:
                    print(f"    ⚠️ MISSING: Extractor missed expected entities: {missing_entities}")
                else:
                    print("    ✅ ALL expected entities extracted.")
                    
                if spurious_entities:
                    print(f"    ⚠️ SPURIOUS: Extractor extracted extra/hallucinated entities: {spurious_entities}")
                else:
                    print("    ✅ NO hallucinated/spurious entities found.")
                    
                # Specific check for merge duplicate location
                if filename == "compliance_call_wayne.wav":
                    wayne_ents = [e for e in entities if e["name"].lower() == "wayne enterprises"]
                    if wayne_ents:
                        loc = wayne_ents[0]["source_location"]
                        print(f"    ℹ️ Multi-mention Location Check ('Wayne Enterprises'): \"{loc}\"")
                        if "01:15" in loc and "08:40" in loc:
                            print("    ✅ SUCCESS: Both timestamps captured chronologically. First mention ('01:15') is listed first.")
                        elif "01:15" in loc:
                            print("    ✅ SUCCESS: Correctly defaulted to first mention timestamp.")
                        else:
                            print("    ❌ FAILURE: Did not capture the correct first mention timestamp.")
                            
        except Exception as e:
            logger.error(f"Error running extraction for {filename}: {str(e)}", exc_info=True)

    print("\n" + "="*80)
    print("CLEANING UP SEEDED TEST DATA")
    print("="*80 + "\n")

    # 3. Clean up the documents (this cascade-deletes entities and relationships as well)
    for doc_id, filename in seeded_doc_ids:
        logger.info(f"Deleting test document {filename}...")
        supabase.table("documents").delete().eq("id", doc_id).execute()
        
    # Write JSON results to file
    results_path = os.path.join(os.path.dirname(__file__), "test_audio_results.json")
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
        logger.error(f"Failed to write test_audio_results.json: {str(e)}")
        
    print("\nTest suit run completed.")

if __name__ == "__main__":
    run_test_suite()

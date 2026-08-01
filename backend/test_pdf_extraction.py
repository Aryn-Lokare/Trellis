import os
import sys
import json
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from extractor import extract_entities_from_pdf, get_supabase_client

# Setup logging to console
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test-pdf-extraction")

# Sample mock documents simulating PDF text and page metadata
TEST_DOCUMENTS = [
    {
        "filename": "gdpr_audit_acme_corp.pdf",
        "doc_type": "pdf",
        "raw_text": "On June 15, 2026, ACME Corp's compliance officer Sarah Jenkins initiated an audit of the primary database server, DB-PROD-01, located in Frankfurt. The audit checked the system's compliance with GDPR standards.\fSarah Jenkins completed the audit on June 18, 2026. The final report noted that the DB-PROD-01 database was regulated by GDPR, but was found in violation of Section 5 due to cross-border transfer. ACME Corp faces regulatory scrutiny from the European Data Protection Board.",
        "extraction_metadata": {
            "pages": [
                {
                    "page_num": 1,
                    "text": "On June 15, 2026, ACME Corp's compliance officer Sarah Jenkins initiated an audit of the primary database server, DB-PROD-01, located in Frankfurt. The audit checked the system's compliance with GDPR standards."
                },
                {
                    "page_num": 2,
                    "text": "Sarah Jenkins completed the audit on June 18, 2026. The final report noted that the DB-PROD-01 database was regulated by GDPR, but was found in violation of Section 5 due to cross-border transfer. ACME Corp faces regulatory scrutiny from the European Data Protection Board."
                }
            ]
        }
    },
    {
        "filename": "chocolate_chip_cookies.pdf",
        "doc_type": "pdf",
        "raw_text": "How to make the perfect chocolate chip cookies. Ingredients: 2 cups of all-purpose flour, 1 cup of unsalted butter at room temperature, 3/4 cup of granulated sugar, and 1 cup of chocolate chips. Bake at 375 degrees Fahrenheit for 10-12 minutes on a baking sheet. Let it cool on a wire rack.",
        "extraction_metadata": {
            "pages": [
                {
                    "page_num": 1,
                    "text": "How to make the perfect chocolate chip cookies. Ingredients: 2 cups of all-purpose flour, 1 cup of unsalted butter at room temperature, 3/4 cup of granulated sugar, and 1 cup of chocolate chips. Bake at 375 degrees Fahrenheit for 10-12 minutes on a baking sheet. Let it cool on a wire rack."
                }
            ]
        }
    },
    {
        "filename": "enterprise_systems_mapping.pdf",
        "doc_type": "pdf",
        "raw_text": "The IT map of Globex Corp identifies three critical systems: ERP-Main (regulated by SOX), CRM-Cloud (regulated by GDPR), and HR-Portal (regulated by HIPAA). ERP-Main is located in Chicago. CRM-Cloud is located in Dublin. HR-Portal is located in Munich. Chief Information Officer Michael Vance reports to CEO Arthur Pendelton. Globex Corp supplies software services to Stark Industries.",
        "extraction_metadata": {
            "pages": [
                {
                    "page_num": 1,
                    "text": "The IT map of Globex Corp identifies three critical systems: ERP-Main (regulated by SOX), CRM-Cloud (regulated by GDPR), and HR-Portal (regulated by HIPAA). ERP-Main is located in Chicago. CRM-Cloud is located in Dublin. HR-Portal is located in Munich. Chief Information Officer Michael Vance reports to CEO Arthur Pendelton. Globex Corp supplies software services to Stark Industries."
                }
            ]
        }
    },
    {
        "filename": "vendor_financials_2026.pdf",
        "doc_type": "pdf",
        "raw_text": "Vendor: Wayne Enterprises. Financial Instrument: Credit Agreement A-102. Date: August 1, 2026. Party to: Gotham City National Bank. Wayne Enterprises employs Bruce Wayne. Wayne Enterprises violates the Dodd-Frank Act.",
        "extraction_metadata": {
            "pages": [
                {
                    "page_num": 1,
                    "text": "Vendor: Wayne Enterprises. Financial Instrument: Credit Agreement A-102. Date: August 1, 2026. Party to: Gotham City National Bank. Wayne Enterprises employs Bruce Wayne. Wayne Enterprises violates the Dodd-Frank Act."
                }
            ]
        }
    }
]

EXPECTED_OUTPUTS = {
    "gdpr_audit_acme_corp.pdf": {
        "description": "Standard multi-page compliance report.",
        "expected_entities": ["Sarah Jenkins (person)", "ACME Corp (organization)", "DB-PROD-01 (system)", "Frankfurt (location)", "GDPR (regulation)", "June 15, 2026 (date_or_deadline)", "European Data Protection Board (organization)"],
        "expected_relationships": ["ACME Corp employs Sarah Jenkins", "DB-PROD-01 located_at Frankfurt", "DB-PROD-01 regulated_by GDPR", "DB-PROD-01 violates GDPR"]
    },
    "chocolate_chip_cookies.pdf": {
        "description": "Adversarial test - non-compliance recipe content.",
        "expected_entities": [],
        "expected_relationships": []
    },
    "enterprise_systems_mapping.pdf": {
        "description": "Dense test - high-density system mapping.",
        "expected_entities": ["Globex Corp (organization)", "ERP-Main (system)", "SOX (regulation)", "CRM-Cloud (system)", "GDPR (regulation)", "HR-Portal (system)", "HIPAA (regulation)", "Michael Vance (person)", "Arthur Pendelton (person)", "Stark Industries (organization)"],
        "expected_relationships": ["Globex Corp employs Michael Vance", "Michael Vance reports_to Arthur Pendelton", "ERP-Main regulated_by SOX", "CRM-Cloud regulated_by GDPR", "HR-Portal regulated_by HIPAA", "Globex Corp supplies_to Stark Industries"]
    },
    "vendor_financials_2026.pdf": {
        "description": "Financial and vendor compliance log.",
        "expected_entities": ["Wayne Enterprises (organization)", "Credit Agreement A-102 (financial_instrument)", "Gotham City National Bank (organization)", "Bruce Wayne (person)", "Dodd-Frank Act (regulation)", "August 1, 2026 (date_or_deadline)"],
        "expected_relationships": ["Wayne Enterprises party_to Credit Agreement A-102", "Gotham City National Bank party_to Credit Agreement A-102", "Wayne Enterprises employs Bruce Wayne", "Wayne Enterprises violates Dodd-Frank Act"]
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
    print("STARTING HACKATHON PDF ENTITY EXTRACTION TEST HARNESS")
    print("="*80 + "\n")

    seeded_doc_ids = []
    all_results = []
    
    # 1. Seed the test mock documents
    logger.info("Seeding mock PDF documents in Supabase...")
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
            result = extract_entities_from_pdf(doc_id)
            print(f"Extraction Status: {result['status']}")
            print(f"Processed Chunks: {result.get('processed_chunks', 0)}")
            print(f"Entities Extracted: {result.get('entities_extracted', 0)}")
            print(f"Relationships Extracted: {result.get('relationships_extracted', 0)}")
            print(f"Relationships Skipped (unresolved): {result.get('unresolved_relationships_skipped', 0)}")
            
            # Fetch extracted entities from database
            ent_res = supabase.table("entities").select("name, type, source_span, source_location").eq("source_doc_id", doc_id).execute()
            rel_res = supabase.table("relationships").select("source_entity_id, target_entity_id, relation_type, source_span").eq("source_doc_id", doc_id).execute()
            
            entities = ent_res.data or []
            relationships = rel_res.data or []
            
            # Map entity IDs to names for printing relationships
            ent_name_map = {e["id"]: e["name"] for e in (supabase.table("entities").select("id, name").eq("source_doc_id", doc_id).execute().data or [])}

            print("\nExtracted Entities:")
            for ent in entities:
                print(f"  - {ent['name']} ({ent['type']}) | Location: {ent['source_location']} | Span: \"{ent['source_span']}\"")
                
            print("\nExtracted Relationships:")
            for rel in relationships:
                src_name = ent_name_map.get(rel["source_entity_id"], "Unknown")
                tgt_name = ent_name_map.get(rel["target_entity_id"], "Unknown")
                print(f"  - {src_name} --[{rel['relation_type']}]--> {tgt_name} | Span: \"{rel['source_span']}\"")
                
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
                        "source_span": rel["source_span"]
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
    results_path = os.path.join(os.path.dirname(__file__), "test_results.json")
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
        logger.error(f"Failed to write test_results.json: {str(e)}")
        
    print("\nTest suit run completed.")

if __name__ == "__main__":
    run_test_suite()

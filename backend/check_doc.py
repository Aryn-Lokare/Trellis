import os
from dotenv import load_dotenv
from extractor import get_supabase_client

load_dotenv()
supabase = get_supabase_client()

doc_id = "7c072ca9-9181-4d22-97fa-ec5dd4858fd3"
print(f"Checking document {doc_id}...")
res = supabase.table("documents").select("*").eq("id", doc_id).execute()
if res.data:
    doc = res.data[0]
    print(f"Status: {doc.get('status')}")
    print(f"Error Message: {doc.get('error_message')}")
    print(f"Raw Text Length: {len(doc.get('raw_text') or '')}")
    print(f"Metadata: {doc.get('extraction_metadata')}")
    
    # Check if there are any entities linked to this document
    ent_res = supabase.table("entities").select("id, name, type").eq("source_doc_id", doc_id).execute()
    print(f"\nEntities extracted for this document: {len(ent_res.data or [])}")
    for ent in (ent_res.data or []):
         print(f"  - {ent['name']} ({ent['type']})")
         
    # Check if there are any relationships linked to this document
    rel_res = supabase.table("relationships").select("id, relation_type").eq("source_doc_id", doc_id).execute()
    print(f"\nRelationships extracted: {len(rel_res.data or [])}")
else:
    print("Document not found.")

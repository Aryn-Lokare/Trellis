import os
from dotenv import load_dotenv
from extractor import get_supabase_client

load_dotenv()
supabase = get_supabase_client()

print("=== ALL ENTITIES IN DB ===")
ent_res = supabase.table("entities").select("id, name, type, source_doc_id").execute()
entities = ent_res.data or []
for ent in entities:
    print(f"[{ent['id'][:8]}] {ent['name']} ({ent['type']})")

print("\n=== ALL RELATIONSHIPS IN DB ===")
rel_res = supabase.table("relationships").select("id, source_entity_id, target_entity_id, relation_type").execute()
relationships = rel_res.data or []

# Create a map for easy lookup
ent_map = {ent['id']: ent['name'] for ent in entities}
for rel in relationships:
    src_name = ent_map.get(rel['source_entity_id'], rel['source_entity_id'][:8])
    tgt_name = ent_map.get(rel['target_entity_id'], rel['target_entity_id'][:8])
    print(f"  {src_name} --[{rel['relation_type']}]--> {tgt_name}")

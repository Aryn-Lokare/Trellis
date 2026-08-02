import os
from dotenv import load_dotenv
from extractor import get_supabase_client

load_dotenv()
supabase = get_supabase_client()

doc_id = "7eea59f9-f413-4cd6-a999-de0b07df1dfe"
print(f"=== ENTITIES FOR PDF {doc_id} ===")
res = supabase.table("entities").select("name, type, source_span").eq("source_doc_id", doc_id).execute()
for e in (res.data or []):
    print(f"- {e['name']} ({e['type']}) | Span: \"{e['source_span']}\"")

print(f"\n=== RELATIONSHIPS FOR PDF {doc_id} ===")
res = supabase.table("relationships").select("source_entity_id, target_entity_id, relation_type, source_span").eq("source_doc_id", doc_id).execute()
# Get entity name map
ent_res = supabase.table("entities").select("id, name").execute()
ent_map = {e['id']: e['name'] for e in (ent_res.data or [])}

for r in (res.data or []):
    src = ent_map.get(r['source_entity_id'], r['source_entity_id'][:8])
    tgt = ent_map.get(r['target_entity_id'], r['target_entity_id'][:8])
    print(f"- {src} --[{r['relation_type']}]--> {tgt} | Span: \"{r['source_span']}\"")

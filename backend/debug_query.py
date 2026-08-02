import os
import uuid
import logging
from dotenv import load_dotenv
from extractor import get_supabase_client, generate_embeddings_batch

logging.basicConfig(level=logging.INFO)
load_dotenv()
supabase = get_supabase_client()

# Seed a test document
doc_res = supabase.table("documents").insert({
    "filename": "debug_doc.pdf",
    "doc_type": "pdf",
    "status": "processed"
}).execute()
doc_id = doc_res.data[0]["id"]
print(f"Seeded document: {doc_id}")

# Seed one entity
entities = [
    {"id": str(uuid.uuid4()), "name": "Wayne Enterprises", "type": "organization", "source_doc_id": doc_id}
]

# Generate embedding
texts = [f"{e['name']} ({e['type']})" for e in entities]
print("Generating embedding for Wayne Enterprises...")
embeddings = generate_embeddings_batch(texts)
entities[0]["embedding"] = embeddings[0]

print("First 10 dimensions of entity embedding:", embeddings[0][:10])

# Insert entity
ent_res = supabase.table("entities").insert(entities).execute()
ent_id = ent_res.data[0]["id"]
print(f"Inserted entity: {ent_id}")

# Fetch back from database to verify embedding is populated and matches length
check_res = supabase.table("entities").select("id, name, type, embedding").eq("id", ent_id).execute()
check_ent = check_res.data[0]
db_embedding = check_ent.get("embedding")
if db_embedding:
    print(f"Embedding length in DB: {len(db_embedding)}")
    print(f"First 10 dimensions from DB: {db_embedding[:10]}")
else:
    print("Embedding in DB is NULL!")

# Run direct match query
import google.generativeai as genai
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
query_res = genai.embed_content(
    model="models/embedding-001",
    content="Which regulation does Wayne Enterprises violate?",
    task_type="retrieval_query"
)
query_vector = query_res["embedding"]
print("First 10 dimensions of query embedding:", query_vector[:10])

print("\nCalling match_entities RPC with match_threshold = -1.0...")
rpc_res = supabase.rpc("match_entities", {
    "query_embedding": query_vector,
    "match_threshold": -1.0,
    "match_count": 5
}).execute()

print("RPC Results:")
for row in (rpc_res.data or []):
    print(f"  Entity: {row['name']} | Similarity: {row['similarity']}")

# Cleanup
supabase.table("documents").delete().eq("id", doc_id).execute()
print("Cleanup complete.")

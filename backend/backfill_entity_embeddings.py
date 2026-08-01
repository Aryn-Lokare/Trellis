"""
One-time script to backfill 768-dimensional embeddings for existing entities
where the embedding column is NULL.
"""

import os
import sys
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from extractor import get_supabase_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("backfill-embeddings")


def backfill_embeddings():
    load_dotenv()
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("Missing GEMINI_API_KEY in environment variables.")
        sys.exit(1)
        
    genai.configure(api_key=api_key)
    supabase = get_supabase_client()

    logger.info("Fetching entities with NULL embeddings...")
    res = supabase.table("entities").select("id, name, type").is_("embedding", "null").execute()
    
    entities = res.data or []
    if not entities:
        logger.info("No entities found with NULL embeddings. Backfill complete.")
        return

    logger.info(f"Found {len(entities)} entities to embed. Starting backfill...")

    batch_size = 20
    for i in range(0, len(entities), batch_size):
        batch = entities[i:i+batch_size]
        texts = [f"{e['name']} ({e['type']})" for e in batch]
        
        try:
            logger.info(f"Generating embeddings for batch {i//batch_size + 1} (size {len(batch)})...")
            embed_res = genai.embed_content(
                model="models/gemini-embedding-2",
                content=texts,
                task_type="retrieval_document",
                output_dimensionality=768
            )
            
            embeddings = embed_res["embedding"]
            
            # Update each entity individually in Supabase
            for idx, ent in enumerate(batch):
                vector = embeddings[idx]
                supabase.table("entities").update({
                    "embedding": vector
                }).eq("id", ent["id"]).execute()
                
            logger.info(f"Successfully backfilled batch {i//batch_size + 1}.")
            
        except Exception as e:
            logger.error(f"Error backfilling batch: {str(e)}")
            # Continue to next batch instead of crashing
            continue

    logger.info("Deduplicating and backfilling complete.")


if __name__ == "__main__":
    backfill_embeddings()

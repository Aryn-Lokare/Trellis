"""
Test harness for cross-format entity deduplication.

Seeds overlapping entities across 3 mock documents (simulating PDF, audio, table extraction),
runs deduplication, and validates:
  - Entity count is reduced (3 "Wayne Enterprises" rows -> 1)
  - All relationships point to the canonical entity
  - entity_sources preserves all 3 document references
"""

import os
import sys
import json
import logging
import uuid
from dotenv import load_dotenv
from extractor import get_supabase_client, deduplicate_entities

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test-dedup")


def run_test_suite():
    load_dotenv()

    try:
        supabase = get_supabase_client()
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {str(e)}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("STARTING CROSS-FORMAT ENTITY DEDUPLICATION TEST HARNESS")
    print("=" * 80 + "\n")

    # 1. Seed 3 mock document records
    doc_ids = []
    for doc_type, filename in [
        ("pdf", "test_dedup_report.pdf"),
        ("audio", "test_dedup_call.wav"),
        ("table", "test_dedup_vendors.csv"),
    ]:
        res = supabase.table("documents").insert({
            "filename": filename,
            "doc_type": doc_type,
            "raw_text": f"Mock {doc_type} content for dedup testing.",
            "status": "processed",
        }).execute()
        doc_id = res.data[0]["id"]
        doc_ids.append(doc_id)
        logger.info(f"Seeded mock document: {filename} (ID: {doc_id})")

    # 2. Seed overlapping entities across the 3 documents
    #    "Wayne Enterprises" (organization) appears in all 3
    #    "Sarah Jenkins" (person) appears in PDF and table
    #    "GDPR" (regulation) appears in PDF and audio
    #    "DB-PROD-01" (system) appears only in PDF (should NOT be merged)

    shared_entities = [
        # Wayne Enterprises in PDF
        {"name": "Wayne Enterprises", "type": "organization", "source_doc_id": doc_ids[0],
         "source_span": "Wayne Enterprises", "source_location": "Page 1"},
        # Wayne Enterprises in Audio
        {"name": "Wayne Enterprises", "type": "organization", "source_doc_id": doc_ids[1],
         "source_span": "Wayne Enterprises", "source_location": "01:15"},
        # Wayne Enterprises in Table
        {"name": "Wayne Enterprises", "type": "organization", "source_doc_id": doc_ids[2],
         "source_span": "Wayne Enterprises", "source_location": "row 1"},

        # Sarah Jenkins in PDF
        {"name": "Sarah Jenkins", "type": "person", "source_doc_id": doc_ids[0],
         "source_span": "Sarah Jenkins", "source_location": "Page 3"},
        # Sarah Jenkins in Table
        {"name": "Sarah Jenkins", "type": "person", "source_doc_id": doc_ids[2],
         "source_span": "Sarah Jenkins", "source_location": "row 2"},

        # GDPR in PDF
        {"name": "GDPR", "type": "regulation", "source_doc_id": doc_ids[0],
         "source_span": "GDPR", "source_location": "Page 2"},
        # GDPR in Audio
        {"name": "GDPR", "type": "regulation", "source_doc_id": doc_ids[1],
         "source_span": "GDPR", "source_location": "08:40"},

        # DB-PROD-01 only in PDF (no duplicates)
        {"name": "DB-PROD-01", "type": "system", "source_doc_id": doc_ids[0],
         "source_span": "DB-PROD-01", "source_location": "Page 4"},
    ]

    entity_ids = []
    for ent in shared_entities:
        ent_id = str(uuid.uuid4())
        ent["id"] = ent_id
        ent["embedding"] = None
        entity_ids.append(ent_id)

    supabase.table("entities").insert(shared_entities).execute()
    logger.info(f"Seeded {len(shared_entities)} overlapping entities across 3 documents.")

    # 3. Seed entity_sources provenance rows
    sources = []
    for ent in shared_entities:
        sources.append({
            "entity_id": ent["id"],
            "source_doc_id": ent["source_doc_id"],
            "source_span": ent["source_span"],
            "source_location": ent["source_location"],
        })
    supabase.table("entity_sources").insert(sources).execute()
    logger.info(f"Seeded {len(sources)} entity_sources provenance rows.")

    # 4. Seed relationships that reference different entity IDs for "Wayne Enterprises"
    #    This tests that relationship FK rewiring works correctly.
    wayne_pdf_id = entity_ids[0]   # Wayne from PDF
    wayne_audio_id = entity_ids[1] # Wayne from Audio
    sarah_pdf_id = entity_ids[3]   # Sarah from PDF
    gdpr_pdf_id = entity_ids[5]    # GDPR from PDF
    gdpr_audio_id = entity_ids[6]  # GDPR from Audio

    test_relationships = [
        # Wayne (PDF) employs Sarah (PDF)
        {"source_entity_id": wayne_pdf_id, "target_entity_id": sarah_pdf_id,
         "relation_type": "employs", "source_doc_id": doc_ids[0],
         "source_span": "Wayne Enterprises employs Sarah Jenkins", "source_location": "Page 3"},
        # Wayne (Audio) regulated_by GDPR (Audio)
        {"source_entity_id": wayne_audio_id, "target_entity_id": gdpr_audio_id,
         "relation_type": "regulated_by", "source_doc_id": doc_ids[1],
         "source_span": "Wayne Enterprises regulated by GDPR", "source_location": "08:40"},
    ]

    rel_ids = []
    for rel in test_relationships:
        rel_id = str(uuid.uuid4())
        rel["id"] = rel_id
        rel_ids.append(rel_id)

    supabase.table("relationships").insert(test_relationships).execute()
    logger.info(f"Seeded {len(test_relationships)} relationships referencing different Wayne/GDPR IDs.")

    # ==================== SNAPSHOT BEFORE ====================
    before_count = len(supabase.table("entities")
        .select("id")
        .in_("source_doc_id", doc_ids)
        .execute().data)
    print(f"\n  BEFORE DEDUP: {before_count} entity rows across test documents")

    # ==================== RUN DEDUPLICATION ====================
    print("\n" + "=" * 80)
    print("RUNNING CROSS-FORMAT ENTITY DEDUPLICATION")
    print("=" * 80 + "\n")

    result = deduplicate_entities()

    for k, v in result.items():
        print(f"  {k}: {v}")

    # ==================== SNAPSHOT AFTER ====================
    after_entities = supabase.table("entities").select("id, name, type, source_span, source_location").in_("source_doc_id", doc_ids).execute().data
    after_count = len(after_entities)
    print(f"\n  AFTER DEDUP: {after_count} entity rows across test documents")

    # ==================== ASSERTIONS ====================
    print("\n" + "=" * 80)
    print("QUALITY ASSERTIONS")
    print("=" * 80 + "\n")

    # A1: Wayne Enterprises should be exactly 1 row
    wayne_rows = [e for e in after_entities if e["name"].lower() == "wayne enterprises"]
    if len(wayne_rows) == 1:
        print("  ✅ Wayne Enterprises: deduplicated to 1 row (was 3)")
        wayne_canonical = wayne_rows[0]
        # Check merged locations
        if "Page 1" in wayne_canonical["source_location"] and "01:15" in wayne_canonical["source_location"] and "row 1" in wayne_canonical["source_location"]:
            print("  ✅ Wayne Enterprises: source_location contains all 3 document references")
        else:
            print(f"  ⚠️ Wayne Enterprises: source_location = '{wayne_canonical['source_location']}' (expected Page 1, 01:15, row 1)")
    else:
        print(f"  ❌ Wayne Enterprises: expected 1 row, got {len(wayne_rows)}")

    # A2: Sarah Jenkins should be exactly 1 row
    sarah_rows = [e for e in after_entities if e["name"].lower() == "sarah jenkins"]
    if len(sarah_rows) == 1:
        print("  ✅ Sarah Jenkins: deduplicated to 1 row (was 2)")
    else:
        print(f"  ❌ Sarah Jenkins: expected 1 row, got {len(sarah_rows)}")

    # A3: GDPR should be exactly 1 row
    gdpr_rows = [e for e in after_entities if e["name"].lower() == "gdpr"]
    if len(gdpr_rows) == 1:
        print("  ✅ GDPR: deduplicated to 1 row (was 2)")
    else:
        print(f"  ❌ GDPR: expected 1 row, got {len(gdpr_rows)}")

    # A4: DB-PROD-01 should still be exactly 1 row (was never duplicated)
    db_rows = [e for e in after_entities if e["name"].lower() == "db-prod-01"]
    if len(db_rows) == 1:
        print("  ✅ DB-PROD-01: unchanged (1 row, no duplicates)")
    else:
        print(f"  ❌ DB-PROD-01: expected 1 row, got {len(db_rows)}")

    # A5: Relationships should all point to canonical IDs now
    after_rels = supabase.table("relationships").select("*").in_("source_doc_id", doc_ids).execute().data
    remaining_entity_ids = {e["id"] for e in after_entities}
    broken_rels = [r for r in after_rels if r["source_entity_id"] not in remaining_entity_ids or r["target_entity_id"] not in remaining_entity_ids]
    if not broken_rels:
        print("  ✅ All relationships point to canonical (non-deleted) entity IDs")
    else:
        print(f"  ❌ {len(broken_rels)} relationships point to deleted entity IDs!")

    # A6: entity_sources should have provenance for all original documents
    if wayne_rows:
        wayne_sources = supabase.table("entity_sources").select("*").eq("entity_id", wayne_rows[0]["id"]).execute().data
        if len(wayne_sources) >= 3:
            print(f"  ✅ Wayne Enterprises entity_sources: {len(wayne_sources)} provenance rows (≥3 expected)")
        else:
            print(f"  ⚠️ Wayne Enterprises entity_sources: {len(wayne_sources)} provenance rows (expected ≥3)")

    # ==================== CLEANUP ====================
    print("\n" + "=" * 80)
    print("CLEANING UP TEST DATA")
    print("=" * 80 + "\n")

    for doc_id in doc_ids:
        logger.info(f"Deleting document {doc_id}...")
        supabase.table("documents").delete().eq("id", doc_id).execute()

    print("Test suite run completed.\n")


if __name__ == "__main__":
    run_test_suite()

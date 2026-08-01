"""
Cross-format entity deduplication script.

Groups entities by normalized (name, type), picks a canonical entity per group,
rewires all relationships to point to the canonical, migrates entity_sources
provenance rows, and deletes duplicate entity rows.

Idempotent — safe to run multiple times.
"""

import logging
from collections import defaultdict
from typing import Dict, List, Any
from extractor import get_supabase_client

logger = logging.getLogger("compliance-graphrag-dedup")


def deduplicate_entities() -> dict:
    """
    Main deduplication routine:
    1. Fetch all entities.
    2. Group by (name_lower, type_lower).
    3. For each group with >1 row, merge into a single canonical entity.
    4. Rewire relationships + entity_sources to canonical ID.
    5. Delete duplicate rows.
    Returns a summary dict.
    """
    supabase = get_supabase_client()

    # 1. Fetch all entities
    logger.info("Fetching all entities from database...")
    all_entities = []
    offset = 0
    page_size = 1000
    while True:
        res = (
            supabase.table("entities")
            .select("id, name, type, source_doc_id, source_span, source_location")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        if not res.data:
            break
        all_entities.extend(res.data)
        if len(res.data) < page_size:
            break
        offset += page_size

    logger.info(f"Total entities in database: {len(all_entities)}")

    # 2. Group by normalized (name, type)
    groups: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for ent in all_entities:
        key = (ent["name"].strip().lower(), ent["type"].strip().lower())
        groups[key].append(ent)

    # 3. Find groups with duplicates
    duplicate_groups = {k: v for k, v in groups.items() if len(v) > 1}
    logger.info(
        f"Found {len(duplicate_groups)} entity groups with duplicates "
        f"(out of {len(groups)} unique name+type keys)."
    )

    if not duplicate_groups:
        logger.info("No duplicates found. Database is clean.")
        return {
            "status": "success",
            "total_entities_before": len(all_entities),
            "total_entities_after": len(all_entities),
            "groups_merged": 0,
            "entities_removed": 0,
            "relationships_rewired": 0,
            "sources_migrated": 0,
        }

    total_removed = 0
    total_rewired = 0
    total_sources_migrated = 0

    for (name_key, type_key), entity_list in duplicate_groups.items():
        # Pick canonical: sort by id (deterministic) and take the first
        entity_list.sort(key=lambda e: e["id"])
        canonical = entity_list[0]
        duplicates = entity_list[1:]

        canonical_id = canonical["id"]
        duplicate_ids = [d["id"] for d in duplicates]

        logger.info(
            f"Merging '{canonical['name']}' ({canonical['type']}): "
            f"canonical={canonical_id}, duplicates={duplicate_ids}"
        )

        # Merge source_span and source_location into canonical
        all_spans = set()
        all_locations = []
        for ent in entity_list:
            if ent.get("source_span"):
                for s in ent["source_span"].split(", "):
                    all_spans.add(s.strip())
            if ent.get("source_location"):
                for loc in ent["source_location"].split(", "):
                    loc = loc.strip()
                    if loc and loc not in all_locations:
                        all_locations.append(loc)

        merged_span = ", ".join(sorted(all_spans))
        merged_location = ", ".join(all_locations)

        # Update canonical entity with merged spans/locations
        supabase.table("entities").update({
            "source_span": merged_span,
            "source_location": merged_location,
        }).eq("id", canonical_id).execute()

        # 4a. Rewire relationships: source_entity_id
        for dup_id in duplicate_ids:
            res = (
                supabase.table("relationships")
                .update({"source_entity_id": canonical_id})
                .eq("source_entity_id", dup_id)
                .execute()
            )
            rewired = len(res.data) if res.data else 0
            total_rewired += rewired

            # 4b. Rewire relationships: target_entity_id
            res = (
                supabase.table("relationships")
                .update({"target_entity_id": canonical_id})
                .eq("target_entity_id", dup_id)
                .execute()
            )
            rewired = len(res.data) if res.data else 0
            total_rewired += rewired

            # 4c. Migrate entity_sources rows
            res = (
                supabase.table("entity_sources")
                .update({"entity_id": canonical_id})
                .eq("entity_id", dup_id)
                .execute()
            )
            migrated = len(res.data) if res.data else 0
            total_sources_migrated += migrated

        # 5. Delete duplicate entity rows
        for dup_id in duplicate_ids:
            supabase.table("entities").delete().eq("id", dup_id).execute()
            total_removed += 1

    total_after = len(all_entities) - total_removed
    summary = {
        "status": "success",
        "total_entities_before": len(all_entities),
        "total_entities_after": total_after,
        "groups_merged": len(duplicate_groups),
        "entities_removed": total_removed,
        "relationships_rewired": total_rewired,
        "sources_migrated": total_sources_migrated,
    }

    logger.info(f"Deduplication complete: {summary}")
    return summary


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    result = deduplicate_entities()
    print("\n=== DEDUPLICATION RESULT ===")
    for k, v in result.items():
        print(f"  {k}: {v}")

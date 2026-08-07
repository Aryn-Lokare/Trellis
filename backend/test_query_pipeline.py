"""
Test harness for the GraphRAG retrieval and query pipeline.
Seeds compliance test data with vector embeddings, runs 4 distinct test scenarios,
validates output and citation constraints, and prints the full node state transitions
for a relational query.
"""

import os
import sys
import json
import time
import logging
import uuid
from dotenv import load_dotenv
from extractor import get_supabase_client, generate_embeddings_batch
from query_pipeline import build_query_graph

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test-query-pipeline")


def run_query_test_suite():
    load_dotenv()

    try:
        supabase = get_supabase_client()
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {str(e)}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("STARTING GRAPHRAG RETRIEVAL & QUERY PIPELINE TEST HARNESS")
    print("=" * 80 + "\n")

    # 1. Seed compliance test documents
    doc_ids = []
    for doc_type, filename, text in [
        ("pdf", "acme_audit_report.pdf", "ACME Corp database server DB-PROD-01 is physically located in Frankfurt. The server was audited by Sarah Jenkins."),
        ("audio", "wayne_compliance_call.wav", "Wayne Enterprises executive board discussed compliance audits. Wayne Enterprises violates the GDPR data residency requirements."),
        ("table", "vendor_compliance_status.csv", "Vendor Wayne Enterprises employs Lead Auditor Sarah Jenkins. Sarah Jenkins is auditing vendor Wayne Enterprises."),
    ]:
        res = supabase.table("documents").insert({
            "filename": filename,
            "doc_type": doc_type,
            "raw_text": text,
            "status": "processed",
        }).execute()
        doc_id = res.data[0]["id"]
        doc_ids.append(doc_id)
        logger.info(f"Seeded mock document: {filename} (ID: {doc_id})")

    # 2. Seed entities and generate embeddings for them
    entity_data = [
        # ACME Corp (PDF)
        {"name": "ACME Corp", "type": "organization", "source_doc_id": doc_ids[0],
         "source_span": "ACME Corp", "source_location": "Page 1"},
        # DB-PROD-01 (PDF)
        {"name": "DB-PROD-01", "type": "system", "source_doc_id": doc_ids[0],
         "source_span": "DB-PROD-01", "source_location": "Page 1"},
        # Frankfurt (PDF)
        {"name": "Frankfurt", "type": "location", "source_doc_id": doc_ids[0],
         "source_span": "Frankfurt", "source_location": "Page 1"},
        # Sarah Jenkins (PDF & Table)
        {"name": "Sarah Jenkins", "type": "person", "source_doc_id": doc_ids[0],
         "source_span": "Sarah Jenkins", "source_location": "Page 1"},

        # Wayne Enterprises (Audio & Table)
        {"name": "Wayne Enterprises", "type": "organization", "source_doc_id": doc_ids[1],
         "source_span": "Wayne Enterprises", "source_location": "01:15"},
        # GDPR (Audio)
        {"name": "GDPR", "type": "regulation", "source_doc_id": doc_ids[1],
         "source_span": "GDPR", "source_location": "08:40"},
    ]

    # Batch generate embeddings
    texts_to_embed = [f"{e['name']} ({e['type']})" for e in entity_data]
    logger.info("Generating 768-dim embeddings for test entities...")
    embeddings = generate_embeddings_batch(texts_to_embed)

    entity_ids = []
    for idx, ent in enumerate(entity_data):
        ent_id = str(uuid.uuid4())
        ent["id"] = ent_id
        ent["embedding"] = embeddings[idx] if idx < len(embeddings) else None
        entity_ids.append(ent_id)

    supabase.table("entities").insert(entity_data).execute()
    logger.info(f"Seeded {len(entity_data)} entities with embeddings in Supabase.")

    # Populate entity_sources
    sources = []
    for ent in entity_data:
        sources.append({
            "entity_id": ent["id"],
            "source_doc_id": ent["source_doc_id"],
            "source_span": ent["source_span"],
            "source_location": ent["source_location"],
        })
    supabase.table("entity_sources").insert(sources).execute()

    # 3. Seed relationships
    acme_id = entity_ids[0]
    db_id = entity_ids[1]
    frankfurt_id = entity_ids[2]
    sarah_id = entity_ids[3]
    wayne_id = entity_ids[4]
    gdpr_id = entity_ids[5]

    test_relationships = [
        # DB-PROD-01 located_at Frankfurt
        {"source_entity_id": db_id, "target_entity_id": frankfurt_id,
         "relation_type": "located_at", "source_doc_id": doc_ids[0],
         "source_span": "DB-PROD-01, located in Frankfurt", "source_location": "Page 1"},
        # Wayne Enterprises violates GDPR
        {"source_entity_id": wayne_id, "target_entity_id": gdpr_id,
         "relation_type": "violates", "source_doc_id": doc_ids[1],
         "source_span": "Wayne Enterprises violates the GDPR data residency requirements", "source_location": "08:40"},
        # Wayne Enterprises employs Sarah Jenkins
        {"source_entity_id": wayne_id, "target_entity_id": sarah_id,
         "relation_type": "employs", "source_doc_id": doc_ids[2],
         "source_span": "Vendor Wayne Enterprises employs Lead Auditor Sarah Jenkins", "source_location": "row 1"},
    ]

    for rel in test_relationships:
        rel["id"] = str(uuid.uuid4())

    supabase.table("relationships").insert(test_relationships).execute()
    logger.info(f"Seeded {len(test_relationships)} relationships in Supabase.")

    # 4. Build compiled query graph
    query_graph = build_query_graph()

    # ==================== TEST SCENARIOS ====================
    scenarios = [
        {
            "name": "Scenario 1: Relational / Graph Query",
            "question": "Which regulation does Wayne Enterprises violate?"
        },
        {
            "name": "Scenario 2: Fallback / No Match Query",
            "question": "What is the capital of France?"
        },
        {
            "name": "Scenario 3: 2-Hop Traversal Query",
            "question": "What regulation applies to the company that employs Sarah Jenkins?"
        },
        {
            "name": "Scenario 4: Over-claiming / Gap Detection Query",
            "question": "What is the exact dollar amount of the fine for Wayne Enterprises violating GDPR?"
        }
    ]

    all_test_outputs = []

    for idx, sc in enumerate(scenarios):
        print("\n" + "=" * 80)
        print(f"RUNNING: {sc['name']}")
        print(f"Question: \"{sc['question']}\"")
        print("=" * 80 + "\n")

        initial_state = {
            "question": sc["question"],
            "history": None,
            "standalone_question": None,
            "question_embedding": None,
            "seed_entity_ids": [],
            "subgraph": {"entities": [], "relationships": []},
            "synthesized_context": "",
            "raw_answer": "",
            "verified_answer": "",
            "citations": [],
            "status": "pending",
            "error_message": None
        }

        start_time = time.time()
        
        # If it's Scenario 1, print full node state transitions for trace reporting
        if idx == 0:
            print("--- PIPELINE STATE TRANSITION TRACE ---")
            state = initial_state
            
            # Node 1: embed_question
            from query_pipeline import embed_question_node, seed_search_node, graph_traversal_node, assemble_context_node, generate_answer_node, verify_citations_node
            state.update(embed_question_node(state))
            print(f"\n[embed_question_node] status: {state['status']}")
            print(f"Embedding dimensions: {len(state['question_embedding']) if state['question_embedding'] else 0}")
            
            # Node 2: seed_search
            state.update(seed_search_node(state))
            print(f"\n[seed_search_node] status: {state['status']}")
            print(f"Seed entity IDs matching query: {state['seed_entity_ids']}")
            
            # Node 3: graph_traversal
            state.update(graph_traversal_node(state))
            print(f"\n[graph_traversal_node] status: {state['status']}")
            print(f"Sub-graph traversed: {len(state['subgraph']['entities'])} entities, {len(state['subgraph']['relationships'])} relationships")
            
            # Node 4: assemble_context
            state.update(assemble_context_node(state))
            print(f"\n[assemble_context_node] status: {state['status']}")
            print(f"Synthesized Context:\n{state['synthesized_context']}")
            
            # Node 5: generate_answer
            state.update(generate_answer_node(state))
            print(f"\n[generate_answer_node] status: {state['status']}")
            print(f"Raw Answer:\n{state['raw_answer']}")
            
            # Node 6: verify_citations
            state.update(verify_citations_node(state))
            print(f"\n[verify_citations_node] status: {state['status']}")
            print(f"Verified Answer:\n{state['verified_answer']}")
            
            final_state = state
        else:
            final_state = query_graph.invoke(initial_state)

        latency = time.time() - start_time

        print(f"\nFinal Answer:\n{final_state.get('verified_answer')}")
        print("\nCitations:")
        for cit in final_state.get("citations", []):
            print(f"  - Location: {cit['location']} | Document: {cit['filename']} | Verified: {cit['verified']} | Excerpt: \"{cit['excerpt']}\"")
        print(f"\nStatus: {final_state.get('status')}")
        print(f"Latency: {latency:.4f} seconds")

        all_test_outputs.append({
            "scenario": sc["name"],
            "question": sc["question"],
            "answer": final_state.get("verified_answer"),
            "citations": final_state.get("citations"),
            "status": final_state.get("status"),
            "latency": latency
        })

    # ==================== CLEANUP ====================
    print("\n" + "=" * 80)
    print("CLEANING UP TEST DATA")
    print("=" * 80 + "\n")

    for doc_id in doc_ids:
        logger.info(f"Deleting test document {doc_id}...")
        supabase.table("documents").delete().eq("id", doc_id).execute()

    # Save results to JSON file
    results_path = os.path.join(os.path.dirname(__file__), "test_query_results.json")
    try:
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(all_test_outputs, f, indent=2)
        print("\n" + "=" * 80)
        print(f"SAVED QUERY PIPELINE OUTPUT TO:")
        print(f"  {results_path}")
        print("=" * 80 + "\n")
    except Exception as e:
        logger.error(f"Failed to save results: {str(e)}")


if __name__ == "__main__":
    run_query_test_suite()

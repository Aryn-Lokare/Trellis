import os
import json
import logging
from dotenv import load_dotenv
from query_pipeline import build_query_graph

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("check-query")

def run_diagnostic():
    load_dotenv()
    
    question = "Is the parking garage badge system update related to the security investigation?"
    print(f"Running diagnostic for question: \"{question}\"")
    
    query_graph = build_query_graph()
    
    initial_state = {
        "question": question,
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
    
    # Step-by-step state trace
    state = initial_state
    
    from query_pipeline import (
        embed_question_node,
        seed_search_node,
        graph_traversal_node,
        assemble_context_node,
        generate_answer_node,
        verify_citations_node
    )
    
    print("\n--- Running embed_question_node ---")
    state.update(embed_question_node(state))
    print(f"Status: {state['status']}")
    print(f"Embedding length: {len(state['question_embedding']) if state['question_embedding'] else 0}")
    
    print("\n--- Running seed_search_node ---")
    state.update(seed_search_node(state))
    print(f"Status: {state['status']}")
    print(f"Seed Entity IDs: {state['seed_entity_ids']}")
    
    # Fetch seed names from database to show what matched
    if state['seed_entity_ids']:
        from extractor import get_supabase_client
        supabase = get_supabase_client()
        res = supabase.table("entities").select("id, name, type").in_("id", state['seed_entity_ids']).execute()
        print("Matching Seed Entities:")
        for ent in (res.data or []):
            print(f"  - {ent['name']} ({ent['type']}) [ID: {ent['id']}]")
            
    print("\n--- Running graph_traversal_node ---")
    state.update(graph_traversal_node(state))
    print(f"Status: {state['status']}")
    print(f"Subgraph: {len(state['subgraph']['entities'])} entities, {len(state['subgraph']['relationships'])} relationships")
    
    print("\n--- Running assemble_context_node ---")
    state.update(assemble_context_node(state))
    print(f"Status: {state['status']}")
    print(f"Synthesized Context:\n{state['synthesized_context']}")
    
    print("\n--- Running generate_answer_node ---")
    state.update(generate_answer_node(state))
    print(f"Status: {state['status']}")
    print(f"Raw Answer:\n{state['raw_answer']}")
    
    print("\n--- Running verify_citations_node ---")
    state.update(verify_citations_node(state))
    print(f"Status: {state['status']}")
    print(f"Verified Answer:\n{state['verified_answer']}")
    print(f"Citations: {state['citations']}")

if __name__ == "__main__":
    run_diagnostic()

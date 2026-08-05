import re
import os
import logging
from typing import Dict, List, Any, TypedDict, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from langgraph.graph import StateGraph, END
from extractor import get_supabase_client

logger = logging.getLogger("compliance-graphrag-query")

# Define state schema
class QueryState(TypedDict):
    question: str
    question_embedding: Optional[List[float]]
    seed_entity_ids: List[str]
    subgraph: Dict[str, Any]  # {"entities": [...], "relationships": [...]}
    synthesized_context: str
    raw_answer: str
    verified_answer: str
    citations: List[Dict[str, Any]]
    status: str
    error_message: Optional[str]
    f1_score: Optional[float]
    retry_count: Optional[int]
    feedback_notes: Optional[str]


def embed_question_node(state: QueryState) -> Dict[str, Any]:
    """Generates the 768-dimensional embedding for the user's question."""
    logger.info(f"Generating embedding for question: {state['question']}")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"error_message": "Missing GEMINI_API_KEY", "status": "failed"}

    genai.configure(api_key=api_key)
    try:
        res = genai.embed_content(
            model="models/gemini-embedding-2",
            content=state["question"],
            task_type="retrieval_query",
            output_dimensionality=768
        )
        return {"question_embedding": res["embedding"], "status": "embedding_success"}
    except Exception as e:
        logger.error(f"Failed to embed question: {str(e)}")
        return {"error_message": str(e), "status": "failed"}


def seed_search_node(state: QueryState) -> Dict[str, Any]:
    """Runs vector similarity search against entities using pgvector RPC."""
    logger.info("Searching for seed entities in knowledge graph...")
    supabase = get_supabase_client()
    embedding = state.get("question_embedding")
    if not embedding:
        return {"status": "no_seed_match", "seed_entity_ids": []}

    try:
        # Match entities using custom pgvector similarity search RPC
        res = supabase.rpc("match_entities", {
            "query_embedding": embedding,
            "match_threshold": 0.35,
            "match_count": 10
        }).execute()

        matches = res.data or []
        if not matches:
            logger.info("No matching seed entities found above threshold.")
            return {"status": "no_seed_match", "seed_entity_ids": []}

        seed_ids = [m["id"] for m in matches]
        logger.info(f"Found {len(seed_ids)} seed entities: {[m['name'] for m in matches]}")
        return {"seed_entity_ids": seed_ids, "status": "seeds_found"}

    except Exception as e:
        logger.error(f"Error matching entities: {str(e)}")
        return {"status": "no_seed_match", "seed_entity_ids": []}


def graph_traversal_node(state: QueryState) -> Dict[str, Any]:
    """Traverses relationships outward from seed entities up to 2 hops using RPC recursive CTE."""
    seed_ids = state.get("seed_entity_ids")
    if not seed_ids or state.get("status") == "no_seed_match":
        return {"subgraph": {"entities": [], "relationships": []}}

    logger.info(f"Traversing graph from {len(seed_ids)} seed entities...")
    supabase = get_supabase_client()

    try:
        # Call recursive CTE function to traverse the graph (max 2 hops, max 50 entities)
        traverse_res = supabase.rpc("traverse_graph", {
            "seed_ids": seed_ids,
            "max_hops": 2,
            "max_entities": 50
        }).execute()

        entities = traverse_res.data or []
        entity_ids = [e["entity_id"] for e in entities]

        if not entity_ids:
            return {"subgraph": {"entities": [], "relationships": []}}

        # Fetch relationships connecting these entities
        rel_res = supabase.rpc("get_relationships_for_entities", {
            "entity_ids": entity_ids
        }).execute()

        relationships = rel_res.data or []
        logger.info(f"Traversed subgraph: {len(entities)} entities, {len(relationships)} relationships.")

        return {
            "subgraph": {
                "entities": entities,
                "relationships": relationships
            }
        }

    except Exception as e:
        logger.error(f"Error during graph traversal: {str(e)}")
        return {"subgraph": {"entities": [], "relationships": []}, "error_message": str(e)}


def assemble_context_node(state: QueryState) -> Dict[str, Any]:
    """Compiles the retrieved subgraph into structured markdown context."""
    subgraph = state.get("subgraph") or {"entities": [], "relationships": []}
    entities = subgraph.get("entities", [])
    relationships = subgraph.get("relationships", [])
    status = state.get("status")

    # Fallback path: If no vector seeds, run fuzzy name match / broad text search
    if status == "no_seed_match" or not entities:
        logger.info("Running fallback context assembly (fuzzy name match)...")
        supabase = get_supabase_client()
        question = state["question"]

        # Extract potential nouns from question for basic ILIKE matching
        keywords = [w.strip("?,.()\"'") for w in question.split() if len(w) > 4]
        fallback_entities = []

        for kw in keywords[:3]:  # search up to 3 keywords
            res = supabase.table("entities").select("id, name, type, source_doc_id, source_span, source_location").ilike("name", f"%{kw}%").limit(5).execute()
            if res.data:
                fallback_entities.extend(res.data)

        if fallback_entities:
            # Deduplicate by entity ID
            seen_ids = set()
            unique_fallback = []
            for e in fallback_entities:
                if e["id"] not in seen_ids:
                    seen_ids.add(e["id"])
                    # Align keys with traverse_graph return columns
                    unique_fallback.append({
                        "entity_id": e["id"],
                        "entity_name": e["name"],
                        "entity_type": e["type"],
                        "entity_source_doc_id": e["source_doc_id"],
                        "entity_source_span": e["source_span"],
                        "entity_source_location": e["source_location"]
                    })
            entities = unique_fallback
            # Get relationships connecting these entities
            rel_res = supabase.rpc("get_relationships_for_entities", {
                "entity_ids": list(seen_ids)
            }).execute()
            relationships = rel_res.data or []
            logger.info(f"Fallback matched {len(entities)} entities and {len(relationships)} relationships.")
        else:
            return {
                "synthesized_context": "Insufficient information in the knowledge graph to answer this question.",
                "status": "fallback_insufficient"
            }

    # Compile the context into text format
    context_lines = []
    context_lines.append("### Relevant Entities:")
    for ent in entities:
        name = ent.get("entity_name") or ent.get("name")
        ent_type = ent.get("entity_type") or ent.get("type")
        loc = ent.get("entity_source_location") or ent.get("source_location") or "Unknown"
        span = ent.get("entity_source_span") or ent.get("source_span") or ""
        context_lines.append(f"- {name} ({ent_type}) [source: {loc}] (Context: \"{span}\")")

    context_lines.append("\n### Relevant Relationships:")

    # Map entity IDs to names and hop distances
    ent_name_map = {}
    entity_hop_map = {}
    for ent in entities:
        eid = ent.get("entity_id") or ent.get("id")
        name = ent.get("entity_name") or ent.get("name")
        ent_name_map[eid] = name
        entity_hop_map[eid] = ent.get("hop_distance", 0)

    # Deduplicate relationships to avoid redundancy across multiple ingestion runs
    seen_rels = set()
    unique_relationships = []
    for rel in relationships:
        src_id = rel["source_entity_id"]
        tgt_id = rel["target_entity_id"]
        rtype = rel["relation_type"]
        span = rel.get("source_span", "").strip().lower()
        key = (src_id, tgt_id, rtype, span)
        if key not in seen_rels:
            seen_rels.add(key)
            unique_relationships.append(rel)

    # Sort relationships by the sum of endpoint hop distances to prioritize relationships closer to seeds
    def rel_sort_key(rel):
        src_hop = entity_hop_map.get(rel["source_entity_id"], 99)
        tgt_hop = entity_hop_map.get(rel["target_entity_id"], 99)
        return src_hop + tgt_hop

    sorted_rels = sorted(unique_relationships, key=rel_sort_key)
    trimmed_rels = sorted_rels[:60]

    for rel in trimmed_rels:
        src_name = ent_name_map.get(rel["source_entity_id"], "Unknown")
        tgt_name = ent_name_map.get(rel["target_entity_id"], "Unknown")
        rel_type = rel["relation_type"]
        loc = rel.get("source_location") or "Unknown"
        span = rel.get("source_span") or ""
        context_lines.append(f"- {src_name} --[{rel_type}]--> {tgt_name} [source: {loc}] (Context: \"{span}\")")

    return {"synthesized_context": "\n".join(context_lines)}


def generate_answer_node(state: QueryState) -> Dict[str, Any]:
    """Generates the grounded compliance answer from LLM using Groq."""
    logger.info("Generating answer from compliance context using Groq...")
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"error_message": "Missing GROQ_API_KEY", "status": "failed"}

    import groq
    client = groq.Groq(api_key=api_key)

    feedback = state.get("feedback_notes") or ""
    retry_prompt = ""
    if feedback:
        retry_prompt = (
            "\n\nCRITICAL CORRECTION (PREVIOUS ATTEMPT ISSUES):\n"
            "Your previous attempt had the following citation verification errors. You must correct these in your new response:\n"
            f"{feedback}\n"
            "Ensure that any citations you list strictly correspond to source locations from the Compliance Context. Do NOT use the unverified locations."
        )

    prompt = (
        "You are an expert enterprise compliance AI assistant.\n"
        "Your task is to answer the User Question using ONLY the provided Compliance Context below. "
        "Do NOT use outside knowledge, do NOT make assumptions, and do NOT extrapolate.\n\n"
        "RULES:\n"
        "1. Every factual claim or relation you state MUST include an inline citation marker "
        "at the end of the sentence matching the exact source location provided in the context, "
        "formatted exactly like '[source: Page X]', '[source: 01:15]', or '[source: row Y]'.\n"
        "2. If the context does not contain sufficient information to answer the question, state exactly: "
        "\"I don't have enough information to answer this based on the retrieved compliance graph.\"\n"
        "3. Do not formulate answers that aren't directly supported by the context.\n\n"
        f"Compliance Context:\n{state['synthesized_context']}\n\n"
        f"User Question: {state['question']}{retry_prompt}\n\n"
        "Answer:"
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        raw_answer = response.choices[0].message.content.strip()

        # Extract citation locations (e.g. from "[source: Page 1]" -> "Page 1")
        citations = re.findall(r"\[source:\s*([^\]]+)\]", raw_answer)
        citations_list = [{"location": loc.strip()} for loc in citations]

        return {"raw_answer": raw_answer, "citations": citations_list, "status": "raw_answer_generated"}
    except Exception as e:
        logger.error(f"Failed to generate answer via Groq: {str(e)}")
        return {"error_message": str(e), "status": "failed"}


def verify_citations_node(state: QueryState) -> Dict[str, Any]:
    """Checks that LLM inline citations correspond to locations in retrieved context."""
    logger.info("Verifying citations against retrieved context...")
    raw_answer = state.get("raw_answer") or ""
    subgraph = state.get("subgraph") or {"entities": [], "relationships": []}
    retry_count = state.get("retry_count") or 0

    if "I don't have enough information" in raw_answer:
        return {
            "verified_answer": raw_answer,
            "citations": [],
            "status": "success",
            "f1_score": 0.0,
            "retry_count": retry_count,
            "feedback_notes": "",
        }

    # Extract all valid locations from retrieved context
    valid_locations = set()
    for ent in subgraph.get("entities", []):
        loc = ent.get("entity_source_location") or ent.get("source_location")
        if loc:
            valid_locations.add(loc.strip().lower())
    for rel in subgraph.get("relationships", []):
        loc = rel.get("source_location")
        if loc:
            valid_locations.add(loc.strip().lower())

    # Regular expression to match "[source: ...]"
    pattern = r"\[source:\s*([^\]]+)\]"

    verified_answer = raw_answer
    resolved_citations = []
    unverified_citations = []

    # We find all citation markers and verify them
    matches = list(re.finditer(pattern, raw_answer))

    # Process matches in reverse order so replacements don't shift indices of subsequent matches
    offset_shift = 0
    status = "success"

    supabase = get_supabase_client()
    doc_cache = {}

    for match in matches:
        original_citation = match.group(0)  # "[source: Page 1]"
        location_text = match.group(1).strip()  # "Page 1"
        normalized_loc = location_text.lower()

        # Citation validation check
        is_verified = normalized_loc in valid_locations

        if not is_verified:
            logger.warning(f"Unverified citation found: '{location_text}'")
            unverified_citations.append(location_text)
            status = "citation_warning"
            replacement = f"{original_citation} [UNVERIFIED]"

            # Find index in verified_answer (accounting for previous replacements)
            start = match.start() + offset_shift
            end = match.end() + offset_shift

            verified_answer = verified_answer[:start] + replacement + verified_answer[end:]
            offset_shift += len("[UNVERIFIED]") + 1

        # Attempt to resolve source document info for the resolved list
        # Look up which document matches this location in the subgraph
        matching_doc_id = None
        matching_excerpt = ""

        for ent in subgraph.get("entities", []):
            ent_loc = ent.get("entity_source_location") or ent.get("source_location")
            if ent_loc and ent_loc.strip().lower() == normalized_loc:
                matching_doc_id = ent.get("entity_source_doc_id") or ent.get("source_doc_id")
                matching_excerpt = ent.get("entity_source_span") or ent.get("source_span") or ""
                break

        if not matching_doc_id:
            for rel in subgraph.get("relationships", []):
                rel_loc = rel.get("source_location")
                if rel_loc and rel_loc.strip().lower() == normalized_loc:
                    matching_doc_id = rel.get("source_doc_id")
                    matching_excerpt = rel.get("source_span") or ""
                    break

        filename = "Unknown"
        if matching_doc_id:
            # Simple caching to save queries
            if matching_doc_id not in doc_cache:
                doc_res = supabase.table("documents").select("filename").eq("id", matching_doc_id).execute()
                if doc_res.data:
                    doc_cache[matching_doc_id] = doc_res.data[0]["filename"]
            filename = doc_cache.get(matching_doc_id, "Unknown")

        resolved_citations.append({
            "location": location_text,
            "source_doc_id": matching_doc_id,
            "filename": filename,
            "excerpt": matching_excerpt,
            "verified": is_verified
        })

    # Compute F1 score based on citation verification
    total_citations = len(resolved_citations)
    verified_count = sum(1 for c in resolved_citations if c.get("verified") == True)
    if total_citations > 0:
        precision = verified_count / total_citations
        recall = verified_count / total_citations  # assuming all citations should be verified
        if precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0.0
    else:
        f1 = 0.0

    # Determine if retry is needed
    new_retry_count = retry_count
    feedback_notes = ""
    if len(unverified_citations) > 0 and retry_count < 2:
        new_retry_count += 1
        feedback_notes = (
            "The following citation locations you used were NOT found in the retrieved compliance graph and are invalid:\n"
            + "\n".join(f"- '{loc}'" for loc in unverified_citations)
        )
        status = "retry_needed"

    return {
        "verified_answer": verified_answer,
        "citations": resolved_citations,
        "status": status,
        "f1_score": f1,
        "retry_count": new_retry_count,
        "feedback_notes": feedback_notes,
    }


def route_after_search(state: QueryState) -> str:
    """Routes the graph: to fallback context if no seeds match, else to traversal."""
    if state.get("status") == "no_seed_match":
        return "fallback"
    return "traversal"


def route_after_verification(state: QueryState) -> str:
    """Routes the graph: back to generation if retry is needed, else to END."""
    if state.get("status") == "retry_needed":
        logger.info(f"Unverified citations detected. Routing back to generation. Attempt {state.get('retry_count') or 1}...")
        return "retry"
    return "end"


# Define LangGraph State Graph
def build_query_graph() -> StateGraph:
    workflow = StateGraph(QueryState)

    # Add Nodes
    workflow.add_node("embed_question", embed_question_node)
    workflow.add_node("seed_search", seed_search_node)
    workflow.add_node("graph_traversal", graph_traversal_node)
    workflow.add_node("assemble_context", assemble_context_node)
    workflow.add_node("generate_answer", generate_answer_node)
    workflow.add_node("verify_citations", verify_citations_node)

    # Set Entry Point
    workflow.set_entry_point("embed_question")

    # Define edges
    workflow.add_edge("embed_question", "seed_search")

    # Conditional routing after search
    workflow.add_conditional_edges(
        "seed_search",
        route_after_search,
        {
            "fallback": "assemble_context",
            "traversal": "graph_traversal"
        }
    )

    workflow.add_edge("graph_traversal", "assemble_context")
    workflow.add_edge("assemble_context", "generate_answer")
    workflow.add_edge("generate_answer", "verify_citations")
    
    # Conditional routing after verification (feedback loop)
    workflow.add_conditional_edges(
        "verify_citations",
        route_after_verification,
        {
            "retry": "generate_answer",
            "end": END
        }
    )

    return workflow.compile()
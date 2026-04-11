# import sys, os
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# import chromadb
# from sentence_transformers import SentenceTransformer
# from db import locksems_col, timetables_col, PERIOD_TIMES
# import warnings
# warnings.filterwarnings("ignore")

# # ── ChromaDB (must match path used in ingest.py) ─────────────────────────────
# chroma_client = chromadb.PersistentClient(path="./chroma_store")
# collection = chroma_client.get_or_create_collection(name="timetable_slots")

# # ── Same embedding model as ingest.py ────────────────────────────────────────
# embedder = SentenceTransformer("all-MiniLM-L6-v2")


# def get_active_codes() -> list:
#     """Returns all codes from timetables where currentSession is True."""
#     return timetables_col.distinct("code", {"currentSession": True})


# def build_mongo_filter(parsed: dict) -> dict:
#     """
#     Layer 1 — builds a MongoDB query from parsed fields.
#     Uses regex for partial/case-insensitive matching on text fields.
#     """
#     query = {}

#     # Always restrict to active session codes
#     active_codes = get_active_codes()
#     query["code"] = {"$in": active_codes}

#     if parsed.get("faculty"):
#         query["slotData.faculty"] = {
#             "$regex": parsed["faculty"], "$options": "i"
#         }
#     if parsed.get("day"):
#         query["day"] = {"$regex": parsed["day"], "$options": "i"}

#     if parsed.get("room"):
#         query["slotData.room"] = {
#             "$regex": parsed["room"], "$options": "i"
#         }
#     if parsed.get("subject"):
#         query["slotData.subject"] = {
#             "$regex": parsed["subject"], "$options": "i"
#         }

#     # sem can be matched directly or built from parts
#     if parsed.get("sem"):
#         query["sem"] = {"$regex": parsed["sem"], "$options": "i"}
#     else:
#         sem_parts = []
#         if parsed.get("course"):
#             sem_parts.append(parsed["course"])
#         if parsed.get("branch"):
#             sem_parts.append(parsed["branch"])
#         if parsed.get("semester_number"):
#             sem_parts.append(str(parsed["semester_number"]))
#         if sem_parts:
#             # Match all provided parts in the sem string
#             query["$and"] = [
#                 {"sem": {"$regex": part, "$options": "i"}}
#                 for part in sem_parts
#             ]

#     if parsed.get("slot"):
#         query["slot"] = parsed["slot"]

#     return query


# def retrieve(parsed: dict, user_query: str, top_k: int = 8) -> list:
#     """
#     Two-layer retrieval:
#       Layer 1 — MongoDB structured filter → candidate documents
#       Layer 2 — ChromaDB semantic search filtered to those candidate IDs

#     Returns a list of metadata dicts for the top matching slot entries.
#     """

#     # ── Layer 1: MongoDB filter ───────────────────────────────────────────────
#     mongo_filter = build_mongo_filter(parsed)
#     candidates = list(locksems_col.find(mongo_filter))

#     if not candidates:
#         # No structured matches — fall back to pure semantic search
#         print("⚠️  No MongoDB candidates found, falling back to full semantic search")
#         results = collection.query(
#             query_embeddings=[embedder.encode(user_query).tolist()],
#             n_results=top_k,
#         )
#         return _format_results(results)

#     # ── Layer 2: semantic search on candidate IDs only ────────────────────────
#     # Collect all slotData entry IDs that belong to these candidates
#     # We use the metadata field 'sem' + 'day' + 'slot' to build a where filter
#     # ChromaDB doesn't support $in on multiple fields easily, so we use day+sem
#     # as the narrowing filter since those are the most discriminating fields

#     where_conditions = []

#     days_seen  = set()
#     sems_seen  = set()
#     slots_seen = set()

#     for doc in candidates:
#         if doc.get("day"):
#             days_seen.add(doc["day"])
#         if doc.get("sem"):
#             sems_seen.add(doc["sem"])
#         if doc.get("slot"):
#             slots_seen.add(doc["slot"])

#     # Build ChromaDB where filter
#     # ChromaDB supports $and / $or with individual field conditions
#     chroma_filter = {}

#     filter_parts = []

#     if len(days_seen) == 1:
#         filter_parts.append({"day": {"$eq": list(days_seen)[0]}})
#     elif len(days_seen) > 1:
#         filter_parts.append({"day": {"$in": list(days_seen)}})

#     if len(sems_seen) == 1:
#         filter_parts.append({"sem": {"$eq": list(sems_seen)[0]}})
#     elif len(sems_seen) > 1:
#         filter_parts.append({"sem": {"$in": list(sems_seen)}})

#     if parsed.get("faculty"):
#         filter_parts.append({"faculty": {"$eq": parsed["faculty"]}})

#     if parsed.get("slot") or len(slots_seen) == 1:
#         slot_val = parsed.get("slot") or list(slots_seen)[0]
#         filter_parts.append({"slot": {"$eq": slot_val}})

#     if len(filter_parts) == 1:
#         chroma_filter = filter_parts[0]
#     elif len(filter_parts) > 1:
#         chroma_filter = {"$and": filter_parts}

#     try:
#         if chroma_filter:
#             results = collection.query(
#                 query_embeddings=[embedder.encode(user_query).tolist()],
#                 n_results=min(top_k, 10),
#                 where=chroma_filter,
#             )
#         else:
#             results = collection.query(
#                 query_embeddings=[embedder.encode(user_query).tolist()],
#                 n_results=min(top_k, 10),
#             )
#     except Exception as e:
#         print(f"⚠️  ChromaDB query failed: {e}, falling back to unfiltered search")
#         results = collection.query(
#             query_embeddings=[embedder.encode(user_query).tolist()],
#             n_results=top_k,
#         )

#     return _format_results(results)


# def _format_results(results: dict) -> list:
#     """Flattens ChromaDB query results into a clean list of dicts."""
#     output = []
#     if not results or not results.get("metadatas"):
#         return output

#     for meta, doc in zip(results["metadatas"][0], results["documents"][0]):
#         entry = dict(meta)
#         entry["text"] = doc
#         # Expand slot to human readable time
#         entry["time"] = PERIOD_TIMES.get(entry.get("slot", ""), entry.get("slot", ""))
#         output.append(entry)

#     return output


# # ── Quick test ────────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     from parser import parse_query
#     import time

#     tests = [
#         "When is Rawel Singh free on Monday?",
#         "Who teaches in room CY-102 on Wednesday?",
#     ]

#     for q in tests:
#         print(f"\nQ: {q}")
#         parsed = parse_query(q)
#         print(f"Parsed: {parsed}")
#         results = retrieve(parsed, q)
#         print(f"Results ({len(results)}):")
#         for r in results:
#             print(f"  → {r['faculty']} | {r['subject']} | {r['day']} {r['slot']} ({r['time']}) | {r['sem']}")
#         time.sleep(13)



import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import chromadb
from sentence_transformers import SentenceTransformer
from db import locksems_col, timetables_col, PERIOD_TIMES
import warnings
warnings.filterwarnings("ignore")

chroma_client = chromadb.PersistentClient(path="./chroma_store")
collection = chroma_client.get_or_create_collection(name="timetable_slots")
embedder = SentenceTransformer("all-MiniLM-L6-v2")


def get_active_codes() -> list:
    return timetables_col.distinct("code", {"currentSession": True})


def build_mongo_filter(parsed: dict) -> dict:
    query = {}
    active_codes = get_active_codes()
    query["code"] = {"$in": active_codes}

    if parsed.get("faculty"):
        query["slotData.faculty"] = {"$regex": parsed["faculty"], "$options": "i"}
    if parsed.get("day"):
        query["day"] = {"$regex": parsed["day"], "$options": "i"}
    if parsed.get("room"):
        query["slotData.room"] = {"$regex": parsed["room"], "$options": "i"}
    if parsed.get("subject"):
        query["slotData.subject"] = {"$regex": parsed["subject"], "$options": "i"}

    if parsed.get("sem"):
        query["sem"] = {"$regex": parsed["sem"], "$options": "i"}
    else:
        sem_parts = []
        if parsed.get("course"):
            sem_parts.append(parsed["course"])
        if parsed.get("branch"):
            sem_parts.append(parsed["branch"])
        if parsed.get("semester_number"):
            sem_parts.append(str(parsed["semester_number"]))
        if sem_parts:
            query["$and"] = [
                {"sem": {"$regex": part, "$options": "i"}}
                for part in sem_parts
            ]

    if parsed.get("slot"):
        query["slot"] = parsed["slot"]

    return query


def get_actual_faculty_name(faculty_query: str, candidates: list) -> str | None:
    """
    Resolves the exact faculty name as stored in ChromaDB
    by looking it up from MongoDB candidates (case-insensitive match).
    This fixes the issue where parser returns 'vipin kumar' but
    ChromaDB stores 'Vipin Kumar'.
    """
    faculty_lower = faculty_query.lower()
    for doc in candidates:
        for entry in doc.get("slotData", []):
            stored_name = entry.get("faculty", "")
            if stored_name and faculty_lower in stored_name.lower():
                return stored_name
    return faculty_query  # fallback to original if not found


def retrieve(parsed: dict, user_query: str, top_k: int = 10) -> list:
    mongo_filter = build_mongo_filter(parsed)
    candidates   = list(locksems_col.find(mongo_filter))
    query_embedding = embedder.encode(user_query).tolist()

    if not candidates:
        print("⚠️  No MongoDB candidates, falling back to full semantic search")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        return _format_results(results)

    # Build ChromaDB filter parts
    filter_parts = []

    # Resolve exact faculty name from candidates (fixes case mismatch)
    if parsed.get("faculty"):
        actual_name = get_actual_faculty_name(parsed["faculty"], candidates)
        if actual_name:
            filter_parts.append({"faculty": {"$eq": actual_name}})

    # Add day only if user specified it
    if parsed.get("day"):
        days = list(set(d["day"] for d in candidates if d.get("day")))
        if len(days) == 1:
            filter_parts.append({"day": {"$eq": days[0]}})
        elif len(days) > 1:
            filter_parts.append({"day": {"$in": days}})

    # Add slot only if user specified it
    if parsed.get("slot"):
        filter_parts.append({"slot": {"$eq": parsed["slot"]}})

    # Add sem filter only if user specified sem-related fields
    sem_specified = any([
        parsed.get("sem"), parsed.get("course"),
        parsed.get("branch"), parsed.get("semester_number")
    ])
    if sem_specified:
        sems = list(set(d["sem"] for d in candidates if d.get("sem")))
        if len(sems) == 1:
            filter_parts.append({"sem": {"$eq": sems[0]}})
        elif len(sems) > 1:
            filter_parts.append({"sem": {"$in": sems}})

    # Add room filter if specified
    if parsed.get("room"):
        filter_parts.append({"room": {"$eq": parsed["room"]}})

    # Build final chroma filter
    if len(filter_parts) == 0:
        chroma_filter = None
    elif len(filter_parts) == 1:
        chroma_filter = filter_parts[0]
    else:
        chroma_filter = {"$and": filter_parts}

    try:
        total = collection.count()
        n = min(top_k, total)
        if chroma_filter:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n,
                where=chroma_filter,
            )
        else:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n,
            )
    except Exception as e:
        print(f"⚠️  ChromaDB query failed: {e}, falling back to unfiltered")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

    return _format_results(results)


def _format_results(results: dict) -> list:
    output = []
    if not results or not results.get("metadatas"):
        return output
    for meta, doc in zip(results["metadatas"][0], results["documents"][0]):
        entry = dict(meta)
        entry["text"] = doc
        entry["time"] = PERIOD_TIMES.get(entry.get("slot", ""), entry.get("slot", ""))
        output.append(entry)
    return output


if __name__ == "__main__":
    from parser import parse_query

    tests = [
        "what subjects does Vipin Kumar teach?",
        "what does Vipin Kumar teach on Monday?",
        "what subject is taught in room SB-3 during period3 on Thursday?",
        "give me the timetable of vipin kumar",
    ]
    for q in tests:
        print(f"\nQ: {q}")
        parsed  = parse_query(q)
        results = retrieve(parsed, q)
        print(f"Results ({len(results)}):")
        for r in results:
            print(f"  → {r['faculty']} | {r['subject']} | {r['day']} {r['slot']} ({r['time']}) | {r['sem']}")
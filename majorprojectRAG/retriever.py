
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import chromadb
import warnings
warnings.filterwarnings("ignore")

from db import locksems_col, timetables_col, PERIOD_TIMES
from embedder import embed

chroma_client = chromadb.PersistentClient(path="./chroma_store")
collection = chroma_client.get_or_create_collection(name="timetable_slots")


def get_active_codes():
    return timetables_col.distinct("code", {"currentSession": True})


def build_mongo_filter(parsed):
    query = {}
    active_codes = get_active_codes()
    query["code"] = {"$in": active_codes}

    if parsed.get("faculty"):
        query["slotData.faculty"] = {"$regex": parsed["faculty"], "$options": "i"}
    if parsed.get("day"):
        query["day"] = {"$regex": parsed["day"], "$options": "i"}
    if parsed.get("room"):
        query["slotData.room"] = {"$regex": parsed["room"], "$options": "i"}
    # if parsed.get("room"):
    #     # Resolve actual room name from MongoDB candidates (fixes case mismatch)
    #     room_query = parsed["room"]
    #     for doc in candidates:
    #         for entry in doc.get("slotData", []):
    #             stored_room = entry.get("room", "")
    #             if stored_room and room_query.lower() == stored_room.lower():
    #                room_query = stored_room  # use exact stored case
    #                break
    #     filter_parts.append({"room": {"$eq": room_query}})
        
        
    if parsed.get("subject"):
        query["slotData.subject"] = {"$regex": parsed["subject"], "$options": "i"}

    if parsed.get("sem"):
        query["sem"] = {"$regex": parsed["sem"], "$options": "i"}
    else:
        sem_parts = []
        if parsed.get("course"):          sem_parts.append(parsed["course"])
        if parsed.get("branch"):          sem_parts.append(parsed["branch"])
        if parsed.get("semester_number"): sem_parts.append(str(parsed["semester_number"]))
        if sem_parts:
            query["$and"] = [{"sem": {"$regex": p, "$options": "i"}} for p in sem_parts]

    if parsed.get("slot"):
        query["slot"] = parsed["slot"]

    return query


def get_actual_faculty_name(faculty_query, candidates):
    faculty_lower = faculty_query.lower()
    for doc in candidates:
        for entry in doc.get("slotData", []):
            stored = entry.get("faculty", "")
            if stored and faculty_lower in stored.lower():
                return stored
    return faculty_query


def mongo_candidates_to_results(candidates, faculty_filter=None, room_filter=None):
    """
    Converts raw MongoDB locksem documents directly into result dicts.
    Used for faculty_schedule intent to guarantee ALL slots are returned
    without being limited by ChromaDB's top_k.
    """
    output = []
    for doc in candidates:
        day  = doc.get("day", "")
        slot = doc.get("slot", "")
        sem  = doc.get("sem", "")
        code = doc.get("code", "")

        for entry in doc.get("slotData", []):
            faculty = entry.get("faculty", "").strip()
            subject = entry.get("subject", "").strip()
            room    = entry.get("room", "").strip()

            if not faculty and not subject:
                continue

            # Apply faculty filter if specified
            if faculty_filter and faculty_filter.lower() not in faculty.lower():
                continue

            # Apply room filter if specified
            if room_filter and room_filter.lower() not in room.lower():
                continue

            output.append({
                "faculty": faculty,
                "subject": subject,
                "room":    room,
                "day":     day,
                "slot":    slot,
                "sem":     sem,
                "code":    code,
                "time":    PERIOD_TIMES.get(slot, slot),
                "text":    f"{faculty} teaches {subject} in {room} on {day} {slot} for {sem}",
            })

    return output


def retrieve(parsed, user_query, top_k=20):
    intent = parsed.get("intent", "general")
    mongo_filter = build_mongo_filter(parsed)
    candidates   = list(locksems_col.find(mongo_filter))
    
    if parsed.get("room") and candidates:
        room_query = parsed["room"]
        for doc in candidates:
            for entry in doc.get("slotData", []):
                stored_room = entry.get("room", "")
                if stored_room and room_query.lower() == stored_room.lower():
                    parsed["room"] = stored_room  # overwrite with exact stored casing
                    break

    if not candidates:
        # No MongoDB matches — fall back to full ChromaDB semantic search
        print("⚠️  No MongoDB candidates, falling back to full semantic search")
        query_embedding = embed(user_query)
        results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
        return _format_results(results)

    # ── For faculty_schedule and free_slots: use MongoDB directly ────────────
    # This guarantees ALL slots are returned, not limited by ChromaDB top_k
    # if intent in ("faculty_schedule", "free_slots", "sem_timetable"):
    if intent in ("faculty_schedule", "free_slots", "room_free_slots", "sem_timetable"):
        return mongo_candidates_to_results(
            candidates,
            faculty_filter=parsed.get("faculty"),
            room_filter=parsed.get("room"),
        )

    # ── For all other intents: use ChromaDB semantic search ──────────────────
    query_embedding = embed(user_query)

    filter_parts = []

    if parsed.get("faculty"):
        actual_name = get_actual_faculty_name(parsed["faculty"], candidates)
        if actual_name:
            filter_parts.append({"faculty": {"$eq": actual_name}})

    if parsed.get("day"):
        days = list(set(d["day"] for d in candidates if d.get("day")))
        if len(days) == 1:
            filter_parts.append({"day": {"$eq": days[0]}})
        elif len(days) > 1:
            filter_parts.append({"day": {"$in": days}})

    if parsed.get("slot"):
        filter_parts.append({"slot": {"$eq": parsed["slot"]}})

    sem_specified = any([parsed.get("sem"), parsed.get("course"),
                         parsed.get("branch"), parsed.get("semester_number")])
    if sem_specified:
        sems = list(set(d["sem"] for d in candidates if d.get("sem")))
        if len(sems) == 1:
            filter_parts.append({"sem": {"$eq": sems[0]}})
        elif len(sems) > 1:
            filter_parts.append({"sem": {"$in": sems}})

    if parsed.get("room"):
        filter_parts.append({"room": {"$eq": parsed["room"]}})

    if len(filter_parts) == 0:
        chroma_filter = None
    elif len(filter_parts) == 1:
        chroma_filter = filter_parts[0]
    else:
        chroma_filter = {"$and": filter_parts}

    try:
        n = min(top_k, collection.count())
        if chroma_filter:
            results = collection.query(query_embeddings=[query_embedding], n_results=n, where=chroma_filter)
        else:
            results = collection.query(query_embeddings=[query_embedding], n_results=n)
    except Exception as e:
        print(f"⚠️  ChromaDB query failed: {e}, falling back to MongoDB direct")
        return mongo_candidates_to_results(candidates, faculty_filter=parsed.get("faculty"))

    return _format_results(results)


def _format_results(results):
    output = []
    if not results or not results.get("metadatas"):
        return output
    for meta, doc in zip(results["metadatas"][0], results["documents"][0]):
        entry = dict(meta)
        entry["text"] = doc
        entry["time"] = PERIOD_TIMES.get(entry.get("slot", ""), entry.get("slot", ""))
        output.append(entry)
    return output

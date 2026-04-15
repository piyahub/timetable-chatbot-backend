
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import hashlib
import warnings
warnings.filterwarnings("ignore")

import chromadb
from dotenv import load_dotenv
from db import timetables_col, locksems_col, PERIOD_TIMES, parse_sem
from embedder import embed

load_dotenv()

chroma_client = chromadb.PersistentClient(path="./chroma_store")
collection = chroma_client.get_or_create_collection(name="timetable_slots")


def make_doc_id(faculty: str, day: str, slot: str, sem: str, subject: str) -> str:
    key = f"{faculty}|{day}|{slot}|{sem}|{subject}".lower()
    return hashlib.md5(key.encode()).hexdigest()


def build_sentence(faculty, subject, room, day, slot, sem) -> str:
    time_range = PERIOD_TIMES.get(slot, slot)
    parsed = parse_sem(sem)
    return (
        f"{faculty} teaches {subject} in room {room} "
        f"on {day} during {slot} ({time_range}) "
        f"for {sem} "
        f"(course: {parsed['course']}, branch: {parsed['branch']}, semester: {parsed['semester']})."
    )


def get_active_locksems():
    active_codes = timetables_col.distinct("code", {"currentSession": True})
    if not active_codes:
        print("⚠️  No active sessions found.")
        return []
    print(f"✅  Found {len(active_codes)} active session code(s).")
    docs = list(locksems_col.find({"code": {"$in": active_codes}}))
    print(f"✅  Found {len(docs)} locksems documents.")
    return docs


def upsert_slot_entry(faculty, subject, room, day, slot, sem, code):
    doc_id   = make_doc_id(faculty, day, slot, sem, subject)
    sentence = build_sentence(faculty, subject, room, day, slot, sem)
    embedding = embed(sentence)

    collection.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[sentence],
        metadatas=[{
            "faculty": faculty, "subject": subject,
            "room": room,      "day": day,
            "slot": slot,      "sem": sem,
            "code": code,
        }]
    )
    return doc_id


def run_full_ingestion():
    docs = get_active_locksems()
    if not docs:
        return

    total = 0
    skipped = 0

    for doc in docs:
        day  = doc.get("day", "")
        slot = doc.get("slot", "")
        sem  = doc.get("sem", "")
        code = doc.get("code", "")

        for entry in doc.get("slotData", []):
            faculty = entry.get("faculty", "").strip()
            subject = entry.get("subject", "").strip()
            room    = entry.get("room", "").strip()

            if not faculty or not subject:
                skipped += 1
                continue

            upsert_slot_entry(faculty, subject, room, day, slot, sem, code)
            total += 1

    print(f"✅  Ingestion complete. {total} upserted, {skipped} skipped.")


if __name__ == "__main__":
    run_full_ingestion()

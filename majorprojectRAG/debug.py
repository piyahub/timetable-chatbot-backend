# import sys, os
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# import warnings
# warnings.filterwarnings("ignore")

# from db import locksems_col, timetables_col

# # Step 1 — check active codes exist
# active_codes = timetables_col.distinct("code", {"currentSession": True})
# print(f"Active codes: {len(active_codes)}")

# # Step 2 — search for vipin kumar with regex (case insensitive)
# docs = list(locksems_col.find({
#     "code": {"$in": active_codes},
#     "slotData.faculty": {"$regex": "vipin", "$options": "i"}
# }))
# print(f"\nDocs found for 'vipin': {len(docs)}")
# for d in docs[:3]:
#     print(f"  day={d['day']} slot={d['slot']} sem={d['sem']}")
#     for e in d.get("slotData", []):
#         if "vipin" in e.get("faculty","").lower():
#             print(f"    → faculty='{e['faculty']}' subject='{e['subject']}' room='{e['room']}'")

# # Step 3 — check what the retriever actually builds as filter
# from retriever import build_mongo_filter, retrieve
# parsed = {
#     "intent": "faculty_schedule",
#     "faculty": "vipin kumar",
#     "room": None, "day": None, "subject": None,
#     "sem": None, "course": None, "branch": None,
#     "semester_number": None, "slot": None
# }
# mongo_filter = build_mongo_filter(parsed)
# print(f"\nMongo filter built: {mongo_filter}")

# candidates = list(locksems_col.find(mongo_filter))
# print(f"Candidates from filter: {len(candidates)}")

# # Step 4 — full retrieve
# results = retrieve(parsed, "what subjects are taught by vipin kumar?")
# print(f"\nRetrieval results ({len(results)}):")
# for r in results:
#     print(f"  → {r['faculty']} | {r['subject']} | {r['day']} {r['slot']} | {r['sem']}")


import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import warnings
warnings.filterwarnings("ignore")

from parser import parse_query
from retriever import retrieve, build_mongo_filter
from db import locksems_col, timetables_col

tests = [
    "what subjects does harimurugan teach?",
    "what does Vipin Kumar teach on Monday?",
    "what subject is taught in room SB-3 during period3 on Thursday?",
    "give me the timetable of vipin kumar",
]

active_codes = timetables_col.distinct("code", {"currentSession": True})

for q in tests:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    parsed = parse_query(q)
    print(f"Parsed: {parsed}")

    mongo_filter = build_mongo_filter(parsed)
    candidates = list(locksems_col.find(mongo_filter))
    print(f"MongoDB candidates: {len(candidates)}")
    for c in candidates[:2]:
        print(f"  day={c['day']} slot={c['slot']} sem={c['sem']}")
        for e in c.get('slotData', []):
            print(f"    → {e.get('faculty')} | {e.get('subject')} | {e.get('room')}")

    results = retrieve(parsed, q)
    print(f"Retrieval results: {len(results)}")
    for r in results:
        print(f"  → {r['faculty']} | {r['subject']} | {r['day']} {r['slot']} ({r['time']}) | {r['sem']}")

# from pymongo import MongoClient

# # 🔹 Connect to MongoDB
# client = MongoClient("mongodb+srv://hari:nitjeed@cluster0.caetrkr.mongodb.net/")
# db = client["test"]

# # 🔹 Step 1: Fetch ALL codes where currentSession = True
# timetables = db.timetables.find({"currentSession": True})

# codes = set()

# for t in timetables:
#     if "code" in t:
#         codes.add(t["code"])

# if not codes:
#     print("❌ No codes found in active timetables")
#     exit()

# print("✅ Active Codes:")
# print(codes)

# # 🔹 Step 2: Fetch ONE document from locksems using these codes
# doc = db.locksems.find_one({
#     "code": {"$in": list(codes)}
# })

# if not doc:
#     print("❌ No matching document found in locksems")
# else:
#     print("\n✅ Matching locksems document structure:\n")
#     for key, value in doc.items():
#         print(f"{key}: {value}")
        
        
# from pymongo import MongoClient
# from collections import defaultdict

# # =============================
# # CONFIG
# # =============================
# MONGO_URI = "mongodb+srv://hari:nitjeed@cluster0.caetrkr.mongodb.net/"
# DB_NAME = "test"

# # =============================
# # CONNECT
# # =============================
# client = MongoClient(MONGO_URI)
# db = client[DB_NAME]

# # =============================
# # GET CURRENT SESSION CODES
# # =============================
# def get_current_session_codes():
#     docs = list(db["timetables"].find({"currentSession": True}))
#     codes = list(set([doc.get("code") for doc in docs if doc.get("code")]))

#     print("\n✅ Current Session Codes:", codes)
#     return codes


# # =============================
# # FETCH ALL FACULTY DATA
# # =============================
# def get_all_faculty_data(faculty_name):
#     codes = get_current_session_codes()

#     if not codes:
#         print("❌ No active session found")
#         return

#     docs = list(db["locksems"].find({"code": {"$in": codes}}))

#     faculty_data = []
#     subjects = set()

#     for doc in docs:
#         for entry in doc.get("slotData", []):
#             if faculty_name.lower() in entry.get("faculty", "").lower():

#                 record = {
#                     "faculty": entry.get("faculty"),
#                     "subject": entry.get("subject"),
#                     "room": entry.get("room"),
#                     "day": doc.get("day"),
#                     "slot": doc.get("slot"),
#                     "sem": doc.get("sem"),
#                 }

#                 faculty_data.append(record)

#                 if entry.get("subject"):
#                     subjects.add(entry.get("subject"))

#     # =============================
#     # OUTPUT
#     # =============================
#     print("\n==============================")
#     print(f"📊 TOTAL RECORDS: {len(faculty_data)}")
#     print(f"📚 UNIQUE SUBJECTS: {len(subjects)}")
#     print("==============================\n")

#     if not faculty_data:
#         print("❌ No data found for this faculty")
#         return

#     # 🔹 Print subjects list
#     print("🎯 SUBJECTS TAUGHT:")
#     print(", ".join(subjects))
#     print("\n------------------------------\n")

#     # 🔹 Print all records
#     print("📋 FULL TIMETABLE DATA:\n")

#     for i, r in enumerate(faculty_data, 1):
#         print(f"{i}. {r['subject']} | {r['day']} | {r['slot']} | Room: {r['room']} | Sem: {r['sem']}")

#     print("\n==============================\n")


# # =============================
# # RUN
# # =============================
# if __name__ == "__main__":
#     name = input("Enter faculty name: ")
#     get_all_faculty_data(name)

# view_faculty_docs.py

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# -------------------------------
# 1. Load ENV
# -------------------------------
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env")

# -------------------------------
# 2. Connect DB
# -------------------------------
client = MongoClient(MONGO_URI)
db = client["test"]

locksems = db["locksems"]
timetables = db["timetables"]

# -------------------------------
# 3. Get active timetable codes
# -------------------------------
active_codes = [
    d["code"]
    for d in timetables.find(
        {"currentSession": True},
        {"code": 1}
    )
]

print(f"\n[INFO] Active timetable codes: {active_codes}\n")

# -------------------------------
# 4. Input faculty name
# -------------------------------
faculty_query = input("Enter faculty name: ").lower().strip()

# -------------------------------
# 5. Fetch & filter docs
# -------------------------------
results = []

for doc in locksems.find({"code": {"$in": active_codes}}):

    day = doc.get("day", "")
    slot = doc.get("slot", "")
    sem = doc.get("sem", "")

    for entry in doc.get("slotData", []):
        faculty = entry.get("faculty", "")
        subject = entry.get("subject", "")
        room = entry.get("room", "")

        # ✅ PARTIAL MATCH (important)
        if faculty_query in faculty.lower():
            results.append({
                "faculty": faculty,
                "subject": subject,
                "room": room,
                "day": day,
                "slot": slot,
                "sem": sem
            })

# -------------------------------
# 6. Print results
# -------------------------------
if not results:
    print("\n❌ No records found.\n")
else:
    print(f"\n✅ Found {len(results)} records:\n")

    for r in results:
        print(f"{r['faculty']} teaches {r['subject']}")
        print(f"  Day: {r['day']} | Slot: {r['slot']} | Room: {r['room']} | Sem: {r['sem']}")
        print("-" * 60)



# from pymongo import MongoClient

# # Replace with your MongoDB URI
# MONGO_URI = "mongodb+srv://hari:nitjeed@cluster0.caetrkr.mongodb.net/"

# def get_one_document():
#     try:
#         # Connect to MongoDB
#         client = MongoClient(MONGO_URI)

#         # Access database and collection
#         db = client["test"]
#         collection = db["timetables"]

#         # Fetch one document
#         doc = collection.find_one()

#         if doc:
#             print("Document found:")
#             print(doc)
#         else:
#             print("No document found.")

#     except Exception as e:
#         print("Error:", e)

#     finally:
#         client.close()

# if __name__ == "__main__":
#     get_one_document()
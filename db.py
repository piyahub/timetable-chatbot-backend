import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()  # loads .env file from the same directory

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env file")

client = MongoClient(MONGO_URI)
db = client["test"]

timetables_col = db["timetables"]
locksems_col   = db["locksems"]

# Period number → actual time range
PERIOD_TIMES = {
    "period1": "8:30 - 9:25",
    "period2": "9:30 - 10:25",
    "period3": "10:30 - 11:25",
    "period4": "11:30 - 12:25",
    "lunch":   "12:30 - 1:25",
    "period5": "1:30 - 2:25",
    "period6": "2:30 - 3:25",
    "period7": "3:30 - 4:25",
    "period8": "4:30 - 5:25",
}

# All teaching periods (lunch excluded from free slot calculation)
TEACHING_PERIODS = [p for p in PERIOD_TIMES if p != "lunch"]


def parse_sem(sem: str) -> dict:
    """
    Breaks a sem string like 'B.Sc-CHE-4' into its components.
    Returns course, branch, semester number, and the raw original string.
    """
    parts = sem.split("-")
    return {
        "course":   parts[0] if len(parts) > 0 else "",
        "branch":   parts[1] if len(parts) > 1 else "",
        "semester": parts[2] if len(parts) > 2 else "",
        "raw":      sem,
    }
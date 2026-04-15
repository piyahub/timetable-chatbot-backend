import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.utils.normalize import normalize

def filter_by_course(data, course_input):
    input_norm = normalize(course_input)
    filtered = []
    for doc in data:
        sem = doc.get("sem", "")
        if normalize(sem) == input_norm:
            if not doc.get("slotData"):
                continue
            filtered.append(doc)
    return filtered

def filter_by_faculty(data, faculty_name):
    faculty_name = faculty_name.lower()
    filtered = []

    for doc in data:
        for entry in doc.get("slotData", []):
            faculty = entry.get("faculty", "").lower()
            if faculty_name in faculty:
                new_doc = doc.copy()
                new_doc["slotData"] = [entry]
                filtered.append(new_doc)

    return filtered
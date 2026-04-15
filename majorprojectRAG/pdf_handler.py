# import sys, os
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# from db import locksems_col, timetables_col
# from app.services.faculty import filter_by_faculty
# from app.services.course  import filter_by_course
# from app.services.pdf     import build_timetable, generate_pdf


# def get_active_locksems() -> list:
#     """Fetch all locksem docs from active sessions."""
#     active_codes = timetables_col.distinct("code", {"currentSession": True})
#     return list(locksems_col.find({"code": {"$in": active_codes}}))


# def generate_faculty_timetable_pdf(faculty_name: str) -> str | None:
#     """
#     Generates a timetable PDF for a given faculty.
#     Returns the file path or None if no data found.
#     """
#     all_docs = get_active_locksems()
#     filtered = filter_by_faculty(all_docs, faculty_name)

#     if not filtered:
#         return None

#     timetable = build_timetable(filtered)
#     filepath  = generate_pdf(timetable, faculty_name)
#     return filepath


# def generate_course_timetable_pdf(course_name: str) -> str | None:
#     """
#     Generates a timetable PDF for a given course/sem like B.Sc-CHE-4.
#     Returns the file path or None if no data found.
#     """
#     all_docs = get_active_locksems()
#     filtered = filter_by_course(all_docs, course_name)

#     if not filtered:
#         return None

#     timetable = build_timetable(filtered)
#     filepath  = generate_pdf(timetable, course_name)
#     return filepath

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import locksems_col, timetables_col
from app.services.faculty import filter_by_faculty
from app.services.course  import filter_by_course
from app.services.pdf     import build_timetable, generate_pdf_bytes


def get_active_locksems() -> list:
    active_codes = timetables_col.distinct("code", {"currentSession": True})
    return list(locksems_col.find({"code": {"$in": active_codes}}))


def generate_faculty_timetable_pdf(faculty_name: str) -> bytes | None:
    all_docs = get_active_locksems()
    filtered = filter_by_faculty(all_docs, faculty_name)
    if not filtered:
        return None
    timetable = build_timetable(filtered)
    return generate_pdf_bytes(timetable, faculty_name)


def generate_course_timetable_pdf(course_name: str) -> bytes | None:
    all_docs = get_active_locksems()
    filtered = filter_by_course(all_docs, course_name)
    if not filtered:
        return None
    timetable = build_timetable(filtered)
    return generate_pdf_bytes(timetable, course_name)

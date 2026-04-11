import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import locksems_col, timetables_col, TEACHING_PERIODS, PERIOD_TIMES


def get_free_slots(faculty_name: str, day: str) -> dict:
    """
    Computes which periods a faculty member is free on a given day.
    Done entirely in Python — never delegated to the LLM.

    Returns a dict with:
        - busy_slots: list of periods the faculty is teaching
        - free_slots: list of periods the faculty is free
        - busy_details: list of dicts with subject/room/sem for each busy slot
        - day: the day queried
        - faculty: the faculty name queried
    """
    active_codes = timetables_col.distinct("code", {"currentSession": True})

    # Find all locksem docs for this faculty on this day
    docs = list(locksems_col.find({
        "code":           {"$in": active_codes},
        "day":            {"$regex": day, "$options": "i"},
        "slotData.faculty": {"$regex": faculty_name, "$options": "i"},
    }))

    busy_slots   = []
    busy_details = []

    for doc in docs:
        slot = doc.get("slot", "")
        sem  = doc.get("sem", "")

        for entry in doc.get("slotData", []):
            if faculty_name.lower() in entry.get("faculty", "").lower():
                busy_slots.append(slot)
                busy_details.append({
                    "slot":    slot,
                    "time":    PERIOD_TIMES.get(slot, slot),
                    "subject": entry.get("subject", ""),
                    "room":    entry.get("room", ""),
                    "sem":     sem,
                })

    free_slots = [
        {"slot": p, "time": PERIOD_TIMES[p]}
        for p in TEACHING_PERIODS
        if p not in busy_slots
    ]

    return {
        "faculty":      faculty_name,
        "day":          day,
        "busy_slots":   busy_slots,
        "busy_details": busy_details,
        "free_slots":   free_slots,
    }


def format_free_slots_context(result: dict) -> str:
    """
    Converts the free slots result into a plain text string
    that gets passed to the LLM as context.
    The LLM just formats this into a natural sentence — no computation.
    """
    lines = [f"Free slot analysis for {result['faculty']} on {result['day']}:"]

    if result["free_slots"]:
        free_str = ", ".join(
            f"{f['slot']} ({f['time']})" for f in result["free_slots"]
        )
        lines.append(f"FREE periods: {free_str}")
    else:
        lines.append("FREE periods: none — fully booked")

    if result["busy_details"]:
        lines.append("BUSY periods:")
        for b in result["busy_details"]:
            lines.append(
                f"  - {b['slot']} ({b['time']}): teaching {b['subject']} "
                f"in {b['room']} for {b['sem']}"
            )

    return "\n".join(lines)


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = get_free_slots("Rawel Singh", "Monday")
    print(format_free_slots_context(result))
    print()
    print("Raw result:", result)
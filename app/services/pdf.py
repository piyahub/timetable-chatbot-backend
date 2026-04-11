# import os
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import landscape, A4
# from reportlab.lib.styles import getSampleStyleSheet


# def build_timetable(data):
#     slots = [
#         "period1", "period2", "period3", "period4",
#         "period5", "period6", "period7", "period8"
#     ]
#     days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
#     timetable = {day: [""] * 9 for day in days}

#     for doc in data:
#         day  = doc.get("day")
#         slot = doc.get("slot")

#         if day not in timetable or slot not in slots:
#             continue

#         db_index = slots.index(slot)
#         index    = db_index if db_index < 4 else db_index + 1

#         slot_data = doc.get("slotData", [])
#         if not slot_data:
#             continue

#         entry   = slot_data[0]
#         subject = entry.get("subject", "")
#         room    = entry.get("room", "")
#         timetable[day][index] = f"{subject}\n({room})"

#     for day in timetable:
#         timetable[day][4] = "LUNCH"

#     return timetable


# def generate_pdf(timetable, title_name) -> str:
#     """Generates a PDF and returns its file path."""
#     filename = os.path.join("/tmp", f"timetable_{title_name.replace(' ', '_')}.pdf")

#     doc = SimpleDocTemplate(
#         filename,
#         pagesize=landscape(A4),
#         rightMargin=20, leftMargin=20,
#         topMargin=20,   bottomMargin=20
#     )

#     styles   = getSampleStyleSheet()
#     elements = []

#     elements.append(Paragraph(
#         "<b>Dr B R Ambedkar National Institute of Technology, Jalandhar</b>",
#         styles["Title"]
#     ))
#     elements.append(Spacer(1, 10))
#     elements.append(Paragraph(
#         f"<b>Timetable: {title_name.title()}</b>",
#         styles["Heading2"]
#     ))
#     elements.append(Spacer(1, 20))

#     header = [
#         "Day/Period",
#         "P1\n8:30-9:25",  "P2\n9:30-10:25",
#         "P3\n10:30-11:25","P4\n11:30-12:25",
#         "LUNCH",
#         "P5\n1:30-2:25",  "P6\n2:30-3:25",
#         "P7\n3:30-4:25",  "P8\n4:30-5:25"
#     ]

#     table_data = [header]
#     for day, periods in timetable.items():
#         table_data.append([day] + periods)

#     table = Table(table_data, colWidths=[80] + [85] * 9)
#     table.setStyle(TableStyle([
#         ("GRID",       (0, 0), (-1, -1), 1, colors.black),
#         ("BACKGROUND", (0, 0), (-1,  0), colors.lightgrey),
#         ("BACKGROUND", (5, 1), (5,  -1), colors.lightgrey),
#         ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
#         ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
#         ("FONTSIZE",   (0, 0), (-1, -1), 8),
#         ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
#         ("TOPPADDING",    (0, 0), (-1, -1), 6),
#     ]))

#     elements.append(table)
#     doc.build(elements)
#     return filename

import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet


def build_timetable(data):
    slots = [
        "period1", "period2", "period3", "period4",
        "period5", "period6", "period7", "period8"
    ]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    timetable = {day: [""] * 9 for day in days}

    for doc in data:
        day  = doc.get("day")
        slot = doc.get("slot")

        if day not in timetable or slot not in slots:
            continue

        db_index = slots.index(slot)
        index    = db_index if db_index < 4 else db_index + 1

        slot_data = doc.get("slotData", [])
        if not slot_data:
            continue

        entry   = slot_data[0]
        subject = entry.get("subject", "")
        room    = entry.get("room", "")
        timetable[day][index] = f"{subject}\n({room})"

    for day in timetable:
        timetable[day][4] = "LUNCH"

    return timetable


def generate_pdf_bytes(timetable, title_name) -> bytes:
    """
    Generates a PDF entirely in memory and returns raw bytes.
    Nothing is written to disk — the bytes are streamed directly to the user.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=20, leftMargin=20,
        topMargin=20,   bottomMargin=20
    )

    styles   = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(
        "<b>Dr B R Ambedkar National Institute of Technology, Jalandhar</b>",
        styles["Title"]
    ))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        f"<b>Timetable: {title_name.title()}</b>",
        styles["Heading2"]
    ))
    elements.append(Spacer(1, 20))

    header = [
        "Day/Period",
        "P1\n8:30-9:25",   "P2\n9:30-10:25",
        "P3\n10:30-11:25", "P4\n11:30-12:25",
        "LUNCH",
        "P5\n1:30-2:25",   "P6\n2:30-3:25",
        "P7\n3:30-4:25",   "P8\n4:30-5:25"
    ]

    table_data = [header]
    for day, periods in timetable.items():
        table_data.append([day] + periods)

    table = Table(table_data, colWidths=[80] + [85] * 9)
    table.setStyle(TableStyle([
        ("GRID",          (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND",    (0, 0), (-1,  0), colors.lightgrey),
        ("BACKGROUND",    (5, 1), (5,  -1), colors.lightgrey),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return buffer.read()
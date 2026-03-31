from __future__ import annotations

from calendar import month_name
from collections import defaultdict
from datetime import date

from sqlalchemy import extract

from app.models import Attendance, Exam, Marks, Subject

STRONG_THRESHOLD = 75.0
WEAK_THRESHOLD = 50.0
PASS_THRESHOLD = 40.0


def _normalize_score(marks_obtained, max_marks):
    if not max_marks:
        return 0.0
    return round((marks_obtained / max_marks) * 100, 2)


def _classify_exam_type(exam_name):
    name = (exam_name or "").lower()
    if "final" in name or "semester" in name or "end sem" in name:
        return "Final"
    if "term" in name or "unit" in name or "internal" in name:
        return "Term Test"
    if "practical" in name or "lab" in name:
        return "Practical"
    return "Assessment"


def _calculate_trend(percentages):
    if len(percentages) < 2:
        return "steady"

    delta = percentages[-1] - percentages[0]
    if delta >= 5:
        return "increasing"
    if delta <= -5:
        return "decreasing"
    return "steady"


def _status_for_score(score):
    if score >= STRONG_THRESHOLD:
        return "Strong"
    if score < WEAK_THRESHOLD:
        return "Weak"
    return "Stable"


def build_student_profile(student):
    return {
        "name": f"{student.first_name} {student.last_name}",
        "email": student.email,
        "branch": student.branch_ref.name if student.branch_ref else "N/A",
        "division": student.division_ref.name if student.division_ref else "N/A",
        "prn": student.prn or "N/A",
        "roll_no": student.roll_no or "N/A",
    }


def get_released_marks(student):
    return (
        Marks.query.join(Exam)
        .join(Subject)
        .filter(
            Marks.student_id == student.id,
            Exam.results_released.is_(True),
        )
        .order_by(Exam.date.asc(), Subject.name.asc(), Marks.id.asc())
        .all()
    )


def _serialize_mark(mark):
    percentage = _normalize_score(mark.marks_obtained, mark.exam.max_marks)
    return {
        "subject_name": mark.exam.subject.name,
        "subject_id": mark.exam.subject.id,
        "semester": mark.exam.subject.semester,
        "exam_name": mark.exam.name,
        "exam_type": _classify_exam_type(mark.exam.name),
        "date": mark.exam.date.strftime("%Y-%m-%d"),
        "date_label": mark.exam.date.strftime("%d %b %Y"),
        "date_sort": mark.exam.date.isoformat(),
        "marks_obtained": round(mark.marks_obtained, 2),
        "max_marks": round(mark.exam.max_marks, 2),
        "percentage": percentage,
    }


def build_subject_performance(student):
    marks = get_released_marks(student)
    grouped_marks = defaultdict(list)

    for mark in marks:
        serialized = _serialize_mark(mark)
        grouped_marks[serialized["subject_name"]].append(serialized)

    subject_rows = []
    for subject_name, entries in grouped_marks.items():
        entries.sort(key=lambda item: (item["date_sort"], item["exam_name"]))
        percentages = [entry["percentage"] for entry in entries]
        average_marks = round(sum(entry["marks_obtained"] for entry in entries) / len(entries), 2)
        average_percentage = round(sum(percentages) / len(percentages), 2)
        trend = _calculate_trend(percentages)
        latest_entry = entries[-1]

        subject_rows.append(
            {
                "subject_name": subject_name,
                "subject_id": latest_entry["subject_id"],
                "semester": latest_entry["semester"],
                "average_marks": average_marks,
                "average_percentage": average_percentage,
                "average_max_marks": round(sum(entry["max_marks"] for entry in entries) / len(entries), 2),
                "latest_marks": latest_entry["marks_obtained"],
                "latest_percentage": latest_entry["percentage"],
                "latest_exam": latest_entry["exam_name"],
                "trend": trend,
                "status": _status_for_score(average_percentage),
                "exam_count": len(entries),
            }
        )

    subject_rows.sort(key=lambda item: item["average_percentage"], reverse=True)

    strong_subjects = [row["subject_name"] for row in subject_rows if row["status"] == "Strong"]
    weak_subjects = [row["subject_name"] for row in subject_rows if row["status"] == "Weak"]

    summary = {
        "overall_average_percentage": round(
            sum(row["average_percentage"] for row in subject_rows) / len(subject_rows), 2
        )
        if subject_rows
        else 0.0,
        "strong_count": len(strong_subjects),
        "weak_count": len(weak_subjects),
        "stable_count": len([row for row in subject_rows if row["status"] == "Stable"]),
        "strong_subjects": strong_subjects,
        "weak_subjects": weak_subjects,
    }

    return {"subjects": subject_rows, "summary": summary}


def build_performance_history(student):
    history = [_serialize_mark(mark) for mark in get_released_marks(student)]
    history.sort(key=lambda item: (item["date_sort"], item["subject_name"], item["exam_name"]))

    cleaned_history = []
    for entry in history:
        cleaned_entry = dict(entry)
        cleaned_entry.pop("date_sort", None)
        cleaned_history.append(cleaned_entry)

    return {"history": cleaned_history}


def generate_performance_insights(subject_rows):
    insights = []

    improving_subjects = [row["subject_name"] for row in subject_rows if row["trend"] == "increasing"]
    declining_subjects = [row["subject_name"] for row in subject_rows if row["trend"] == "decreasing"]
    strong_subjects = [row["subject_name"] for row in subject_rows if row["status"] == "Strong"]
    weak_subjects = [row["subject_name"] for row in subject_rows if row["status"] == "Weak"]

    for subject in improving_subjects[:2]:
        insights.append(f"Your performance is improving in {subject}.")

    for subject in strong_subjects[:2]:
        message = f"{subject} is one of your strongest subjects right now."
        if message not in insights:
            insights.append(message)

    for subject in weak_subjects[:2]:
        insights.append(f"You need to focus more on {subject}.")

    for subject in declining_subjects[:2]:
        message = f"Recent scores are slipping in {subject}; revise before the next assessment."
        if message not in insights:
            insights.append(message)

    if not insights:
        insights.append("Complete more released assessments to unlock meaningful performance insights.")

    return insights[:4]


def get_month_options():
    return [{"value": month, "label": month_name[month]} for month in range(1, 13)]


def get_available_semesters(student):
    released_semesters = sorted({mark.exam.subject.semester for mark in get_released_marks(student)})
    if released_semesters:
        return released_semesters

    branch_subjects = Subject.query.filter_by(branch_id=student.branch_id).all()
    return sorted({subject.semester for subject in branch_subjects})


def resolve_selected_semester(student, requested_semester=None):
    available_semesters = get_available_semesters(student)
    if requested_semester:
        try:
            semester = int(requested_semester)
        except (TypeError, ValueError):
            semester = None
        else:
            if semester in available_semesters or not available_semesters:
                return semester, available_semesters

    return (available_semesters[-1] if available_semesters else None), available_semesters


def build_monthly_attendance_report(student, month=None, year=None):
    today = date.today()
    selected_month = int(month or today.month)
    selected_year = int(year or today.year)

    records = (
        Attendance.query.join(Subject)
        .filter(
            Attendance.student_id == student.id,
            extract("month", Attendance.date) == selected_month,
            extract("year", Attendance.date) == selected_year,
        )
        .order_by(Subject.name.asc(), Attendance.date.asc())
        .all()
    )

    grouped_attendance = defaultdict(list)
    for record in records:
        grouped_attendance[record.subject.name].append(record)

    subject_rows = []
    total_lectures = 0
    attended_lectures = 0

    for subject_name, entries in grouped_attendance.items():
        total = len(entries)
        attended = sum(1 for entry in entries if entry.status)
        percentage = round((attended / total) * 100, 2) if total else 0.0

        total_lectures += total
        attended_lectures += attended
        subject_rows.append(
            {
                "subject_name": subject_name,
                "total_lectures": total,
                "attended_lectures": attended,
                "percentage": percentage,
                "status": "On Track" if percentage >= 75 else "At Risk",
            }
        )

    subject_rows.sort(key=lambda item: item["subject_name"])

    overall_percentage = round((attended_lectures / total_lectures) * 100, 2) if total_lectures else 0.0

    return {
        "student": build_student_profile(student),
        "month": selected_month,
        "year": selected_year,
        "month_label": f"{month_name[selected_month]} {selected_year}",
        "subjects": subject_rows,
        "total_lectures": total_lectures,
        "attended_lectures": attended_lectures,
        "overall_percentage": overall_percentage,
    }


def build_semester_result_report(student, semester=None):
    selected_semester, available_semesters = resolve_selected_semester(student, semester)
    marks = [mark for mark in get_released_marks(student) if selected_semester is None or mark.exam.subject.semester == selected_semester]

    grouped_marks = defaultdict(list)
    for mark in marks:
        grouped_marks[mark.exam.subject.name].append(mark)

    subject_rows = []
    total_marks = 0.0
    total_max_marks = 0.0

    for subject_name, entries in grouped_marks.items():
        obtained = round(sum(entry.marks_obtained for entry in entries), 2)
        max_marks = round(sum(entry.exam.max_marks for entry in entries), 2)
        percentage = _normalize_score(obtained, max_marks) if max_marks else 0.0
        status = "Pass" if percentage >= PASS_THRESHOLD else "Fail"

        total_marks += obtained
        total_max_marks += max_marks
        subject_rows.append(
            {
                "subject_name": subject_name,
                "exam_count": len(entries),
                "marks_obtained": obtained,
                "max_marks": max_marks,
                "percentage": percentage,
                "status": status,
            }
        )

    subject_rows.sort(key=lambda item: item["subject_name"])
    overall_percentage = _normalize_score(total_marks, total_max_marks) if total_max_marks else 0.0
    overall_status = "Pass" if subject_rows and all(row["status"] == "Pass" for row in subject_rows) else "Review"

    return {
        "student": build_student_profile(student),
        "semester": selected_semester,
        "available_semesters": available_semesters,
        "subjects": subject_rows,
        "total_marks": round(total_marks, 2),
        "max_marks": round(total_max_marks, 2),
        "overall_percentage": overall_percentage,
        "overall_status": overall_status,
    }


def build_remarks_report(student, semester=None, month=None, year=None):
    attendance_report = build_monthly_attendance_report(student, month=month, year=year)
    result_report = build_semester_result_report(student, semester=semester)
    performance_report = build_subject_performance(student)

    attendance_percentage = attendance_report["overall_percentage"]
    result_percentage = result_report["overall_percentage"]
    weak_subjects = result_report["subjects"]
    weak_subjects = [row["subject_name"] for row in weak_subjects if row["status"] == "Fail"]
    improving_subjects = [row["subject_name"] for row in performance_report["subjects"] if row["trend"] == "increasing"]

    remarks = []
    if result_report["subjects"]:
        if result_percentage >= STRONG_THRESHOLD:
            remarks.append("Good performance")
        elif result_percentage >= WEAK_THRESHOLD:
            remarks.append("Steady performance with room to improve")
        else:
            remarks.append("Needs improvement")
    else:
        remarks.append("Result data is not available yet")

    if attendance_report["subjects"]:
        if attendance_percentage < 75:
            remarks.append("Low attendance risk")
        elif attendance_percentage >= 85:
            remarks.append("Excellent attendance discipline")
    else:
        remarks.append("Attendance data is limited for the selected month")

    for subject in weak_subjects[:2]:
        remarks.append(f"You need to focus more on {subject}.")

    for subject in improving_subjects[:2]:
        remarks.append(f"Your performance is improving in {subject}.")

    deduplicated_remarks = []
    for remark in remarks:
        if remark not in deduplicated_remarks:
            deduplicated_remarks.append(remark)

    if attendance_percentage < 65 or (result_report["subjects"] and result_percentage < WEAK_THRESHOLD):
        risk_level = "High"
    elif attendance_percentage < 75 or (result_report["subjects"] and result_percentage < STRONG_THRESHOLD):
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    return {
        "student": build_student_profile(student),
        "semester": result_report["semester"],
        "available_semesters": result_report["available_semesters"],
        "month": attendance_report["month"],
        "year": attendance_report["year"],
        "month_label": attendance_report["month_label"],
        "attendance_percentage": attendance_percentage,
        "result_percentage": result_percentage,
        "risk_level": risk_level,
        "remarks": deduplicated_remarks,
        "weak_subjects": weak_subjects,
        "improving_subjects": improving_subjects,
    }


def build_reports_overview(student):
    attendance_report = build_monthly_attendance_report(student)
    result_report = build_semester_result_report(student)
    remarks_report = build_remarks_report(student)

    return {
        "attendance_percentage": attendance_report["overall_percentage"],
        "result_percentage": result_report["overall_percentage"],
        "remark_count": len(remarks_report["remarks"]),
        "semester": result_report["semester"],
        "month_label": attendance_report["month_label"],
    }

from datetime import datetime

from sqlalchemy import case

from app.models import LeaveRequest


LEAVE_STATUSES = {'Pending', 'Approved', 'Rejected'}


def parse_leave_date(value):
    return datetime.strptime(value, '%Y-%m-%d').date()


def get_leave_status_tone(status):
    return (
        'badge-verified'
        if status == 'Approved'
        else 'badge-risk'
        if status == 'Rejected'
        else 'badge-pending'
    )


def get_student_guardians(student):
    return sorted(
        [guardian for guardian in student.local_guardians if guardian.role == 'faculty' and guardian.verified],
        key=lambda guardian: (guardian.first_name, guardian.last_name),
    )


def get_guardian_students(faculty):
    return sorted(
        [student for student in faculty.local_guardian_students if student.role == 'student' and student.verified],
        key=lambda student: (
            student.roll_no if student.roll_no is not None else 10**9,
            student.first_name,
            student.last_name,
        ),
    )


def can_student_apply_leave(student):
    return bool(get_student_guardians(student))


def can_guardian_review_leave_request(faculty, leave_request):
    guardian_student_ids = {student.id for student in get_guardian_students(faculty)}
    return leave_request.student_id in guardian_student_ids


def get_student_leave_requests(student):
    return (
        LeaveRequest.query.filter_by(student_id=student.id)
        .order_by(LeaveRequest.created_at.desc(), LeaveRequest.start_date.desc())
        .all()
    )


def get_guardian_leave_requests(faculty):
    student_ids = [student.id for student in get_guardian_students(faculty)]
    if not student_ids:
        return []

    pending_first = case((LeaveRequest.status == 'Pending', 0), else_=1)
    return (
        LeaveRequest.query.filter(LeaveRequest.student_id.in_(student_ids))
        .order_by(pending_first.asc(), LeaveRequest.start_date.asc(), LeaveRequest.created_at.desc())
        .all()
    )


def build_leave_card(leave_request):
    start_date = leave_request.start_date
    end_date = leave_request.end_date
    return {
        'request': leave_request,
        'status_tone': get_leave_status_tone(leave_request.status),
        'day_count': (end_date - start_date).days + 1,
    }


def build_student_leave_cards(student):
    guardians = get_student_guardians(student)
    guardian_names = [f"{guardian.first_name} {guardian.last_name}" for guardian in guardians]
    cards = []
    for leave_request in get_student_leave_requests(student):
        card = build_leave_card(leave_request)
        card['guardian_names'] = guardian_names
        cards.append(card)
    return cards


def build_guardian_leave_cards(faculty):
    cards = []
    for leave_request in get_guardian_leave_requests(faculty):
        card = build_leave_card(leave_request)
        card['student_name'] = f"{leave_request.student.first_name} {leave_request.student.last_name}"
        cards.append(card)
    return cards

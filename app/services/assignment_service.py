from __future__ import annotations

import os
from datetime import datetime
from uuid import uuid4

from flask import current_app
from werkzeug.utils import secure_filename

from app.models import Assignment, Submission, Subject, User


def parse_due_date(value):
    return datetime.strptime(value, '%Y-%m-%dT%H:%M')


def can_faculty_manage_subject(faculty, subject):
    return subject in faculty.subjects_taught


def can_faculty_manage_assignment(faculty, assignment):
    return assignment.subject in faculty.subjects_taught or assignment.faculty_id == faculty.id


def can_student_access_assignment(student, assignment):
    if student.subjects_enrolled:
        return assignment.subject in student.subjects_enrolled
    return assignment.subject.branch_id == student.branch_id


def get_faculty_subjects(faculty):
    return sorted(faculty.subjects_taught, key=lambda subject: (subject.semester, subject.name))


def get_faculty_assignments(faculty):
    return (
        Assignment.query.join(Subject)
        .filter(Assignment.faculty_id == faculty.id)
        .order_by(Assignment.due_date.asc(), Assignment.created_at.desc())
        .all()
    )


def get_student_assignments(student):
    query = Assignment.query.join(Subject)
    if student.subjects_enrolled:
        subject_ids = [subject.id for subject in student.subjects_enrolled]
        query = query.filter(Assignment.subject_id.in_(subject_ids))
    else:
        query = query.filter(Subject.branch_id == student.branch_id)
    return query.order_by(Assignment.due_date.asc(), Assignment.created_at.desc()).all()


def get_submission_for_student(assignment_id, student_id):
    return Submission.query.filter_by(assignment_id=assignment_id, student_id=student_id).first()


def allowed_assignment_file(filename):
    if not filename or '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in current_app.config['ASSIGNMENT_ALLOWED_EXTENSIONS']


def save_submission_file(file_storage):
    if not file_storage or not file_storage.filename:
        return None, None

    if not allowed_assignment_file(file_storage.filename):
        raise ValueError('Unsupported file format.')

    filename = secure_filename(file_storage.filename)
    unique_name = f"{uuid4().hex}_{filename}"
    absolute_path = os.path.join(current_app.config['ASSIGNMENT_UPLOAD_FOLDER'], unique_name)
    file_storage.save(absolute_path)
    return f"uploads/assignments/{unique_name}", filename


def get_assignment_status(assignment, submission=None, now=None):
    reference_time = now or datetime.utcnow()
    if submission:
        if assignment.due_date and submission.submitted_at > assignment.due_date:
            return 'Late'
        return 'Submitted'

    if assignment.due_date and reference_time > assignment.due_date:
        return 'Late'
    return 'Pending'


def build_assignment_card(assignment, submission=None):
    status = get_assignment_status(assignment, submission=submission)
    return {
        'assignment': assignment,
        'submission': submission,
        'status': status,
        'status_tone': (
            'badge-verified'
            if status == 'Submitted'
            else 'badge-risk'
            if status == 'Late'
            else 'badge-pending'
        ),
        'is_submitted': submission is not None,
        'is_late': status == 'Late',
    }


def build_student_assignment_cards(student):
    assignments = get_student_assignments(student)
    submissions = {
        submission.assignment_id: submission
        for submission in Submission.query.filter_by(student_id=student.id).all()
    }
    return [build_assignment_card(assignment, submissions.get(assignment.id)) for assignment in assignments]


def build_faculty_assignment_cards(faculty):
    cards = []
    for assignment in get_faculty_assignments(faculty):
        submissions = assignment.submissions
        submitted_count = len(submissions)
        late_count = sum(1 for submission in submissions if get_assignment_status(assignment, submission) == 'Late')
        graded_count = sum(1 for submission in submissions if submission.grade is not None)
        cards.append(
            {
                'assignment': assignment,
                'submitted_count': submitted_count,
                'late_count': late_count,
                'graded_count': graded_count,
            }
        )
    return cards


def build_assignment_submission_rows(assignment):
    enrolled_students = [student for student in assignment.subject.enrolled_students if student.verified]
    if enrolled_students:
        students = sorted(
            enrolled_students,
            key=lambda student: (
                student.roll_no if student.roll_no is not None else 10**9,
                student.first_name,
                student.last_name,
            ),
        )
    else:
        students = (
            User.query.filter_by(role='student', branch_id=assignment.subject.branch_id, verified=True)
            .order_by(User.roll_no.asc(), User.first_name.asc(), User.last_name.asc())
            .all()
        )
    submissions = {submission.student_id: submission for submission in assignment.submissions}

    rows = []
    for student in students:
        submission = submissions.get(student.id)
        rows.append(
            {
                'student': student,
                'submission': submission,
                'status': get_assignment_status(assignment, submission=submission),
                'status_tone': (
                    'badge-verified'
                    if submission and get_assignment_status(assignment, submission=submission) == 'Submitted'
                    else 'badge-risk'
                    if get_assignment_status(assignment, submission=submission) == 'Late'
                    else 'badge-pending'
                ),
            }
        )
    return rows

from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_low_attendance_risk(student):
    """
    Dummy AI logic: Check attendance percentage. If < 75%, return True.
    """
    total_classes = len(student.attendances)
    if total_classes == 0:
        return False
    present_classes = sum(1 for a in student.attendances if a.status)
    percentage = (present_classes / total_classes) * 100
    return percentage < 75.0

def predict_student_performance(student):
    """
    Dummy AI logic: Predict final score based on average of past marks.
    """
    if not student.marks:
        return "No Data"
    total_marks = sum(m.marks_obtained for m in student.marks)
    max_marks = sum(m.exam.max_marks for m in student.marks)
    if max_marks == 0:
        return "No Data"
    percentage = (total_marks / max_marks) * 100
    if percentage > 85:
        return "Excellent"
    elif percentage > 70:
        return "Good"
    elif percentage > 50:
        return "Average"
    else:
        return "At Risk"

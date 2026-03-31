import calendar
from datetime import date, datetime

from app import db
from app.models import CalendarEvent, Exam, Subject


SEMESTER_OPTIONS = list(range(1, 9))
CALENDAR_EVENT_TYPES = {'exam', 'holiday', 'event'}
CALENDAR_TYPE_META = {
    'exam': {'label': 'Exam', 'tone': 'badge-risk', 'css': 'calendar-chip--exam'},
    'holiday': {'label': 'Holiday', 'tone': 'badge-verified', 'css': 'calendar-chip--holiday'},
    'event': {'label': 'Event', 'tone': 'badge-info', 'css': 'calendar-chip--event'},
}


def parse_calendar_date(value):
    return datetime.strptime(value, '%Y-%m-%d').date()


def resolve_calendar_period(month=None, year=None, today=None):
    reference = today or date.today()
    resolved_month = month if month and 1 <= month <= 12 else reference.month
    resolved_year = year if year and 2000 <= year <= 2100 else reference.year
    return resolved_year, resolved_month


def shift_calendar_period(year, month, offset):
    new_month = month + offset
    new_year = year
    while new_month < 1:
        new_month += 12
        new_year -= 1
    while new_month > 12:
        new_month -= 12
        new_year += 1
    return new_year, new_month


def validate_semester(value):
    semester = int(value)
    if semester not in SEMESTER_OPTIONS:
        raise ValueError('Semester must be between 1 and 8.')
    return semester


def get_default_calendar_semester(branch_id, user=None):
    if user is not None:
        subject_semesters = []
        if getattr(user, 'subjects_enrolled', None):
            subject_semesters = sorted({subject.semester for subject in user.subjects_enrolled if subject.semester})
        elif getattr(user, 'subjects_taught', None):
            subject_semesters = sorted({subject.semester for subject in user.subjects_taught if subject.semester})
        if subject_semesters:
            return subject_semesters[-1]

    branch_subject_semesters = sorted(
        {subject.semester for subject in Subject.query.filter_by(branch_id=branch_id).all() if subject.semester}
    )
    if branch_subject_semesters:
        return branch_subject_semesters[-1]

    branch_event_semesters = sorted(
        {event.semester for event in CalendarEvent.query.filter_by(branch_id=branch_id).all() if event.semester}
    )
    if branch_event_semesters:
        return branch_event_semesters[-1]

    return SEMESTER_OPTIONS[0]


def resolve_calendar_semester(branch_id, requested_semester=None, user=None):
    if requested_semester:
        try:
            return validate_semester(requested_semester)
        except (TypeError, ValueError):
            pass
    return get_default_calendar_semester(branch_id, user=user)


def create_branch_exam(branch_id, name, subject_id, exam_date, max_marks):
    subject = db.session.get(Subject, subject_id)
    if subject is None:
        raise ValueError('Please choose a valid subject.')
    if subject.branch_id != branch_id:
        raise ValueError('You can only add exams for subjects in your branch.')

    exam = Exam(
        name=name,
        subject_id=subject.id,
        date=exam_date,
        max_marks=float(max_marks),
    )
    db.session.add(exam)
    db.session.commit()
    return exam


def get_branch_calendar_event(branch_id, event_id):
    calendar_event = db.session.get(CalendarEvent, event_id)
    if calendar_event is None or calendar_event.branch_id != branch_id:
        raise ValueError('Calendar event not found for this branch.')
    return calendar_event


def create_calendar_event(branch_id, semester, title, event_date, event_type, description=None):
    normalized_type = (event_type or '').strip().lower()
    if normalized_type not in CALENDAR_EVENT_TYPES:
        raise ValueError('Please choose a valid calendar type.')

    calendar_event = CalendarEvent(
        title=title.strip(),
        date=event_date,
        type=normalized_type,
        branch_id=branch_id,
        semester=validate_semester(semester),
        description=(description or '').strip() or None,
    )
    db.session.add(calendar_event)
    db.session.commit()
    return calendar_event


def update_calendar_event(branch_id, event_id, semester, title, event_date, event_type, description=None):
    calendar_event = get_branch_calendar_event(branch_id, event_id)
    normalized_type = (event_type or '').strip().lower()
    if normalized_type not in CALENDAR_EVENT_TYPES:
        raise ValueError('Please choose a valid calendar type.')

    calendar_event.title = title.strip()
    calendar_event.date = event_date
    calendar_event.type = normalized_type
    calendar_event.semester = validate_semester(semester)
    calendar_event.description = (description or '').strip() or None
    db.session.commit()
    return calendar_event


def delete_calendar_event(branch_id, event_id):
    calendar_event = get_branch_calendar_event(branch_id, event_id)
    db.session.delete(calendar_event)
    db.session.commit()


def can_manage_calendar_event(user, calendar_event):
    return user.role == 'hod' and user.branch_id == calendar_event.branch_id


def _serialize_calendar_event(calendar_event):
    meta = CALENDAR_TYPE_META.get(calendar_event.type, CALENDAR_TYPE_META['event'])
    detail = calendar_event.description or f'{meta["label"]} scheduled for semester {calendar_event.semester}.'
    return {
        'id': calendar_event.id,
        'title': calendar_event.title,
        'type': calendar_event.type,
        'type_label': meta['label'],
        'tone': meta['tone'],
        'css_class': meta['css'],
        'date': calendar_event.date.isoformat(),
        'detail': detail,
        'semester': calendar_event.semester,
        'description': calendar_event.description,
    }


def _build_event_map(branch_id, semester, start_date, end_date):
    event_map = {}
    calendar_events = (
        CalendarEvent.query.filter(
            CalendarEvent.branch_id == branch_id,
            CalendarEvent.semester == semester,
            CalendarEvent.date >= start_date,
            CalendarEvent.date <= end_date,
        )
        .order_by(CalendarEvent.date.asc(), CalendarEvent.title.asc())
        .all()
    )
    for calendar_event in calendar_events:
        event_map.setdefault(calendar_event.date, []).append(_serialize_calendar_event(calendar_event))

    for day_events in event_map.values():
        day_events.sort(key=lambda item: (item['type'], item['title']))

    return event_map


def _build_month_event_rows(branch_id, semester, resolved_month, resolved_year):
    month_start = date(resolved_year, resolved_month, 1)
    month_end = date(resolved_year, resolved_month, calendar.monthrange(resolved_year, resolved_month)[1])
    events = (
        CalendarEvent.query.filter(
            CalendarEvent.branch_id == branch_id,
            CalendarEvent.semester == semester,
            CalendarEvent.date >= month_start,
            CalendarEvent.date <= month_end,
        )
        .order_by(CalendarEvent.date.asc(), CalendarEvent.title.asc())
        .all()
    )
    rows = []
    for event in events:
        serialized = _serialize_calendar_event(event)
        rows.append(
            {
                'event': event,
                'type_label': serialized['type_label'],
                'tone': serialized['tone'],
                'css_class': serialized['css_class'],
                'detail': serialized['detail'],
            }
        )
    return rows


def build_branch_calendar(branch_id, semester=None, month=None, year=None, user=None):
    resolved_year, resolved_month = resolve_calendar_period(month=month, year=year)
    resolved_semester = resolve_calendar_semester(branch_id, requested_semester=semester, user=user)
    month_matrix = calendar.Calendar(firstweekday=0).monthdatescalendar(resolved_year, resolved_month)
    start_date = month_matrix[0][0]
    end_date = month_matrix[-1][-1]
    event_map = _build_event_map(branch_id, resolved_semester, start_date, end_date)

    today = date.today()
    selected_date = today if today.month == resolved_month and today.year == resolved_year else date(resolved_year, resolved_month, 1)

    weeks = []
    selected_day = None
    month_event_count = 0
    month_exam_count = 0
    month_holiday_count = 0
    month_general_event_count = 0

    for week in month_matrix:
        week_cells = []
        for current_date in week:
            events = event_map.get(current_date, [])
            if current_date.month == resolved_month:
                month_event_count += len(events)
                month_exam_count += sum(1 for event in events if event['type'] == 'exam')
                month_holiday_count += sum(1 for event in events if event['type'] == 'holiday')
                month_general_event_count += sum(1 for event in events if event['type'] == 'event')

            cell = {
                'date': current_date,
                'iso_date': current_date.isoformat(),
                'day_number': current_date.day,
                'is_current_month': current_date.month == resolved_month,
                'is_today': current_date == today,
                'is_selected': current_date == selected_date,
                'events': events,
            }
            if current_date == selected_date:
                selected_day = cell
            week_cells.append(cell)
        weeks.append(week_cells)

    if selected_day is None:
        selected_day = weeks[0][0]
        selected_day['is_selected'] = True

    previous_year, previous_month = shift_calendar_period(resolved_year, resolved_month, -1)
    next_year, next_month = shift_calendar_period(resolved_year, resolved_month, 1)

    return {
        'month': resolved_month,
        'year': resolved_year,
        'semester': resolved_semester,
        'semester_options': SEMESTER_OPTIONS,
        'month_label': f'{calendar.month_name[resolved_month]} {resolved_year}',
        'weekday_labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'weeks': weeks,
        'selected_day': selected_day,
        'legend': [
            {'label': 'Exam', 'css_class': CALENDAR_TYPE_META['exam']['css']},
            {'label': 'Holiday', 'css_class': CALENDAR_TYPE_META['holiday']['css']},
            {'label': 'Event', 'css_class': CALENDAR_TYPE_META['event']['css']},
        ],
        'summary': {
            'total': month_event_count,
            'exams': month_exam_count,
            'holidays': month_holiday_count,
            'events': month_general_event_count,
        },
        'month_events': _build_month_event_rows(branch_id, resolved_semester, resolved_month, resolved_year),
        'previous_month': previous_month,
        'previous_year': previous_year,
        'next_month': next_month,
        'next_year': next_year,
    }


def build_calendar_api_payload(branch_id, semester=None, month=None, year=None, user=None):
    calendar_data = build_branch_calendar(branch_id, semester=semester, month=month, year=year, user=user)
    return {
        'month': calendar_data['month'],
        'year': calendar_data['year'],
        'semester': calendar_data['semester'],
        'month_label': calendar_data['month_label'],
        'summary': calendar_data['summary'],
        'selected_day': {
            'date': calendar_data['selected_day']['iso_date'],
            'events': calendar_data['selected_day']['events'],
        },
        'month_events': [
            {
                'id': row['event'].id,
                'title': row['event'].title,
                'date': row['event'].date.isoformat(),
                'type': row['event'].type,
                'type_label': row['type_label'],
                'description': row['event'].description,
                'detail': row['detail'],
                'semester': row['event'].semester,
            }
            for row in calendar_data['month_events']
        ],
    }

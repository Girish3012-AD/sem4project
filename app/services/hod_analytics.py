from __future__ import annotations

from collections import defaultdict

from app.models import Exam, Marks, Subject, User

PASS_PERCENTAGE = 40.0
WEAK_SUBJECT_THRESHOLD = 50.0


def _normalize_score(obtained, max_marks):
    if not max_marks:
        return 0.0
    return round((obtained / max_marks) * 100, 2)


def get_branch_marks(branch_id):
    return (
        Marks.query.join(Exam)
        .join(Subject)
        .join(User, User.id == Marks.student_id)
        .filter(Subject.branch_id == branch_id, User.role == 'student')
        .order_by(Exam.date.asc(), Subject.name.asc(), Marks.id.asc())
        .all()
    )


def build_branch_result_analytics(branch_id):
    marks = get_branch_marks(branch_id)
    subject_groups = defaultdict(list)
    exam_groups = defaultdict(list)
    student_groups = defaultdict(list)

    total_entries = 0
    pass_count = 0
    fail_count = 0

    for mark in marks:
        percentage = _normalize_score(mark.marks_obtained, mark.exam.max_marks)
        serialized = {
            'subject_name': mark.exam.subject.name,
            'subject_id': mark.exam.subject.id,
            'exam_name': mark.exam.name,
            'date': mark.exam.date.strftime('%Y-%m-%d'),
            'date_label': mark.exam.date.strftime('%d %b %Y'),
            'marks_obtained': round(mark.marks_obtained, 2),
            'max_marks': round(mark.exam.max_marks, 2),
            'percentage': percentage,
            'student_name': f'{mark.student.first_name} {mark.student.last_name}',
            'student_id': mark.student.id,
            'roll_no': mark.student.roll_no or 'N/A',
        }

        subject_groups[serialized['subject_name']].append(serialized)
        exam_groups[(serialized['date'], serialized['exam_name'])].append(serialized)
        student_groups[serialized['student_id']].append(serialized)
        total_entries += 1

        if percentage >= PASS_PERCENTAGE:
            pass_count += 1
        else:
            fail_count += 1

    subject_averages = []
    weak_subjects = []

    for subject_name, entries in subject_groups.items():
        average_percentage = round(sum(entry['percentage'] for entry in entries) / len(entries), 2)
        average_marks = round(sum(entry['marks_obtained'] for entry in entries) / len(entries), 2)
        row = {
            'subject_name': subject_name,
            'average_percentage': average_percentage,
            'average_marks': average_marks,
            'student_count': len({entry['student_id'] for entry in entries}),
            'assessment_count': len(entries),
            'status': 'Weak' if average_percentage < WEAK_SUBJECT_THRESHOLD else 'Healthy',
        }
        subject_averages.append(row)
        if row['status'] == 'Weak':
            weak_subjects.append(row)

    subject_averages.sort(key=lambda item: item['average_percentage'], reverse=True)
    weak_subjects.sort(key=lambda item: item['average_percentage'])

    top_performers = []
    for student_id, entries in student_groups.items():
        average_percentage = round(sum(entry['percentage'] for entry in entries) / len(entries), 2)
        total_marks = round(sum(entry['marks_obtained'] for entry in entries), 2)
        top_performers.append(
            {
                'student_id': student_id,
                'student_name': entries[0]['student_name'],
                'roll_no': entries[0]['roll_no'],
                'average_percentage': average_percentage,
                'total_marks': total_marks,
                'assessment_count': len(entries),
            }
        )

    top_performers.sort(key=lambda item: (item['average_percentage'], item['total_marks']), reverse=True)

    performance_trends = []
    for (exam_date, exam_name), entries in sorted(exam_groups.items(), key=lambda item: item[0][0]):
        performance_trends.append(
            {
                'date': exam_date,
                'date_label': entries[0]['date_label'],
                'exam_name': exam_name,
                'average_percentage': round(sum(entry['percentage'] for entry in entries) / len(entries), 2),
                'average_marks': round(sum(entry['marks_obtained'] for entry in entries) / len(entries), 2),
                'student_count': len(entries),
            }
        )

    overall_average = round(sum(row['average_percentage'] for row in subject_averages) / len(subject_averages), 2) if subject_averages else 0.0
    pass_rate = round((pass_count / total_entries) * 100, 2) if total_entries else 0.0

    return {
        'summary': {
            'subject_count': len(subject_averages),
            'pass_count': pass_count,
            'fail_count': fail_count,
            'pass_rate': pass_rate,
            'overall_average_percentage': overall_average,
            'top_performer_count': min(len(top_performers), 5),
        },
        'subject_averages': subject_averages,
        'weak_subjects': weak_subjects[:5],
        'top_performers': top_performers[:5],
        'performance_trends': performance_trends,
    }


def generate_branch_result_insights(analytics):
    insights = []
    summary = analytics['summary']
    subject_averages = analytics['subject_averages']
    weak_subjects = analytics['weak_subjects']
    top_performers = analytics['top_performers']
    performance_trends = analytics['performance_trends']

    insights.append(f"Overall pass rate: {summary['pass_rate']}%.")

    if weak_subjects:
        insights.append(f"{weak_subjects[0]['subject_name']} has the lowest performance at {weak_subjects[0]['average_percentage']}%.")

    if subject_averages:
        insights.append(f"{subject_averages[0]['subject_name']} is currently the strongest subject with an average of {subject_averages[0]['average_percentage']}%.")

    if top_performers:
        insights.append(f"Top performer right now is {top_performers[0]['student_name']} with an average of {top_performers[0]['average_percentage']}%.")

    if len(performance_trends) >= 2:
        delta = performance_trends[-1]['average_percentage'] - performance_trends[0]['average_percentage']
        if delta >= 5:
            insights.append("Branch performance trend is improving across recent assessments.")
        elif delta <= -5:
            insights.append("Recent assessment averages are declining and may need intervention.")
        else:
            insights.append("Performance trend is stable across recent assessments.")

    if not subject_averages:
        insights = ["No marks data is available yet for result analytics."]

    return insights[:5]

# GitHub Logbook

This logbook tracks the main repository changes and publication actions.

## 2026-04-01
- Added project files and pushed the initial application state to GitHub.
- Created `.gitignore` to exclude compiled Python files, database files, logs, and IDE metadata.
- Added `README.md` with installation, setup, and usage instructions.
- Added `GITHUB_LOGBOOK.md` for tracking repository maintenance entries.
- Added detailed phase report covering project work from 30 January 2026 through 1 April 2026.

## Project Phase Report
### Phase 1: Problem Understanding (30 Jan – 3 Feb 2026)
- Day 1: Identified problem in academic systems
- Day 2: Defined system objective: Centralized dashboard, multi-role system
- Day 3: Identified users: Student, Faculty, HOD, Admin
- Day 4: Listed features: Attendance, assignments, analytics
- Day 5: Finalized project title
- Output: Problem statement + requirements

### Phase 2: System Design (4 Feb – 10 Feb 2026)
- Day 6: Chose tech stack: Flask + SQLite
- Day 7: Designed architecture: Frontend → Backend → Database
- Day 8: Designed module structure: Admin, Faculty, Student
- Day 9: Planned folder structure: `app/`, `routes/`, `services/`, `models.py`, `templates/`, `static/`
- Day 10: Designed login system (role-based)
- Day 11: Created workflow diagrams (rough)
- Day 12: Full system blueprint ready

### Phase 3: Database & Backend Setup (11 Feb – 23 Feb 2026)
- Day 13: Installed Flask & dependencies
- Day 14: Created project structure
- Day 15: Defined database models in `models.py`
- Day 16: Created User table with roles
- Day 17: Created Attendance table
- Day 18: Created Assignment table
- Day 19: Established relationships
- Day 20: Initialized database (`site.db`)
- Day 21–22: Built authentication system
- Day 23: Login & logout functionality
- Day 24: Role-based redirection
- Output: Working backend foundation

### Phase 4: Core Feature Development (24 Feb – 9 Mar 2026)
- Day 26–28: Faculty module: mark attendance, upload assignments
- Day 29–31: Student module: view attendance, submit assignments
- Day 32–34: Admin module: manage users, manage branches
- Day 35–37: HOD module: analytics, reports
- Day 38: Created services layer for business logic separation
- Day 39: Implemented analytics logic
- Day 40: All core features implemented

### Phase 5: Frontend Development (10 Mar – 22 Mar 2026)
- Day 41–43: Designed HTML templates
- Day 44–46: Styled using CSS
- Day 47–48: Added JavaScript functionality
- Day 49: Connected frontend with backend
- Day 50: Created dashboards for each role
- Day 51: Improved UI structure
- Day 52: Complete UI integrated

### Phase 6: Testing & Finalization (23 Mar – 1 Apr 2026)
- Day 53: Tested login system
- Day 54: Tested role-based access
- Day 55: Tested attendance module
- Day 56: Tested assignment module
- Day 57: Fixed bugs
- Day 58: Checked database consistency
- Day 59: Final UI adjustments
- Day 60: Project completed
- Output: Fully functional system

## Notes
- Use this file to record future updates, bug fixes, and deployment notes.
- Keep entries chronological and concise.

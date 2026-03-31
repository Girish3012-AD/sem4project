# Student Academic Management System

A Flask-based student academic management application with separate dashboards for Admin, HOD, Faculty, and Students.

## Features
- Admin panel for branch and user management
- HOD dashboard for assigning faculty, managing subjects, exams, and notifications
- Faculty interface for assignments, attendance, marks, and leave requests
- Student portal for assignments, attendance, results, performance analytics, and reports
- Academic calendar support with seeded data

## Project Structure
- `run.py` - Application entry point
- `init_db.py` - Initialize the database schema
- `seed_data.py` / `seed_calendar.py` - Seed initial data
- `requirements.txt` - Python package dependencies
- `app/` - Flask application package
  - `auth.py` - Authentication routes
  - `models.py` - SQLAlchemy models
  - `routes_*` - Role-specific route modules
  - `services/` - Business logic and analytics
  - `templates/` - HTML templates
  - `static/` - CSS and JavaScript assets

## Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the environment:
   - Windows:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - macOS / Linux:
     ```bash
     source venv/bin/activate
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Initialize the database:
   ```bash
   python init_db.py
   ```
5. Seed sample data:
   ```bash
   python seed_data.py
   python seed_calendar.py
   ```
6. Run the application:
   ```bash
   python run.py
   ```

## Usage
Open a browser and visit `http://127.0.0.1:5000` to access the web app.

## Notes
- `app.run(debug=True)` is used for development only. Disable debug mode before deploying to production.
- Add sensitive credentials and local settings to `.env` and do not commit them.

## Project Timeline
Detailed phase plan and timeline are available in `PROJECT_PLAN.md`.

## License
This project is provided as-is. Update this section with your preferred license if needed.

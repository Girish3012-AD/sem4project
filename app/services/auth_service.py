from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.models import Branch, Division, User


ALLOWED_SIGNUP_ROLES = {"student", "faculty", "hod"}


def normalize_signup_data(form):
    roll_no_raw = (form.get("roll_no") or "").strip()
    branch_id_raw = (form.get("branch_id") or "").strip()
    division_id_raw = (form.get("division_id") or "").strip()

    return {
        "first_name": (form.get("first_name") or "").strip(),
        "last_name": (form.get("last_name") or "").strip(),
        "email": (form.get("email") or "").strip().lower(),
        "password": form.get("password") or "",
        "role": (form.get("role") or "").strip().lower(),
        "branch_id": int(branch_id_raw) if branch_id_raw.isdigit() else None,
        "division_id": int(division_id_raw) if division_id_raw.isdigit() else None,
        "prn": (form.get("prn") or "").strip(),
        "roll_no": int(roll_no_raw) if roll_no_raw.isdigit() else None,
    }


def validate_signup_data(data):
    errors = []
    branch = None
    division = None

    if not data["first_name"]:
        errors.append("First name is required.")
    if not data["last_name"]:
        errors.append("Last name is required.")
    if not data["email"]:
        errors.append("Email address is required.")
    if not data["password"]:
        errors.append("Password is required.")
    elif len(data["password"]) < 6:
        errors.append("Password must be at least 6 characters long.")

    if data["role"] not in ALLOWED_SIGNUP_ROLES:
        errors.append("Please choose a valid role.")

    if data["role"] == "admin":
        errors.append("Admin accounts cannot be created via signup.")

    if data["branch_id"] is None:
        errors.append("Please select a branch.")
    else:
        branch = Branch.query.get(data["branch_id"])
        if branch is None:
            errors.append("Selected branch does not exist.")

    if data["email"] and User.query.filter_by(email=data["email"]).first():
        errors.append("Email already registered.")

    if data["role"] == "student":
        if not data["prn"]:
            errors.append("PRN is required for student accounts.")
        elif User.query.filter_by(prn=data["prn"]).first():
            errors.append("PRN already exists.")

        if data["roll_no"] is None:
            errors.append("Roll number is required for student accounts.")
        elif data["roll_no"] <= 0:
            errors.append("Roll number must be greater than 0.")

        if data["division_id"] is None:
            errors.append("Please select a division for the student account.")
        else:
            division = Division.query.get(data["division_id"])
            if division is None:
                errors.append("Selected division does not exist.")
            elif branch is not None and division.branch_id != branch.id:
                errors.append("Selected division does not belong to the chosen branch.")

        if division is not None and data["roll_no"] is not None:
            existing_roll = User.query.filter_by(
                role="student",
                division_id=division.id,
                roll_no=data["roll_no"],
            ).first()
            if existing_roll:
                errors.append("Roll number already exists in the selected division.")
    else:
        data["prn"] = ""
        data["roll_no"] = None
        data["division_id"] = None

    return errors, branch, division


def build_signup_user(data, branch=None, division=None):
    new_user = User(
        email=data["email"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        role=data["role"],
        branch_id=branch.id if branch else None,
        division_id=division.id if division else None,
        prn=data["prn"] or None,
        roll_no=data["roll_no"],
    )
    new_user.set_password(data["password"])
    return new_user


def friendly_signup_integrity_error(error):
    if not isinstance(error, IntegrityError):
        return "Unable to create the account right now. Please try again."

    message = str(error.orig).lower() if getattr(error, "orig", None) else str(error).lower()
    if "user.prn" in message:
        return "PRN already exists."
    if "user.email" in message:
        return "Email already registered."
    return "Unable to create the account because some details already exist. Please review the form and try again."

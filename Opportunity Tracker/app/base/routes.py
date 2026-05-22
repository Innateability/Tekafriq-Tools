from app.utils import login_required
import os

from datetime import timedelta

from flask import (
    Blueprint,
    request,
    url_for,
    flash,
    render_template,
    redirect,
    jsonify,
    session
)

from flask_jwt_extended import (
    create_access_token,
    set_access_cookies,
    unset_jwt_cookies,
    jwt_required,
    get_jwt_identity,
    get_jwt
)

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from sqlalchemy.exc import IntegrityError

from shared_models.models import (
    Employee,
    Authentication,
    Department,
    Administrator,
    EmployeeEmail
)

from shared_models import db

base_bp = Blueprint("OTbase", __name__,url_prefix="opportunity_tracker/")

# =========================================================
# LOGIN
# =========================================================

@base_bp.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Email and password are required", "error")
            return redirect(url_for("base.login"))

        auth = Authentication.query.filter_by(email=email).first()

        if not auth:
            flash("Account linked to this email does not exist", "error")
            return redirect(url_for("base.login"))

        if not check_password_hash(auth.password, password):
            flash("Invalid password", "error")
            return redirect(url_for("base.login"))

        # -------------------------------------------------
        # DETERMINE ROLE
        # -------------------------------------------------

        role = auth.role

        # -------------------------------------------------
        # CREATE JWT TOKEN
        # -------------------------------------------------

        access_token = create_access_token(
            identity=str(auth.id),
            additional_claims={
                "role": role,
                "email": auth.email,
                "name": auth.name
            },
            expires_delta=timedelta(days=1)
        )

        response = None

        session.clear()
        session["user_id"] = auth.id
        session["role"] = role
        session["email"] = auth.email

        flash("Login successful", "success")

        if role == "employee":
            response = redirect(url_for("employee.home"))

        elif role == "admin":
            response = redirect(url_for("admin.home"))

        else:
            flash("Invalid role", "error")
            return redirect(url_for("base.login"))

        # -------------------------------------------------
        # STORE JWT IN SECURE COOKIE
        # -------------------------------------------------

        set_access_cookies(response, access_token)

        return response

    return render_template("login.html")


# =========================================================
# ADMIN SIGNUP
# =========================================================

@base_bp.route("/admin_signup", methods=["GET", "POST"])
def admin_signup():

    if request.method == "POST":

        departments = [
            "HCM",
            "SCM",
            "Procurement",
            "Finance",
            "Administration",
            "Business Development",
            "Technical",
            "Support"
        ]

        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        entered_entry_code = request.form.get("entry_code")

        entry_code = os.getenv("ENTRY_CODE")

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not all([username, password, email, entered_entry_code]):
            flash("All fields are required", "error")
            return redirect(url_for("base.admin_signup"))

        if not entry_code:
            flash("Server configuration error", "error")
            return redirect(url_for("base.admin_signup"))

        if entry_code != entered_entry_code:
            flash("Incorrect entry code", "error")
            return redirect(url_for("base.admin_signup"))
        
        administrator = Administrator.query.first()

        if administrator:
            flash("Admin already registered", "error")
            return redirect(url_for("base.admin_signup"))

        if Authentication.query.filter_by(email=email).first():
            flash("Email already registered", "error")
            return redirect(url_for("base.admin_signup"))

        # -------------------------------------------------
        # CREATE AUTH
        # -------------------------------------------------

        hashed_pw = generate_password_hash(password)

        auth = Authentication(
            email=email,
            password=hashed_pw,
            name=username,
            role="admin"
        )

        # -------------------------------------------------
        # CREATE ADMIN
        # -------------------------------------------------

        administrator = Administrator(name=username)

        auth.administrator = administrator

        db.session.add(administrator)

        # -------------------------------------------------
        # CREATE DEFAULT DEPARTMENTS
        # -------------------------------------------------

        for dep_name in departments:

            dep = Department.query.filter_by(name=dep_name).first()

            if not dep:
                dep = Department(name=dep_name)
                db.session.add(dep)

            administrator.departments.append(dep)

        db.session.add(auth)

        try:
            db.session.commit()

        except IntegrityError:

            db.session.rollback()

            flash("Signup failed", "error")

            return redirect(url_for("base.admin_signup"))

        flash("Admin account created successfully", "success")

        return redirect(url_for("base.login"))

    return render_template("admin_signup.html")


# =========================================================
# EMPLOYEE / TEAM LEADER SIGNUP
# =========================================================

@base_bp.route("/signup", methods=["GET", "POST"])
def signup():

    departments = [
        "HCM",
        "SCM",
        "Procurement",
        "Finance",
        "Administration",
        "Business Development",
        "Technical",
        "Support"
    ]

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        entered_entry_code = request.form.get("entry_code")
        entry_code = os.getenv("ENTRY_CODE")

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not all([username, password, email, entered_entry_code]):
            flash("All fields are required", "error")
            return redirect(url_for("base.signup"))

        if not entry_code:
            flash("Server configuration error", "error")
            return redirect(url_for("base.signup"))

        if entry_code != entered_entry_code:
            flash("Incorrect entry code", "error")
            return redirect(url_for("base.signup"))

        if Authentication.query.filter_by(email=email).first():
            flash("Email already registered", "error")
            return redirect(url_for("base.signup"))

        employee_info = EmployeeEmail.query.filter_by(email=email).first()

        if not employee_info:
            flash("Email not authorized", "error")
            return redirect(request.url)
        hashed_pw = generate_password_hash(password)
        auth = Authentication(
            email=email,
            password=hashed_pw,
            name=username,
            role="employee"
        )
        department_name = employee_info.department

        department = Department.query.filter_by(
            name=department_name
            ).first()
        
        if not department:
            department = Department(name=department_name)
            db.session.add(department)
        employee = Employee(
            name=username,
            department=department
        )

        auth.employee = employee
        db.session.add(employee)
        db.session.add(auth)

        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            flash(
                "Signup failed due to duplicate or invalid data",
                "error"
            )
            return redirect(url_for("base.signup"))
        flash("Signup successful", "success")
        return redirect(url_for("base.login"))
    return render_template(
        "signup.html",
        departments=departments
    )


# =========================================================
# LOGOUT
# =========================================================

@base_bp.route("/logout")
@jwt_required()
def logout():

    response = redirect(url_for("base.login"))

    unset_jwt_cookies(response)

    flash("Logged out successfully", "success")

    session.clear()

    return response


# =========================================================
# CURRENT USER
# =========================================================

@base_bp.route("/me")
@jwt_required()
def me():

    user_id = get_jwt_identity()

    claims = get_jwt()

    return jsonify({
        "user_id": user_id,
        "role": claims.get("role"),
        "email": claims.get("email"),
        "name": claims.get("name")
    })
from flask import Blueprint, render_template, request, redirect, session
from utils.validators import is_valid_name, is_valid_mobile, is_strong_password
from werkzeug.security import check_password_hash, generate_password_hash
from db import cursor, db

auth_bp = Blueprint("auth", __name__)

# ---------------- LOGIN ----------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")

        cursor.execute("SELECT id, password FROM users WHERE mobile=%s", (mobile,))
        user = cursor.fetchone()

        if user and check_password_hash(user[1], password):
            session.clear()
            session["user_id"] = user[0]
            return redirect("/dashboard")

        return render_template("auth.html", error="Invalid mobile or password")

    return render_template("auth.html", error=None)


# ---------------- REGISTER ----------------
@auth_bp.route("/register", methods=["GET","POST"])
def register():
    name = request.form.get("name", "").strip()
    mobile = request.form.get("mobile", "").strip()
    password = request.form.get("password", "")

    # ---- Validations ----
    if not is_valid_name(name):
        return render_template("auth.html", error="Name must be at least 3 letters and only alphabets")

    if not is_valid_mobile(mobile):
        return render_template("auth.html", error="Invalid mobile number (must be 10 digits starting with 6–9)")

    if not is_strong_password(password):
        return render_template("auth.html", error="Password must contain upper, lower, number & special char")

    password_hash = generate_password_hash(password)

    try:
        cursor.execute("""
            INSERT INTO users(name, mobile, password)
            VALUES (%s,%s,%s)
        """, (name, mobile, password_hash))
        db.commit()

    except Exception:
        db.rollback()
        return render_template("auth.html", error="Mobile number already registered")

    # OR
    return render_template("auth.html", success="Registration successful! Please login.")


# ---------------- LOGOUT ----------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

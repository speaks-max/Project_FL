from flask import Blueprint, render_template, request, redirect, session
from db import cursor, db

expense_bp = Blueprint("expense", __name__)

# -------------------------------
@expense_bp.route("/add_expense_ui")
def add_expense_ui():
    cursor.execute("SELECT id, name FROM users")
    users = cursor.fetchall()
    return render_template("add_expense_ui.html", users=users)


# -------------------------------
@expense_bp.route("/add_expense_v2", methods=["POST"])
def add_expense_v2():

    group = request.form.get("group_name", "").strip()
    desc = request.form.get("desc", "").strip()
    paid_by_id = request.form.get("paid_by")
    members = request.form.getlist("members")

    cursor.execute("SELECT id, name FROM users")
    users = cursor.fetchall()

    # Always include payer
    members = list(set(members + [paid_by_id]))


    # ---- Validations ----
    if len(group) < 3:
        return render_template("add_expense_ui.html", users=users, error="Invalid group name")

    if len(desc) < 3:
        return render_template("add_expense_ui.html", users=users, error="Invalid description")

    if not paid_by_id:
        return render_template("add_expense_ui.html", users=users, error="Select who paid")

    if len(members) < 2:
        return render_template("add_expense_ui.html", users=users, error="Select at least 2 members")

    if paid_by_id not in members:
        return render_template("add_expense_ui.html", users=users, error="Paid by must be one of the members")

    # ---- Amount ----
    amount_raw = request.form.get("amount", "").strip()
    if not amount_raw.isdigit():
        return render_template("add_expense_ui.html", users=users, error="Amount must be whole rupees only")

    rupees = int(amount_raw)
    if rupees <= 0:
        return render_template("add_expense_ui.html", users=users, error="Amount must be greater than zero")

    total_paise = rupees * 100

    try:
        # ---- Create or fetch group ----
        cursor.execute("SELECT id FROM split_groups WHERE name=%s", (group,))
        row = cursor.fetchone()

        if row:
            gid = row[0]
        else:
            cursor.execute("INSERT INTO split_groups(name) VALUES(%s)", (group,))
            gid = cursor.lastrowid

        # ---- Add group members ----
        for uid in members:
            cursor.execute("""
                INSERT IGNORE INTO split_group_members (group_id, user_id)
                VALUES (%s,%s)
            """, (gid, uid))

        # ---- Insert expense ----
        cursor.execute("""
            INSERT INTO split_expenses (group_id, paid_by_id, description, total_paise)
            VALUES (%s,%s,%s,%s)
        """, (gid, paid_by_id, desc, total_paise))

        eid = cursor.lastrowid

        # ---- Split equally ----
        n = len(members)
        base = total_paise // n
        remainder = total_paise % n

        for i, uid in enumerate(members):
            share = base + (1 if i < remainder else 0)

            cursor.execute("""
                INSERT INTO split_shares (expense_id, user_id, share_paise)
                VALUES (%s,%s,%s)
            """, (eid, uid, share))

        db.commit()

    except Exception as e:
        db.rollback()
        return render_template("add_expense_ui.html", users=users, error="Database error: " + str(e))

    return redirect("/dashboard")

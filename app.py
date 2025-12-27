from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import MySQLdb
import math

# ---------VALIDATIONS----------
def is_valid_name(name):
    name = name.strip()
    if len(name) < 3:
        return False
    for ch in name:
        if not (ch.isalpha() or ch == " "):
            return False
    return True


def is_valid_mobile(mobile):
    if len(mobile) != 10:
        return False
    if mobile[0] not in "6789":
        return False
    if not mobile.isdigit():
        return False
    return True


def is_strong_password(password):
    if len(password) < 8:
        return False

    has_upper = False
    has_lower = False
    has_digit = False
    has_special = False

    for ch in password:
        if ch.isupper():
            has_upper = True
        elif ch.islower():
            has_lower = True
        elif ch.isdigit():
            has_digit = True
        else:
            has_special = True

    return has_upper and has_lower and has_digit and has_special
# --------------------------------------------------------------------

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

db = MySQLdb.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME")
)

cursor = db.cursor()

# ----------------------------------------
# Settlement Engine (PhonePe logic)
# ----------------------------------------
def get_settlements(group_id):

    # 🔥 If group is closed → no balances should show
    cursor.execute("SELECT closed FROM split_groups WHERE id=%s", (group_id,))
    if cursor.fetchone()[0] == 1:
        return []

    # 1️⃣ Get split balances in paise
    cursor.execute("""
        SELECT ss.username, SUM(ss.balance * 100)
        FROM split_shares ss
        JOIN split_expenses se ON ss.expense_id = se.id
        WHERE se.group_id = %s
        GROUP BY ss.username
    """, (group_id,))

    balances = {}
    for user, paise in cursor.fetchall():
        balances[user] = int(paise)

    # 2️⃣ Apply settlements ledger (paise)
    cursor.execute("""
        SELECT payer, receiver, SUM(amount)
        FROM settlements
        WHERE group_id = %s
        GROUP BY payer, receiver
    """, (group_id,))

    for payer, receiver, amt in cursor.fetchall():
        balances[payer] += int(amt)
        balances[receiver] -= int(amt)

    # 3️⃣ Separate debtors & creditors
    debtors = []
    creditors = []

    for user, paise in balances.items():
        if paise < 0:
            debtors.append([user, -paise])
        elif paise > 0:
            creditors.append([user, paise])

    # 4️⃣ Compute who pays whom
    settlements = []
    i = j = 0

    while i < len(debtors) and j < len(creditors):
        pay_paise = min(debtors[i][1], creditors[j][1])

        pay_rupees = math.ceil(pay_paise / 100)

        settlements.append((
            debtors[i][0],
            creditors[j][0],
            pay_rupees
        ))

        debtors[i][1] -= pay_paise
        creditors[j][1] -= pay_paise

        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1

    return settlements

# ----------------------------------------
@app.route("/")
def root():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")

# ----------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mobile = request.form["mobile"]
        password = request.form["password"]

        cursor.execute(
            "SELECT id, password FROM users WHERE mobile=%s",
            (mobile,)
        )
        user = cursor.fetchone()
        print("DB returned user:", user)
        
        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            return redirect("/dashboard")

        # Instead of returning plain text, show error inside page
        return render_template("auth.html", error="Invalid mobile number or password")

    # GET request → just show the page
    return render_template("auth.html", error=None)

# ----------------------------------------
@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    mobile = request.form["mobile"]
    password = request.form["password"]

    # -------- VALIDATIONS --------
    if not is_valid_name(name):
        return render_template("auth.html", error="Name must contain only letters and spaces and be at least 3 characters")

    if not is_valid_mobile(mobile):
        return render_template("auth.html", error="Invalid mobile number (must be 10 digits starting with 6–9)")

    if not is_strong_password(password):
        return render_template(
            "auth.html",
            error="Password must be at least 8 characters with uppercase, lowercase, number and special character"
        )

    password_hash = generate_password_hash(password)

    try:
        cursor.execute(
            "INSERT INTO users(name, mobile, password) VALUES(%s,%s,%s)",
            (name.strip(), mobile, password_hash)
        )
        db.commit()
    except:
        return render_template("auth.html", error="Mobile number already exists")

    return redirect("/login")

# ----------------------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    cursor.execute("""
    SELECT sg.name
    FROM split_groups sg
    JOIN split_group_members gm ON sg.id = gm.group_id
    JOIN users u ON gm.username = u.name
    WHERE u.id = %s
    """, (session["user_id"],))

    groups = cursor.fetchall()


    return render_template("dashboard.html", split_group=groups)

# ----------------------------------------
@app.route("/add_expense_ui")
def add_expense_ui():
    cursor.execute("SELECT name FROM users")
    users = [u[0] for u in cursor.fetchall()]
    return render_template("add_expense_ui.html", users=users)

# ----------------------------------------
@app.route("/add_expense_v2", methods=["POST"])
def add_expense_v2():
    group = request.form["group_name"].strip()
    amount = request.form["amount"]
    desc = request.form["desc"].strip()
    paid_by = request.form["paid_by"]
    members = request.form.getlist("members")

    # Load users for UI reload
    cursor.execute("SELECT name FROM users")
    users = [u[0] for u in cursor.fetchall()]

    # -------- VALIDATIONS --------

    # Group name
    if not group or len(group) < 3:
        return render_template("add_expense_ui.html", users=users, error="Enter a valid group name")

    # Amount
    try:
        amount = float(amount)
    except:
        return render_template("add_expense_ui.html", users=users, error="Amount must be a number")

    if amount <= 0:
        return render_template("add_expense_ui.html", users=users, error="Amount must be greater than zero")

    # Members
    if len(members) < 2:
        return render_template("add_expense_ui.html", users=users, error="Select at least two members")

    for m in members:
        if m not in users:
            return render_template("add_expense_ui.html", users=users, error="Invalid member selected")

    # Paid by
    if paid_by not in members:
        return render_template("add_expense_ui.html", users=users, error="Paid by must be one of the selected members")

    # Description
    if not desc or len(desc) < 3:
        return render_template("add_expense_ui.html", users=users, error="Enter a valid description")

    # -------- GET OR CREATE GROUP --------
    cursor.execute("SELECT id FROM split_groups WHERE name=%s", (group,))
    g = cursor.fetchone()

    if g:
        gid = g[0]
    else:
        cursor.execute("INSERT INTO split_groups(name) VALUES(%s)", (group,))
        db.commit()
        gid = cursor.lastrowid

        for m in members:
            cursor.execute("INSERT INTO split_group_members VALUES(%s,%s)", (gid, m))
        db.commit()

    # -------- SAVE EXPENSE --------
    cursor.execute("""
        INSERT INTO split_expenses(group_id,description,total,paid_by)
        VALUES(%s,%s,%s,%s)
    """, (gid, desc, amount, paid_by))
    db.commit()
    eid = cursor.lastrowid

    # -------- SPLIT LOGIC (PhonePe style) --------
    n = len(members)
    total_paise = int(round(amount * 100))
    base = total_paise // n
    remainder = total_paise % n

    for i, m in enumerate(members):
        if i < remainder:
            user_share_paise = base + 1
        else:
            user_share_paise = base

        user_share = user_share_paise / 100
        paid = amount if m == paid_by else 0
        balance = round(paid - user_share, 2)

        cursor.execute(
            "INSERT INTO split_shares VALUES(%s,%s,%s,%s,%s)",
            (eid, m, user_share, paid, balance)
        )

    db.commit()
    return redirect("/dashboard")

# ----------------------------------------
@app.route("/group/<group>")
def group_chat(group):
    cursor.execute("SELECT id FROM split_groups WHERE name=%s",(group,))
    g = cursor.fetchone()
    if not g:
        return render_template("group_chat.html", error="Group not found", group=None, expenses=[], settlements=[])

    gid=g[0]

    cursor.execute("SELECT description,total,paid_by FROM split_expenses WHERE group_id=%s",(gid,))
    expenses=cursor.fetchall()

    settlements=get_settlements(gid)

    return render_template("group_chat.html", group=group, expenses=expenses, settlements=settlements)

# ----------------------------------------
@app.route("/settle", methods=["POST"])
def settle():
    group = request.form["group"]
    payer = request.form["payer"]
    receiver = request.form["receiver"]

    rupees = int(request.form["amount"])
    paise = rupees * 100

    cursor.execute("SELECT id FROM split_groups WHERE name=%s", (group,))
    gid = cursor.fetchone()[0]

    # Store settlement
    cursor.execute("""
        INSERT INTO settlements (group_id, payer, receiver, amount)
        VALUES (%s,%s,%s,%s)
    """, (gid, payer, receiver, paise))
    db.commit()

    # Total split paise
    cursor.execute("""
        SELECT SUM(ss.balance * 100)
        FROM split_shares ss
        JOIN split_expenses se ON ss.expense_id = se.id
        WHERE se.group_id = %s
    """, (gid,))
    split_total = int(cursor.fetchone()[0] or 0)

    # Total settled paise
    cursor.execute("""
        SELECT COALESCE(SUM(amount),0)
        FROM settlements
        WHERE group_id = %s
    """, (gid,))
    settled = int(cursor.fetchone()[0])

    remaining = split_total - settled

    # If less than ₹1 remains → absorb it
    if abs(remaining) < 100 and remaining != 0:
        # get first payer
        cursor.execute("""
            SELECT paid_by FROM split_expenses
            WHERE group_id = %s
            ORDER BY id ASC LIMIT 1
        """, (gid,))
        owner = cursor.fetchone()[0]

        # neutralize remainder
        cursor.execute("""
            INSERT INTO settlements (group_id, payer, receiver, amount)
            VALUES (%s,'SYSTEM',%s,%s)
        """, (gid, owner, remaining))

        # close group
        cursor.execute("UPDATE split_groups SET closed=1 WHERE id=%s", (gid,))
        db.commit()

    return redirect(f"/group/{group}")
# ----------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__=="__main__":
    app.run(debug=True)

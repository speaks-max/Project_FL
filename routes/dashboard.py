from flask import Blueprint, render_template, session, redirect
from db import cursor
from services.settlement import get_user_net

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    uid = session["user_id"]

    # -------------------------
    # All groups of this user
    # -------------------------
    cursor.execute("""
        SELECT sg.id, sg.name
        FROM split_groups sg
        JOIN split_group_members gm ON sg.id = gm.group_id
        WHERE gm.user_id = %s
    """, (uid,))

    groups = cursor.fetchall()

    dashboard_data = []

    for gid, gname in groups:
        net = get_user_net(uid, gid)

        if net > 0:
            status = f"You get ₹{net/100:.2f}"
        elif net < 0:
            status = f"You owe ₹{abs(net)/100:.2f}"
        else:
            status = "Settled"

        dashboard_data.append((gname, status))

    return render_template("dashboard.html", split_group=dashboard_data)

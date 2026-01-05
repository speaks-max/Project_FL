from flask import Blueprint, render_template
from db import cursor
from services.settlement import get_settlements, get_user_net, get_payment_history

group_bp = Blueprint("group", __name__, url_prefix="/group")


@group_bp.route("/<group>")
def group_chat(group):

    # --------------------
    # Get group id
    # --------------------
    cursor.execute("SELECT id FROM split_groups WHERE name = %s", (group,))
    row = cursor.fetchone()

    if not row:
        return render_template(
            "group_chat.html",
            error="Group not found",
            group=None,
            expenses=[],
            settlements=[],
            balances=[]
        )

    gid = row[0]

    # --------------------
    # Expenses list
    # --------------------
    cursor.execute("""
        SELECT e.description, e.total_paise, u.name
        FROM split_expenses e
        JOIN users u ON u.id = e.paid_by_id
        WHERE e.group_id = %s
        ORDER BY e.id DESC
    """, (gid,))
    expenses = cursor.fetchall()

    # --------------------
    # Get group members
    # --------------------
    cursor.execute("""
        SELECT u.id, u.name
        FROM users u
        JOIN split_group_members gm ON gm.user_id = u.id
        WHERE gm.group_id = %s
        ORDER BY u.name
    """, (gid,))
    members = cursor.fetchall()

    # --------------------
    # Compute balances (Python engine)
    # --------------------
    balances = []

    for uid, name in members:
        net = get_user_net(uid, gid)

        if net > 0:
            balances.append((name, f"gets ₹{net / 100:.2f}"))
        elif net < 0:
            balances.append((name, f"owes ₹{abs(net) / 100:.2f}"))
        else:
            balances.append((name, "settled"))

    # --------------------
    # Live settlements (who should pay whom)
    # --------------------
    settlements = get_settlements(gid)
    payment_history = get_payment_history(gid)

    return render_template(
    "group_chat.html",
    group=group,
    expenses=expenses,
    balances=balances,
    settlements=settlements,
    payment_history=payment_history
)


from flask import Blueprint, request, redirect, session
from db import cursor, db
from services.settlement import get_user_net
from decimal import Decimal

settle_bp = Blueprint("settle", __name__)


@settle_bp.route("/settle", methods=["POST"])
def settle():
    if "user_id" not in session:
        return redirect("/login")

    group = request.form["group"]
    payer_id = int(request.form["payer"])
    receiver_id = int(request.form["receiver"])

    try:
        rupees = Decimal(request.form["amount"])
        amount_paise = int(rupees * 100)
    except:
        return redirect(f"/group/{group}")

    if rupees <= 0:
        return redirect(f"/group/{group}")

    amount_paise = int(rupees * 100)

    # get group id
    cursor.execute("SELECT id FROM split_groups WHERE name=%s", (group,))
    gid = cursor.fetchone()[0]

    # get real balances
    payer_net = get_user_net(payer_id, gid)
    receiver_net = get_user_net(receiver_id, gid)

    # payer must owe, receiver must be owed
    if payer_net >= 0 or receiver_net <= 0:
        print("Invalid payer/receiver")
        return redirect(f"/group/{group}")

    max_payable = min(-payer_net, receiver_net)

    if amount_paise > max_payable:
        print("Overpay blocked")
        return redirect(f"/group/{group}")

    # record payment
    cursor.execute("""
        INSERT INTO settlements (group_id, payer_id, receiver_id, amount_paise)
        VALUES (%s, %s, %s, %s)
    """, (gid, payer_id, receiver_id, amount_paise))

    db.commit()

    return redirect(f"/group/{group}")

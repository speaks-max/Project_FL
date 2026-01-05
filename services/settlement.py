from db import cursor
from decimal import Decimal

def get_user_net(user_id, group_id):
    cursor.execute("""
    SELECT
        COALESCE((
            SELECT SUM(total_paise)
            FROM split_expenses
            WHERE paid_by_id = %s AND group_id = %s
        ),0)

        -

        COALESCE((
            SELECT SUM(ss.share_paise)
            FROM split_shares ss
            JOIN split_expenses e ON ss.expense_id = e.id
            WHERE ss.user_id = %s AND e.group_id = %s
        ),0)

        +

        COALESCE((
            SELECT SUM(amount_paise)
            FROM settlements
            WHERE receiver_id = %s AND group_id = %s
        ),0)

        +

        COALESCE((
            SELECT SUM(amount_paise)
            FROM settlements
            WHERE payer_id = %s AND group_id = %s
        ),0)
    """, (user_id, group_id, user_id, group_id, user_id, group_id, user_id, group_id))

    return cursor.fetchone()[0] or 0

def get_settlements(group_id):
    cursor.execute("""
        SELECT
            u.id,
            u.name,

            COALESCE((
                SELECT SUM(total_paise)
                FROM split_expenses
                WHERE paid_by_id = u.id AND group_id = %s
            ),0)

            -

            COALESCE((
                SELECT SUM(ss.share_paise)
                FROM split_shares ss
                JOIN split_expenses e ON ss.expense_id = e.id
                WHERE ss.user_id = u.id AND e.group_id = %s
            ),0)

            +

            COALESCE((
                SELECT SUM(amount_paise)
                FROM settlements
                WHERE receiver_id = u.id AND group_id = %s
            ),0)

            +

            COALESCE((
                SELECT SUM(amount_paise)
                FROM settlements
                WHERE payer_id = u.id AND group_id = %s
            ),0)

            AS net_paise

        FROM users u
        JOIN split_group_members gm ON gm.user_id = u.id
        WHERE gm.group_id = %s
    """, (group_id, group_id, group_id, group_id, group_id))

    rows = cursor.fetchall()

    debtors = []
    creditors = []

    for uid, name, net in rows:
        if net < 0:
            debtors.append([uid, name, -net])
        elif net > 0:
            creditors.append([uid, name, net])

    settlements = []
    i = j = 0

    while i < len(debtors) and j < len(creditors):
        pay = min(debtors[i][2], creditors[j][2])

        settlements.append((
            debtors[i][0], debtors[i][1],
            creditors[j][0], creditors[j][1],
            pay / Decimal("100")     # DO NOT truncate money
        ))

        debtors[i][2] -= pay
        creditors[j][2] -= pay

        if debtors[i][2] == 0:
            i += 1
        if creditors[j][2] == 0:
            j += 1

    return settlements

def get_payment_history(group_id):
    cursor.execute("""
    SELECT
        p.name AS payer,
        r.name AS receiver,
        (s.amount_paise / 100.0) AS amount_rupees,
        s.created_at
    FROM settlements s
    JOIN users p ON p.id = s.payer_id
    JOIN users r ON r.id = s.receiver_id
    WHERE s.group_id = %s
    ORDER BY s.created_at DESC
    """, (group_id,))

    return cursor.fetchall()


"""
auth.py — Session-based authentication helpers for GRec_Tr
"""
from functools import wraps
from flask import session, redirect, url_for, flash
from database import get_db

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    if 'user_id' not in session:
        return None
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?", (session['user_id'],)
    ).fetchone()
    conn.close()
    return user

def get_user_groups(user_id):
    conn = get_db()
    groups = conn.execute("""
        SELECT tg.*, gm.role,
               (SELECT COUNT(*) FROM group_members WHERE group_id = tg.id) AS member_count
        FROM travel_groups tg
        JOIN group_members gm ON tg.id = gm.group_id
        WHERE gm.user_id = ?
        ORDER BY tg.created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return groups
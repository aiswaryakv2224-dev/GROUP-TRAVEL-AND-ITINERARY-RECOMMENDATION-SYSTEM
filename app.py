"""
app.py — GRec_Tr Flask Application
Full routes including recommendation engine integration.
"""
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify)
from database import get_db, init_db, hash_password, verify_password
from auth import login_required, get_current_user, get_user_groups
import secrets

app = Flask(__name__)
app.secret_key = 'grec_tr_secret_key_2024'


# ─────────────────────────────────────────────────────────────────────────────
# HOME
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    user = get_current_user()
    return render_template('index.html', user=user)


# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username         = request.form.get('username', '').strip()
        email            = request.form.get('email', '').strip()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name        = request.form.get('full_name', '').strip()
        age              = request.form.get('age', None)

        errors = []
        if len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if not full_name:
            errors.append('Full name is required.')

        if not errors:
            conn = get_db()
            existing = conn.execute(
                'SELECT id FROM users WHERE username=? OR email=?',
                (username, email)
            ).fetchone()
            if existing:
                errors.append('Username or email already taken.')
            else:
                conn.execute('''
                    INSERT INTO users
                      (username, email, password, full_name, age)
                    VALUES (?,?,?,?,?)
                ''', (username, email, hash_password(password),
                      full_name, age or None))
                conn.commit()
                conn.close()
                flash('Account created! Please sign in.', 'success')
                return redirect(url_for('login'))
            conn.close()

        for e in errors:
            flash(e, 'danger')
        return render_template('register.html',
                               form_data=request.form)

    return render_template('register.html', form_data={})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE username=? OR email=?',
            (username, username)
        ).fetchone()
        conn.close()

        if user and verify_password(password, user['password']):
            session['user_id']   = user['id']
            session['username']  = user['username']
            session['full_name'] = user['full_name']
            flash(f"Welcome back, {user['full_name'].split()[0]}!", 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    user   = get_current_user()
    groups = get_user_groups(session['user_id'])

    conn = get_db()
    rating_count = conn.execute(
        'SELECT COUNT(*) as c FROM destination_ratings WHERE user_id=?',
        (session['user_id'],)
    ).fetchone()['c']
    conn.close()

    return render_template('dashboard.html',
                           user=user,
                           groups=groups,
                           rating_count=rating_count)


# ─────────────────────────────────────────────────────────────────────────────
# GROUPS
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/groups/create', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        name = request.form.get('group_name', '').strip()
        desc = request.form.get('description', '').strip()

        if not name:
            flash('Group name is required.', 'danger')
            return render_template('create_group.html')

        invite_code = secrets.token_hex(4).upper()
        conn = get_db()
        conn.execute('''
            INSERT INTO travel_groups
              (group_name, description, created_by, invite_code)
            VALUES (?,?,?,?)
        ''', (name, desc, session['user_id'], invite_code))
        gid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.execute('''
            INSERT INTO group_members (group_id, user_id, role)
            VALUES (?,?,'leader')
        ''', (gid, session['user_id']))
        conn.commit()
        conn.close()

        flash(f'Group "{name}" created!', 'success')
        return redirect(url_for('view_group', group_id=gid))

    return render_template('create_group.html')


@app.route('/groups/join', methods=['GET', 'POST'])
@login_required
def join_group():
    if request.method == 'POST':
        code = request.form.get('invite_code', '').strip().upper()
        conn = get_db()
        group = conn.execute(
            'SELECT * FROM travel_groups WHERE invite_code=?', (code,)
        ).fetchone()

        if not group:
            flash('Invalid invite code. Please try again.', 'danger')
            conn.close()
            return render_template('join_group.html')

        already = conn.execute(
            'SELECT id FROM group_members WHERE group_id=? AND user_id=?',
            (group['id'], session['user_id'])
        ).fetchone()

        if already:
            flash('You are already a member of this group.', 'info')
        else:
            conn.execute('''
                INSERT INTO group_members (group_id, user_id, role)
                VALUES (?,?,'member')
            ''', (group['id'], session['user_id']))
            conn.commit()
            flash(f"Joined \"{group['group_name']}\"!", 'success')
        conn.close()
        return redirect(url_for('view_group', group_id=group['id']))

    return render_template('join_group.html')


@app.route('/groups/<int:group_id>')
@login_required
def view_group(group_id):
    conn  = get_db()
    group = conn.execute(
        'SELECT * FROM travel_groups WHERE id=?', (group_id,)
    ).fetchone()

    if not group:
        flash('Group not found.', 'danger')
        conn.close()
        return redirect(url_for('dashboard'))

    members = conn.execute('''
        SELECT u.id, u.username, u.full_name, u.age, gm.role
        FROM group_members gm
        JOIN users u ON gm.user_id = u.id
        WHERE gm.group_id = ?
    ''', (group_id,)).fetchall()

    current_role = None
    for m in members:
        if m['id'] == session['user_id']:
            current_role = m['role']
            break

    if not current_role:
        flash('You are not a member of this group.', 'danger')
        conn.close()
        return redirect(url_for('dashboard'))

    constraints_set = conn.execute(
        'SELECT user_id FROM group_constraints WHERE group_id=?',
        (group_id,)
    ).fetchall()
    members_with_constraints = {r['user_id'] for r in constraints_set}

    has_constraints = session['user_id'] in members_with_constraints
    conn.close()

    return render_template('view_group.html',
                           group=group,
                           members=members,
                           current_role=current_role,
                           members_with_constraints=members_with_constraints,
                           has_constraints=has_constraints)


# ─────────────────────────────────────────────────────────────────────────────
# CONSTRAINTS
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/groups/<int:group_id>/constraints', methods=['GET', 'POST'])
@login_required
def set_constraints(group_id):
    conn  = get_db()
    group = conn.execute(
        'SELECT * FROM travel_groups WHERE id=?', (group_id,)
    ).fetchone()

    if not group:
        flash('Group not found.', 'danger')
        conn.close()
        return redirect(url_for('dashboard'))

    existing = conn.execute(
        'SELECT * FROM group_constraints WHERE group_id=? AND user_id=?',
        (group_id, session['user_id'])
    ).fetchone()

    if request.method == 'POST':
        f = request.form

        def to_int(val):
            try: return int(val) if val else None
            except: return None

        def to_float(val):
            try: return float(val) if val else None
            except: return None

        budget_min    = to_float(f.get('budget_min'))
        budget_max    = to_float(f.get('budget_max'))
        budget_delta  = to_float(f.get('budget_delta')) or 50
        duration_min  = to_int(f.get('duration_min'))
        duration_max  = to_int(f.get('duration_max'))
        flight_class  = f.get('flight_class', 'economy')
        hotel_min     = to_int(f.get('hotel_stars_min')) or 3
        hotel_max     = to_int(f.get('hotel_stars_max')) or 5
        activity_types = f.get('activity_types', '')
        travel_month  = f.get('travel_month', '')

        if existing:
            conn.execute('''
                UPDATE group_constraints SET
                  budget_min=?, budget_max=?, budget_delta=?,
                  duration_min=?, duration_max=?,
                  flight_class=?, hotel_stars_min=?, hotel_stars_max=?,
                  activity_types=?, travel_month=?
                WHERE group_id=? AND user_id=?
            ''', (budget_min, budget_max, budget_delta,
                  duration_min, duration_max,
                  flight_class, hotel_min, hotel_max,
                  activity_types, travel_month,
                  group_id, session['user_id']))
        else:
            conn.execute('''
                INSERT INTO group_constraints
                  (group_id, user_id, budget_min, budget_max, budget_delta,
                   duration_min, duration_max, flight_class,
                   hotel_stars_min, hotel_stars_max,
                   activity_types, travel_month)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (group_id, session['user_id'],
                  budget_min, budget_max, budget_delta,
                  duration_min, duration_max, flight_class,
                  hotel_min, hotel_max, activity_types, travel_month))

        conn.commit()
        conn.close()
        flash('Preferences saved!', 'success')
        return redirect(url_for('view_group', group_id=group_id))

    conn.close()
    return render_template('set_constraints.html',
                           group=group, existing=existing)


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/groups/<int:group_id>/recommend')
@login_required
def recommend(group_id):
    from recommender import run_recommendation_pipeline

    conn  = get_db()
    group = conn.execute(
        'SELECT * FROM travel_groups WHERE id=?', (group_id,)
    ).fetchone()

    if not group:
        flash('Group not found.', 'danger')
        conn.close()
        return redirect(url_for('dashboard'))

    # Check membership
    member = conn.execute(
        'SELECT id FROM group_members WHERE group_id=? AND user_id=?',
        (group_id, session['user_id'])
    ).fetchone()
    if not member:
        flash('You are not a member of this group.', 'danger')
        conn.close()
        return redirect(url_for('dashboard'))

    conn.close()

    try:
        results = run_recommendation_pipeline(group_id, top_n=10, top_m=5)
    except Exception as e:
        flash(f'Recommendation error: {str(e)}', 'danger')
        return redirect(url_for('view_group', group_id=group_id))

    return render_template('recommendations.html',
                           group=group,
                           results=results)


@app.route('/groups/<int:group_id>/itinerary/<package_id>')
@login_required
def view_itinerary(group_id, package_id):
    from recommender import (run_recommendation_pipeline,
                              get_individual_constraints,
                              merge_group_constraints)
    from itinerary import generate_itinerary, summarise_itinerary
    from package_generator import generate_packages_for_destination

    conn  = get_db()
    group = conn.execute(
        'SELECT * FROM travel_groups WHERE id=?', (group_id,)
    ).fetchone()
    conn.close()

    if not group:
        flash('Group not found.', 'danger')
        return redirect(url_for('dashboard'))

    # Re-run pipeline to find the package
    results  = run_recommendation_pipeline(group_id, top_n=10, top_m=5)
    packages = results['phase3']['final_packages']

    selected = None
    for pkg in packages:
        if pkg['package_id'] == package_id:
            selected = pkg
            break

    if not selected:
        flash('Package not found.', 'danger')
        return redirect(url_for('recommend', group_id=group_id))

    destination = selected['destination']
    itinerary   = generate_itinerary(selected, destination)
    summary     = summarise_itinerary(itinerary)

    return render_template('itinerary.html',
                           group=group,
                           package=selected,
                           destination=destination,
                           itinerary=itinerary,
                           summary=summary)


# ─────────────────────────────────────────────────────────────────────────────
# DESTINATIONS & RATINGS
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/rate-destinations', methods=['GET', 'POST'])
@login_required
def rate_destinations():
    conn = get_db()
    destinations = conn.execute('SELECT * FROM destinations ORDER BY region, name').fetchall()

    existing_ratings = {}
    rows = conn.execute(
        'SELECT destination_id, rating FROM destination_ratings WHERE user_id=?',
        (session['user_id'],)
    ).fetchall()
    for r in rows:
        existing_ratings[r['destination_id']] = r['rating']

    if request.method == 'POST':
        count = 0
        for key, val in request.form.items():
            if key.startswith('rating_') and val:
                dest_id = int(key.replace('rating_', ''))
                rating  = float(val)
                if 1 <= rating <= 5:
                    existing = conn.execute(
                        'SELECT id FROM destination_ratings WHERE user_id=? AND destination_id=?',
                        (session['user_id'], dest_id)
                    ).fetchone()
                    if existing:
                        conn.execute(
                            'UPDATE destination_ratings SET rating=? WHERE user_id=? AND destination_id=?',
                            (rating, session['user_id'], dest_id)
                        )
                    else:
                        conn.execute(
                            'INSERT INTO destination_ratings (user_id, destination_id, rating) VALUES (?,?,?)',
                            (session['user_id'], dest_id, rating)
                        )
                    count += 1
        conn.commit()
        flash(f'{count} destination ratings saved!', 'success')
        return redirect(url_for('rate_destinations'))

    conn.close()
    return render_template('rate_destinations.html',
                           destinations=destinations,
                           existing_ratings=existing_ratings)


# ─────────────────────────────────────────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/profile')
@login_required
def profile():
    user   = get_current_user()
    groups = get_user_groups(session['user_id'])

    conn = get_db()
    top_ratings = conn.execute('''
        SELECT d.name, d.country, dr.rating
        FROM destination_ratings dr
        JOIN destinations d ON dr.destination_id = d.id
        WHERE dr.user_id = ?
        ORDER BY dr.rating DESC
        LIMIT 5
    ''', (session['user_id'],)).fetchall()
    conn.close()

    return render_template('profile.html',
                           user=user,
                           groups=groups,
                           top_ratings=top_ratings)


# ─────────────────────────────────────────────────────────────────────────────
# API
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/check-username')
def check_username():
    username = request.args.get('username', '').strip()
    conn = get_db()
    exists = conn.execute(
        'SELECT id FROM users WHERE username=?', (username,)
    ).fetchone()
    conn.close()
    return jsonify({'available': exists is None})


# ─────────────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
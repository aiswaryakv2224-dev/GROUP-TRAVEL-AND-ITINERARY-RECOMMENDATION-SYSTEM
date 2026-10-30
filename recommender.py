"""
recommender.py — Core GRec_Tr Algorithm
Implements all 3 phases from the paper:
  Phase 1: CF-Based Destination Recommendation (Pearson + TLS)
  Phase 2: Group Approximate Constraint Satisfaction
  Phase 3: Individual Dissatisfaction Filtering
"""
import sqlite3
import math
from database import get_db

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1 — CF-BASED DESTINATION RECOMMENDATION
# ─────────────────────────────────────────────────────────────────────────────

def build_rating_matrix():
    """
    Build full user-destination rating matrix.
    Returns: { user_id: { dest_id: rating } }
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT user_id, destination_id, rating FROM destination_ratings"
    ).fetchall()
    conn.close()

    matrix = {}
    for row in rows:
        uid  = row['user_id']
        did  = row['destination_id']
        rate = row['rating']
        if uid not in matrix:
            matrix[uid] = {}
        matrix[uid][did] = rate
    return matrix


def build_group_profile(group_id):
    """
    Build group profile: average rating per destination
    across all group members.
    Returns: { dest_id: avg_rating }
    """
    conn = get_db()
    members = conn.execute(
        "SELECT user_id FROM group_members WHERE group_id=?",
        (group_id,)
    ).fetchall()
    member_ids = [m['user_id'] for m in members]

    if not member_ids:
        conn.close()
        return {}

    placeholders = ','.join('?' * len(member_ids))
    ratings = conn.execute(f"""
        SELECT destination_id, AVG(rating) as avg_rating
        FROM destination_ratings
        WHERE user_id IN ({placeholders})
        GROUP BY destination_id
    """, member_ids).fetchall()
    conn.close()

    return {r['destination_id']: r['avg_rating'] for r in ratings}


def get_all_group_profiles():
    """
    Get profiles for ALL groups in the system.
    Returns: { group_id: { dest_id: avg_rating } }
    """
    conn = get_db()
    groups = conn.execute("SELECT id FROM travel_groups").fetchall()
    conn.close()

    profiles = {}
    for g in groups:
        profiles[g['id']] = build_group_profile(g['id'])
    return profiles


def pearson_similarity(profile_a, profile_b):
    """
    Compute Pearson correlation coefficient between two group profiles.
    Equation (3) from the paper.
    """
    common = set(profile_a.keys()) & set(profile_b.keys())
    n = len(common)

    if n < 2:
        return 0.0

    mean_a = sum(profile_a[d] for d in common) / n
    mean_b = sum(profile_b[d] for d in common) / n

    numerator   = sum((profile_a[d] - mean_a) * (profile_b[d] - mean_b)
                      for d in common)
    denom_a     = math.sqrt(sum((profile_a[d] - mean_a) ** 2 for d in common))
    denom_b     = math.sqrt(sum((profile_b[d] - mean_b) ** 2 for d in common))
    denominator = denom_a * denom_b

    if denominator == 0:
        return 0.0

    return numerator / denominator


def find_neighbor_groups(target_group_id, all_profiles, top_k=5):
    """
    Find top-K neighbor groups most similar to target group.
    Returns: [ (group_id, similarity_score), ... ] sorted desc
    """
    target_profile = all_profiles.get(target_group_id, {})
    if not target_profile:
        return []

    similarities = []
    for gid, profile in all_profiles.items():
        if gid == target_group_id:
            continue
        sim = pearson_similarity(target_profile, profile)
        if sim > 0:
            similarities.append((gid, sim))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]


def compute_tls(target_group_id, neighbor_groups, all_profiles, top_n=10):
    """
    Compute Travel Likelihood Score (TLS) for each destination.
    Equation (4) from the paper.
    Returns: [ (dest_id, tls_score), ... ] sorted desc — Top-N
    """
    if not neighbor_groups:
        return []

    conn = get_db()
    dest_ids = [d['id'] for d in
                conn.execute("SELECT id FROM destinations").fetchall()]
    conn.close()

    target_profile = all_profiles.get(target_group_id, {})

    tls_scores = []
    for dest_id in dest_ids:
        if target_profile.get(dest_id, 0) >= 4.0:
            continue

        numerator   = 0.0
        denominator = 0.0

        for (gid, sim) in neighbor_groups:
            neighbor_profile = all_profiles.get(gid, {})
            if dest_id in neighbor_profile:
                numerator   += neighbor_profile[dest_id] * sim
                denominator += sim

        if denominator > 0:
            tls = numerator / denominator
            tls_scores.append((dest_id, round(tls, 4)))

    tls_scores.sort(key=lambda x: x[1], reverse=True)
    return tls_scores[:top_n]


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 — GROUP APPROXIMATE CONSTRAINT SATISFACTION
# ─────────────────────────────────────────────────────────────────────────────

def get_individual_constraints(group_id):
    conn = get_db()
    constraints = conn.execute("""
        SELECT gc.*, u.full_name
        FROM group_constraints gc
        JOIN users u ON gc.user_id = u.id
        WHERE gc.group_id = ?
    """, (group_id,)).fetchall()
    conn.close()
    return constraints


def merge_group_constraints(individual_constraints):
    """
    Merge individual constraints into group constraints.
    Continuous: intersection (most restrictive)
    Categorical: majority voting
    Paper Section III-C
    """
    if not individual_constraints:
        return None

    budget_maxes  = [c['budget_max']   for c in individual_constraints if c['budget_max']  is not None]
    budget_mins   = [c['budget_min']   for c in individual_constraints if c['budget_min']  is not None]
    budget_deltas = [c['budget_delta'] for c in individual_constraints if c['budget_delta'] is not None]

    group_budget_max   = min(budget_maxes)   if budget_maxes  else None
    group_budget_min   = min(budget_mins)    if budget_mins   else None
    group_budget_delta = max(budget_deltas)  if budget_deltas else 50

    dur_maxes = [c['duration_max'] for c in individual_constraints if c['duration_max'] is not None]
    dur_mins  = [c['duration_min'] for c in individual_constraints if c['duration_min'] is not None]

    group_dur_max = min(dur_maxes) if dur_maxes else None
    group_dur_min = max(dur_mins)  if dur_mins  else None

    flight_classes = [c['flight_class'] for c in individual_constraints if c['flight_class']]
    group_flight   = max(set(flight_classes), key=flight_classes.count) if flight_classes else 'economy'

    hotel_mins  = [c['hotel_stars_min'] for c in individual_constraints if c['hotel_stars_min'] is not None]
    hotel_maxes = [c['hotel_stars_max'] for c in individual_constraints if c['hotel_stars_max'] is not None]

    group_hotel_min = max(hotel_mins)  if hotel_mins  else 3
    group_hotel_max = min(hotel_maxes) if hotel_maxes else 5

    all_activities = set()
    for c in individual_constraints:
        if c['activity_types']:
            for act in c['activity_types'].split(','):
                all_activities.add(act.strip().lower())

    months      = [c['travel_month'] for c in individual_constraints if c['travel_month']]
    group_month = max(set(months), key=months.count) if months else None

    return {
        'budget_min':      group_budget_min,
        'budget_max':      group_budget_max,
        'budget_delta':    group_budget_delta,
        'duration_min':    group_dur_min,
        'duration_max':    group_dur_max,
        'flight_class':    group_flight,
        'hotel_stars_min': group_hotel_min,
        'hotel_stars_max': group_hotel_max,
        'activity_types':  list(all_activities),
        'travel_month':    group_month,
    }


def constraint_error_continuous(constraint_max, value, delta=0):
    """
    Satisfaction error for continuous constraint — Equation (5).
    e(c <= d1, θ) = max(θ - d1 - delta, 0)
    """
    if constraint_max is None:
        return 0.0
    error = max(value - constraint_max, 0)
    if error <= delta:
        return 0.0
    return error - delta


def constraint_error_categorical(constraint_val, actual_val):
    """
    Satisfaction error for categorical constraint — Equation (6).
    """
    if constraint_val is None:
        return 0.0
    return 0.0 if constraint_val == actual_val else 1.0


def score_package_against_group(package, group_constraints):
    """Score a package against group constraints. Lower = better."""
    if not group_constraints:
        return 0.0

    total_error = 0.0

    if package.get('total_cost') and group_constraints.get('budget_max'):
        total_error += constraint_error_continuous(
            group_constraints['budget_max'],
            package['total_cost'],
            group_constraints.get('budget_delta', 50)
        )

    if package.get('duration_days') and group_constraints.get('duration_max'):
        total_error += constraint_error_continuous(
            group_constraints['duration_max'],
            package['duration_days'], delta=0
        )

    if package.get('flight_class') and group_constraints.get('flight_class'):
        total_error += constraint_error_categorical(
            group_constraints['flight_class'],
            package['flight_class']
        )

    if package.get('hotel_stars') and group_constraints.get('hotel_stars_min'):
        if package['hotel_stars'] < group_constraints['hotel_stars_min']:
            total_error += group_constraints['hotel_stars_min'] - package['hotel_stars']

    return round(total_error, 4)


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3 — INDIVIDUAL DISSATISFACTION FILTERING
# ─────────────────────────────────────────────────────────────────────────────

def score_package_individual(package, individual_constraint):
    """Individual dissatisfaction error — Equation (11)."""
    total_error = 0.0

    if package.get('total_cost') and individual_constraint.get('budget_max'):
        total_error += constraint_error_continuous(
            individual_constraint['budget_max'],
            package['total_cost'], delta=0
        )

    if package.get('duration_days') and individual_constraint.get('duration_max'):
        total_error += constraint_error_continuous(
            individual_constraint['duration_max'],
            package['duration_days'], delta=0
        )

    if package.get('flight_class') and individual_constraint.get('flight_class'):
        total_error += constraint_error_categorical(
            individual_constraint['flight_class'],
            package['flight_class']
        )

    if package.get('hotel_stars') and individual_constraint.get('hotel_stars_min'):
        if package['hotel_stars'] < individual_constraint['hotel_stars_min']:
            total_error += individual_constraint['hotel_stars_min'] - package['hotel_stars']

    return round(total_error, 4)


def filter_by_individual_satisfaction(packages, individual_constraints, top_m=5):
    """
    Phase 3: Remove packages causing high dissatisfaction for any member.
    Returns top-M packages.
    """
    if not packages or not individual_constraints:
        return packages[:top_m]

    scored = []
    for pkg in packages:
        individual_errors = [
            score_package_individual(pkg, dict(c))
            for c in individual_constraints
        ]
        max_err = max(individual_errors) if individual_errors else 0
        avg_err = sum(individual_errors) / len(individual_errors) if individual_errors else 0

        scored.append({
            **pkg,
            'max_individual_error': max_err,
            'avg_individual_error': round(avg_err, 4),
            'individual_errors':    individual_errors,
        })

    scored.sort(key=lambda x: (x['max_individual_error'],
                                x['avg_individual_error'],
                                x['group_error']))
    return scored[:top_m]


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def run_recommendation_pipeline(group_id, top_n=10, top_m=5):
    """
    Full GRec_Tr pipeline — Phase 1 → Phase 2 → Phase 3
    Returns final recommended packages with destination info.
    """
    from package_generator import generate_packages_for_destination

    conn = get_db()

    # Phase 1
    all_profiles    = get_all_group_profiles()
    neighbor_groups = find_neighbor_groups(group_id, all_profiles, top_k=8)
    tls_scores      = compute_tls(group_id, neighbor_groups, all_profiles, top_n=top_n)

    if not tls_scores:
        top_dests  = conn.execute("""
            SELECT destination_id, AVG(rating) as avg_r
            FROM destination_ratings
            GROUP BY destination_id
            ORDER BY avg_r DESC LIMIT ?
        """, (top_n,)).fetchall()
        tls_scores = [(r['destination_id'], r['avg_r']) for r in top_dests]

    dest_ids = [d[0] for d in tls_scores]
    tls_map  = {d[0]: d[1] for d in tls_scores}

    placeholders = ','.join('?' * len(dest_ids))
    destinations = conn.execute(
        f"SELECT * FROM destinations WHERE id IN ({placeholders})", dest_ids
    ).fetchall()
    conn.close()

    # Phase 2
    individual_constraints = get_individual_constraints(group_id)
    group_constraints      = merge_group_constraints(individual_constraints)

    all_candidates = []
    for dest in destinations:
        packages = generate_packages_for_destination(dest, group_constraints)
        for pkg in packages:
            pkg['destination'] = dict(dest)
            pkg['tls_score']   = tls_map.get(dest['id'], 0)
            pkg['group_error'] = score_package_against_group(pkg, group_constraints)
        all_candidates.extend(packages)

    all_candidates.sort(key=lambda x: (x['group_error'], -x['tls_score']))

    # Phase 3
    final_packages = filter_by_individual_satisfaction(
        all_candidates, individual_constraints, top_m=top_m
    )

    return {
        'phase1': {
            'neighbor_groups': neighbor_groups,
            'tls_scores':      tls_scores,
            'destinations':    [dict(d) for d in destinations],
        },
        'phase2': {
            'group_constraints': group_constraints,
            'candidate_count':   len(all_candidates),
        },
        'phase3': {
            'final_packages':          final_packages,
            'individual_constraints':  [dict(c) for c in individual_constraints],
        },
        'summary': {
            'top_n_destinations': len(destinations),
            'top_m_packages':     len(final_packages),
            'group_id':           group_id,
        }
    }
"""
package_generator.py — Generates realistic travel packages
for each recommended destination based on group constraints.
Each destination gets multiple package variants (budget/mid/luxury).
"""
import random

# Flight class cost multipliers
FLIGHT_MULTIPLIERS = {
    'economy':  1.0,
    'premium':  1.6,
    'business': 2.8,
    'first':    4.5,
}

# Hotel cost per night by star rating
HOTEL_NIGHTLY = {
    1: 25,
    2: 50,
    3: 90,
    4: 160,
    5: 320,
}

# Base flight costs FROM a generic origin (USD, one-way)
BASE_FLIGHT_COST = {
    'East Asia':     420,
    'Southeast Asia':380,
    'South Asia':    310,
}

# Activity cost per day by type
ACTIVITY_COSTS = {
    'beach':       30,
    'culture':     25,
    'food':        40,
    'adventure':   60,
    'nature':      35,
    'shopping':    80,
    'nightlife':   55,
    'wellness':    70,
    'history':     20,
    'diving':      90,
    'trekking':    50,
    'luxury':     150,
    'relaxation':  20,
    'water_sports':75,
    'temples':     15,
    'skiing':      85,
    'boat':        45,
    'art':         25,
    'romance':     60,
    'surfing':     65,
    'city':        35,
}

PACKAGE_TIERS = [
    {'label': 'Budget',  'hotel_stars': 3, 'dur_days': 6,  'flight': 'economy'},
    {'label': 'Mid',     'hotel_stars': 4, 'dur_days': 8,  'flight': 'economy'},
    {'label': 'Comfort', 'hotel_stars': 4, 'dur_days': 8,  'flight': 'premium'},
    {'label': 'Luxury',  'hotel_stars': 5, 'dur_days': 10, 'flight': 'business'},
]


def estimate_activity_cost(tags_str, duration_days):
    """Estimate total activity cost based on destination tags."""
    if not tags_str:
        return duration_days * 35  # default fallback

    tags = [t.strip().lower() for t in tags_str.split(',')]
    daily = sum(ACTIVITY_COSTS.get(t, 30) for t in tags) / max(len(tags), 1)
    return round(daily * duration_days)


def generate_packages_for_destination(dest, group_constraints=None):
    """
    Generate multiple travel package variants for a destination.
    Applies group constraints to adjust package parameters.
    Returns: list of package dicts
    """
    dest = dict(dest)
    region = dest.get('region', 'Southeast Asia')
    base_flight = BASE_FLIGHT_COST.get(region, 380)
    tags_str    = dest.get('tags', '')

    # Determine which tiers to generate based on constraints
    tiers = PACKAGE_TIERS.copy()

    if group_constraints:
        hotel_min = group_constraints.get('hotel_stars_min', 1)
        hotel_max = group_constraints.get('hotel_stars_max', 5)
        fc        = group_constraints.get('flight_class', None)
        dur_min   = group_constraints.get('duration_min', None)
        dur_max   = group_constraints.get('duration_max', None)

        # Filter tiers by hotel stars
        tiers = [t for t in tiers
                 if hotel_min <= t['hotel_stars'] <= hotel_max]

        # Override flight class if specified
        if fc:
            for t in tiers:
                t = dict(t)
                t['flight'] = fc

        # Adjust duration to fit constraints
        if dur_min or dur_max:
            for t in tiers:
                if dur_min and t['dur_days'] < dur_min:
                    t['dur_days'] = dur_min
                if dur_max and t['dur_days'] > dur_max:
                    t['dur_days'] = dur_max

        # If no tiers passed hotel filter, use fallback
        if not tiers:
            tiers = [{
                'label':       'Custom',
                'hotel_stars': max(hotel_min, 3),
                'dur_days':    dur_min or 7,
                'flight':      fc or 'economy',
            }]

    packages = []
    for tier in tiers:
        hotel_stars  = tier['hotel_stars']
        dur_days     = tier['dur_days']
        flight_class = tier['flight']
        multiplier   = FLIGHT_MULTIPLIERS.get(flight_class, 1.0)

        flight_cost   = round(base_flight * multiplier * 2)  # return trip
        hotel_cost    = round(HOTEL_NIGHTLY[hotel_stars] * dur_days)
        activity_cost = estimate_activity_cost(tags_str, dur_days)
        misc_cost     = round(dur_days * 15)  # transport/food/misc
        total_cost    = flight_cost + hotel_cost + activity_cost + misc_cost

        # Apply budget constraint if present
        if (group_constraints and
                group_constraints.get('budget_max') and
                total_cost > group_constraints['budget_max'] * 1.5):
            continue  # Too expensive even with delta

        # Build activity list from tags
        tag_list = [t.strip() for t in tags_str.split(',') if t.strip()]
        activities = []
        for tag in tag_list[:5]:
            cost = ACTIVITY_COSTS.get(tag.lower(), 30)
            activities.append({
                'name':     tag.replace('_', ' ').title(),
                'cost':     cost,
                'duration': '2-3 hours',
            })

        package = {
            'package_id':    f"{dest['id']}_{tier['label'].lower()}",
            'tier':          tier['label'],
            'destination_id': dest['id'],
            'flight_class':  flight_class,
            'hotel_stars':   hotel_stars,
            'duration_days': dur_days,
            'flight_cost':   flight_cost,
            'hotel_cost':    hotel_cost,
            'activity_cost': activity_cost,
            'misc_cost':     misc_cost,
            'total_cost':    total_cost,
            'activities':    activities,
            'best_season':   dest.get('best_season', 'Year-round'),
            'avg_temp':      dest.get('avg_temp', 25),
        }
        packages.append(package)

    return packages
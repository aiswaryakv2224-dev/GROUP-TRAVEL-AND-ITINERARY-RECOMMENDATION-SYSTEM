"""
itinerary.py — Day-by-day itinerary generator (Enhancement 1)
Generates a structured travel plan for a recommended package.
This is an enhancement beyond the base paper.
"""

# Activity templates per tag type
ACTIVITY_TEMPLATES = {
    'beach': [
        {'time': '07:00', 'activity': 'Morning beach walk & sunrise',         'duration': '1.5h', 'cost': 0},
        {'time': '10:00', 'activity': 'Swimming & snorkelling',               'duration': '2h',   'cost': 25},
        {'time': '15:00', 'activity': 'Beach volleyball & water sports',      'duration': '2h',   'cost': 30},
        {'time': '18:00', 'activity': 'Sunset beachside dinner',              'duration': '1.5h', 'cost': 35},
    ],
    'culture': [
        {'time': '09:00', 'activity': 'Local museum or cultural centre visit','duration': '2h',   'cost': 15},
        {'time': '11:30', 'activity': 'Traditional craft workshop',           'duration': '1.5h', 'cost': 20},
        {'time': '14:00', 'activity': 'Historic district walking tour',       'duration': '2h',   'cost': 10},
        {'time': '19:00', 'activity': 'Traditional cultural performance',     'duration': '2h',   'cost': 30},
    ],
    'food': [
        {'time': '08:00', 'activity': 'Local breakfast at street market',     'duration': '1h',   'cost': 8},
        {'time': '11:00', 'activity': 'Cooking class with local chef',        'duration': '3h',   'cost': 45},
        {'time': '15:00', 'activity': 'Street food tour',                     'duration': '2h',   'cost': 20},
        {'time': '19:30', 'activity': 'Dinner at renowned local restaurant',  'duration': '2h',   'cost': 40},
    ],
    'adventure': [
        {'time': '06:30', 'activity': 'Early morning trek or hike',           'duration': '3h',   'cost': 30},
        {'time': '10:30', 'activity': 'Rock climbing or zip-lining',          'duration': '2h',   'cost': 50},
        {'time': '14:00', 'activity': 'Kayaking or river rafting',            'duration': '2.5h', 'cost': 45},
        {'time': '18:00', 'activity': 'Campfire & adventure debrief',         'duration': '1.5h', 'cost': 10},
    ],
    'nature': [
        {'time': '07:00', 'activity': 'Sunrise nature walk / birdwatching',   'duration': '2h',   'cost': 10},
        {'time': '10:00', 'activity': 'National park or nature reserve tour', 'duration': '3h',   'cost': 25},
        {'time': '14:00', 'activity': 'Waterfall or scenic viewpoint visit',  'duration': '2h',   'cost': 10},
        {'time': '17:00', 'activity': 'Sunset at scenic overlook',            'duration': '1h',   'cost': 0},
    ],
    'history': [
        {'time': '09:00', 'activity': 'Ancient ruins or heritage site visit', 'duration': '2.5h', 'cost': 20},
        {'time': '12:00', 'activity': 'Historical museum tour',               'duration': '2h',   'cost': 15},
        {'time': '15:00', 'activity': 'Guided history walking tour',          'duration': '2h',   'cost': 18},
        {'time': '19:00', 'activity': 'Dinner at heritage restaurant',        'duration': '1.5h', 'cost': 35},
    ],
    'shopping': [
        {'time': '10:00', 'activity': 'Local market & bazaar exploration',    'duration': '2h',   'cost': 50},
        {'time': '13:00', 'activity': 'Souvenir & handicraft shopping',       'duration': '1.5h', 'cost': 40},
        {'time': '15:30', 'activity': 'Modern mall or boutique district',     'duration': '2h',   'cost': 60},
        {'time': '19:00', 'activity': 'Night market tour',                    'duration': '2h',   'cost': 25},
    ],
    'wellness': [
        {'time': '07:00', 'activity': 'Morning yoga or meditation session',   'duration': '1.5h', 'cost': 20},
        {'time': '10:00', 'activity': 'Traditional spa & massage treatment',  'duration': '2h',   'cost': 60},
        {'time': '13:00', 'activity': 'Healthy local cuisine lunch',          'duration': '1h',   'cost': 20},
        {'time': '16:00', 'activity': 'Wellness workshop or hot springs',     'duration': '2h',   'cost': 40},
    ],
    'nightlife': [
        {'time': '18:00', 'activity': 'Rooftop bar & cocktails',              'duration': '2h',   'cost': 40},
        {'time': '20:30', 'activity': 'Dinner at trendy restaurant',          'duration': '1.5h', 'cost': 50},
        {'time': '22:30', 'activity': 'Live music venue or club',             'duration': '2h',   'cost': 30},
    ],
    'temples': [
        {'time': '07:00', 'activity': 'Early morning temple visit (peaceful)','duration': '2h',   'cost': 5},
        {'time': '10:00', 'activity': 'Temple complex guided tour',           'duration': '2.5h', 'cost': 15},
        {'time': '15:00', 'activity': 'Sunset temple ceremony',              'duration': '1.5h', 'cost': 5},
        {'time': '17:30', 'activity': 'Offerings & local ritual observation', 'duration': '1h',   'cost': 0},
    ],
    'diving': [
        {'time': '07:00', 'activity': 'Equipment briefing & boat ride',       'duration': '1h',   'cost': 20},
        {'time': '08:30', 'activity': 'Morning dive at reef site',            'duration': '2.5h', 'cost': 60},
        {'time': '12:00', 'activity': 'Lunch break & gear check',             'duration': '1.5h', 'cost': 15},
        {'time': '14:00', 'activity': 'Afternoon dive at deeper site',        'duration': '2.5h', 'cost': 60},
    ],
    'trekking': [
        {'time': '06:00', 'activity': 'Pre-trek breakfast & gear up',         'duration': '1h',   'cost': 10},
        {'time': '07:00', 'activity': 'Main trek to summit or viewpoint',     'duration': '4h',   'cost': 35},
        {'time': '12:00', 'activity': 'Summit lunch & panoramic views',       'duration': '1h',   'cost': 15},
        {'time': '13:30', 'activity': 'Descent & nature photography',         'duration': '3h',   'cost': 0},
    ],
}

DEFAULT_ACTIVITIES = [
    {'time': '09:00', 'activity': 'Morning city exploration',                 'duration': '2h',   'cost': 10},
    {'time': '12:00', 'activity': 'Local lunch experience',                   'duration': '1h',   'cost': 15},
    {'time': '14:00', 'activity': 'Afternoon sightseeing',                    'duration': '3h',   'cost': 20},
    {'time': '18:00', 'activity': 'Evening relaxation & dinner',              'duration': '2h',   'cost': 30},
]

ARRIVAL_DAY = [
    {'time': '14:00', 'activity': 'Arrive & check in to hotel',              'duration': '1h',   'cost': 0},
    {'time': '16:00', 'activity': 'Orientation walk around neighbourhood',   'duration': '1.5h', 'cost': 0},
    {'time': '18:30', 'activity': 'Welcome dinner at local restaurant',      'duration': '2h',   'cost': 35},
]

DEPARTURE_DAY = [
    {'time': '07:00', 'activity': 'Final breakfast & souvenir shopping',     'duration': '2h',   'cost': 20},
    {'time': '10:00', 'activity': 'Hotel checkout & luggage storage',        'duration': '0.5h', 'cost': 0},
    {'time': '11:00', 'activity': 'Last sightseeing or relaxation',          'duration': '2h',   'cost': 10},
    {'time': '14:00', 'activity': 'Transfer to airport & departure',         'duration': '2h',   'cost': 0},
]


def get_activities_for_tags(tags_str, day_index):
    """
    Pick appropriate activities based on destination tags.
    Rotates through tag types across days for variety.
    """
    if not tags_str:
        return DEFAULT_ACTIVITIES

    tags = [t.strip().lower() for t in tags_str.split(',') if t.strip()]
    available_tags = [t for t in tags if t in ACTIVITY_TEMPLATES]

    if not available_tags:
        return DEFAULT_ACTIVITIES

    # Rotate through tags across days
    selected_tag = available_tags[day_index % len(available_tags)]
    return ACTIVITY_TEMPLATES[selected_tag]


def generate_itinerary(package, destination):
    """
    Generate a full day-by-day itinerary for a travel package.
    Enhancement beyond base paper — adds practical travel planning.

    Args:
        package:     dict from package_generator
        destination: dict with name, country, tags, etc.

    Returns:
        list of day dicts: [
          { 'day': 1, 'title': '...', 'activities': [...], 'daily_cost': ... }
        ]
    """
    duration  = package.get('duration_days', 7)
    tags_str  = destination.get('tags', '')
    dest_name = destination.get('name', 'Destination')
    itinerary = []

    for day_num in range(1, duration + 1):

        # Day 1 — Arrival
        if day_num == 1:
            day = {
                'day':        1,
                'title':      f'Arrival in {dest_name}',
                'theme':      'Arrival & Orientation',
                'activities': ARRIVAL_DAY,
                'daily_cost': sum(a['cost'] for a in ARRIVAL_DAY),
                'notes':      'Take it easy today — jet lag is real!',
            }

        # Last day — Departure
        elif day_num == duration:
            day = {
                'day':        day_num,
                'title':      f'Farewell {dest_name}',
                'theme':      'Departure Day',
                'activities': DEPARTURE_DAY,
                'daily_cost': sum(a['cost'] for a in DEPARTURE_DAY),
                'notes':      'Check flight time and allow extra time at airport.',
            }

        # Middle days — Themed activities
        else:
            acts  = get_activities_for_tags(tags_str, day_num - 2)
            tags  = [t.strip().lower() for t in tags_str.split(',') if t.strip()]
            avail = [t for t in tags if t in ACTIVITY_TEMPLATES]
            theme = avail[(day_num - 2) % len(avail)].title() if avail else 'Exploration'

            day = {
                'day':        day_num,
                'title':      f'Day {day_num} — {theme} Day',
                'theme':      theme,
                'activities': acts,
                'daily_cost': sum(a['cost'] for a in acts),
                'notes':      _get_day_tip(theme.lower(), dest_name),
            }

        itinerary.append(day)

    return itinerary


def _get_day_tip(theme, dest_name):
    """Return a helpful travel tip for the day's theme."""
    tips = {
        'beach':     'Apply sunscreen early and stay hydrated throughout the day.',
        'culture':   'Dress modestly when visiting religious or heritage sites.',
        'food':      'Try the local street food — it is often the most authentic.',
        'adventure': 'Wear comfortable shoes and bring a rain jacket just in case.',
        'nature':    'Start early to avoid crowds and catch the best light.',
        'history':   'Hire a local guide — their stories bring history alive.',
        'shopping':  'Bargaining is expected at local markets — be respectful.',
        'wellness':  'Book spa treatments in advance, especially on weekends.',
        'nightlife': 'Use reputable transport apps when travelling late at night.',
        'temples':   'Remove shoes before entering and speak softly inside.',
        'diving':    'Stay hydrated and avoid alcohol 12 hours before diving.',
        'trekking':  'Bring enough water — at least 2L per person for full day.',
    }
    return tips.get(theme, f'Enjoy every moment in {dest_name}!')


def summarise_itinerary(itinerary):
    """
    Return a summary of the full itinerary.
    Total cost, total activities, highlights.
    """
    total_cost       = sum(d['daily_cost'] for d in itinerary)
    total_activities = sum(len(d['activities']) for d in itinerary)
    highlights       = [d['title'] for d in itinerary
                        if d['theme'] not in ('Arrival & Orientation',
                                               'Departure Day')]
    return {
        'total_days':       len(itinerary),
        'total_cost':       total_cost,
        'total_activities': total_activities,
        'highlights':       highlights[:5],
    }
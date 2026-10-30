"""
seed_data.py — Populates the database with:
  - 53 Asian travel destinations (matching the paper's dataset)
  - 20 sample users with destination ratings
  - 4 sample travel groups
"""
import sqlite3, random, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from database import get_db, hash_password, init_db

DESTINATIONS = [
    ("Tokyo",        "Japan",       "East Asia",    "Bustling metropolis with ancient temples and cutting-edge technology.",        "🗼", 15.4, "Spring/Autumn", "city,culture,food,shopping"),
    ("Kyoto",        "Japan",       "East Asia",    "Japan's cultural heart with over 1,600 Buddhist temples.",                     "⛩️", 14.8, "Spring/Autumn", "culture,temples,history,nature"),
    ("Osaka",        "Japan",       "East Asia",    "Japan's kitchen — famous for street food, nightlife, and Dotonbori.",          "🏯", 16.2, "Spring/Autumn", "food,nightlife,shopping,culture"),
    ("Hokkaido",     "Japan",       "East Asia",    "Scenic island known for ski resorts, lavender fields, and seafood.",           "🌸", 6.5,  "Winter/Summer", "nature,skiing,food,adventure"),
    ("Nara",         "Japan",       "East Asia",    "Ancient capital with free-roaming deer and Todai-ji temple.",                  "🦌", 14.0, "Spring/Autumn", "culture,nature,temples,history"),
    ("Seoul",        "South Korea", "East Asia",    "Dynamic capital blending K-pop culture, palaces, and street food.",            "🌆", 12.5, "Spring/Autumn", "city,culture,food,shopping,nightlife"),
    ("Busan",        "South Korea", "East Asia",    "Coastal city famous for beaches, seafood, and colorful Gamcheon village.",     "🏖️", 14.6, "Summer",        "beach,food,culture,nature"),
    ("Jeju Island",  "South Korea", "East Asia",    "Volcanic island with waterfalls, lava tubes, and stunning coastlines.",        "🌋", 16.2, "Spring/Summer", "nature,beach,adventure,culture"),
    ("Gyeongju",     "South Korea", "East Asia",    "Open-air museum of the ancient Silla Kingdom.",                               "🏛️", 13.0, "Spring/Autumn", "history,culture,temples"),
    ("Beijing",      "China",       "East Asia",    "China's capital with the Forbidden City and Great Wall.",                     "🏯", 11.8, "Spring/Autumn", "history,culture,city,food"),
    ("Shanghai",     "China",       "East Asia",    "Global financial hub with Art Deco architecture and vibrant nightlife.",       "🌃", 16.0, "Spring/Autumn", "city,shopping,food,nightlife"),
    ("Xi'an",        "China",       "East Asia",    "Home of the Terracotta Warriors and ancient Silk Road culture.",               "🏺", 13.3, "Spring/Autumn", "history,culture,food"),
    ("Guilin",       "China",       "East Asia",    "Karst mountain landscape along the Li River — one of China's most scenic.",   "⛰️", 18.9, "Spring/Autumn", "nature,scenery,culture"),
    ("Chengdu",      "China",       "East Asia",    "Panda base, spicy Sichuan cuisine, and a laid-back teahouse culture.",        "🐼", 16.2, "Spring/Autumn", "nature,food,culture,city"),
    ("Bangkok",      "Thailand",    "Southeast Asia","Vibrant capital with ornate temples, street food, and buzzing nightlife.",    "🛕", 28.6, "Winter",        "city,culture,food,shopping,nightlife"),
    ("Chiang Mai",   "Thailand",    "Southeast Asia","Northern Thailand's cultural capital with night markets and temples.",        "🌿", 25.3, "Winter",        "culture,food,nature,adventure"),
    ("Phuket",       "Thailand",    "Southeast Asia","Tropical island with turquoise waters, white beaches, and beach clubs.",      "🏝️", 27.8, "Winter",        "beach,nightlife,water_sports,food"),
    ("Krabi",        "Thailand",    "Southeast Asia","Dramatic limestone cliffs, emerald lagoons, and island-hopping paradise.",    "🧗", 27.5, "Winter",        "beach,adventure,nature,water_sports"),
    ("Koh Samui",    "Thailand",    "Southeast Asia","Tropical island known for coconut palms, luxury resorts, and nightlife.",     "🥥", 27.9, "Summer",        "beach,luxury,nightlife,relaxation"),
    ("Hanoi",        "Vietnam",     "Southeast Asia","Vietnam's capital with French colonial charm and vibrant street life.",       "🏮", 23.2, "Autumn/Spring", "culture,food,history,city"),
    ("Ho Chi Minh City","Vietnam",  "Southeast Asia","Fast-paced southern city with war history, rooftop bars, and street food.",   "🛵", 27.5, "Winter",        "city,food,history,nightlife"),
    ("Ha Long Bay",  "Vietnam",     "Southeast Asia","UNESCO World Heritage site with thousands of limestone karsts.",              "⛵", 20.3, "Spring/Autumn", "nature,scenery,boat,adventure"),
    ("Hoi An",       "Vietnam",     "Southeast Asia","Lantern-lit ancient town with tailor shops and riverside restaurants.",       "🏮", 25.6, "Spring",        "culture,food,history,shopping"),
    ("Da Nang",      "Vietnam",     "Southeast Asia","Coastal city with pristine beaches and the iconic Dragon Bridge.",            "🐉", 25.7, "Summer",        "beach,city,food,culture"),
    ("Singapore",    "Singapore",   "Southeast Asia","Ultra-modern city-state with Gardens by the Bay and hawker centres.",        "🌴", 27.0, "Year-round",    "city,food,shopping,luxury,culture"),
    ("Kuala Lumpur", "Malaysia",    "Southeast Asia","Dynamic capital with Petronas Towers, street food, and diverse culture.",     "🗼", 27.7, "Year-round",    "city,shopping,food,culture"),
    ("Penang",       "Malaysia",    "Southeast Asia","UNESCO heritage town famous for street art and world-class street food.",     "🎨", 27.2, "Year-round",    "food,culture,history,art"),
    ("Langkawi",     "Malaysia",    "Southeast Asia","Archipelago of 99 islands with beaches, duty-free shopping, and nature.",     "🏝️", 27.5, "Winter",        "beach,nature,relaxation,shopping"),
    ("Bali",         "Indonesia",   "Southeast Asia","Island of the Gods with rice terraces, temples, yoga, and surf.",             "🌺", 26.5, "Dry Season",    "culture,beach,nature,wellness,surfing"),
    ("Jakarta",      "Indonesia",   "Southeast Asia","Indonesia's mega-capital with vibrant nightlife and cultural museums.",       "🌆", 27.2, "Dry Season",    "city,food,shopping,nightlife"),
    ("Yogyakarta",   "Indonesia",   "Southeast Asia","Cultural heart of Java with Borobudur and Prambanan temples.",                "🏛️", 26.8, "Dry Season",    "culture,history,temples,art"),
    ("Lombok",       "Indonesia",   "Southeast Asia","Quieter alternative to Bali with Mount Rinjani and pristine beaches.",        "🌊", 26.2, "Dry Season",    "nature,beach,adventure,trekking"),
    ("Manila",       "Philippines", "Southeast Asia","Historic capital with Intramuros, malls, and vibrant food scene.",            "🌊", 27.9, "Winter",        "city,history,food,shopping"),
    ("Palawan",      "Philippines", "Southeast Asia","Pristine beaches, crystal lagoons, and the world's best island.",             "🏝️", 27.4, "Winter",        "beach,nature,diving,adventure"),
    ("Cebu",         "Philippines", "Southeast Asia","Whale shark watching, historic churches, and beautiful beaches.",             "🐋", 28.2, "Winter",        "beach,diving,culture,nature"),
    ("Siem Reap",    "Cambodia",    "Southeast Asia","Gateway to Angkor Wat, the largest religious monument in the world.",         "🏛️", 27.4, "Winter",        "history,culture,temples,adventure"),
    ("Phnom Penh",   "Cambodia",    "Southeast Asia","Capital city with Royal Palace, National Museum, and riverside cafes.",       "🏯", 27.8, "Winter",        "history,culture,food,city"),
    ("Bagan",        "Myanmar",     "Southeast Asia","Ancient city with over 2,000 Buddhist temples on a vast plain.",              "🏯", 25.4, "Winter",        "history,culture,temples,adventure"),
    ("Yangon",       "Myanmar",     "Southeast Asia","Former capital with gilded Shwedagon Pagoda and colonial architecture.",      "🌟", 26.5, "Winter",        "culture,history,food,city"),
    ("Kathmandu",    "Nepal",       "South Asia",   "Himalayan gateway with ancient Durbar Squares and trekking culture.",         "⛰️", 13.8, "Spring/Autumn", "culture,trekking,history,adventure"),
    ("Pokhara",      "Nepal",       "South Asia",   "Lakeside city with paragliding, Annapurna views, and peaceful vibe.",         "🏔️", 17.2, "Spring/Autumn", "adventure,nature,trekking,relaxation"),
    ("Colombo",      "Sri Lanka",   "South Asia",   "Sri Lanka's commercial capital with colonial architecture and street food.",   "🌴", 27.4, "Year-round",    "city,food,culture,shopping"),
    ("Kandy",        "Sri Lanka",   "South Asia",   "Cultural triangle city with the Temple of the Tooth and tea estates.",        "🍵", 23.5, "Year-round",    "culture,nature,history,food"),
    ("Galle",        "Sri Lanka",   "South Asia",   "Dutch-built fort city with boutique hotels, beaches, and whale watching.",    "🏰", 26.8, "Winter",        "history,beach,culture,luxury"),
    ("Goa",          "India",       "South Asia",   "India's beach paradise with Portuguese heritage, beach parties, and seafood.", "🎉", 27.2, "Winter",        "beach,nightlife,culture,food"),
    ("Jaipur",       "India",       "South Asia",   "Pink City with majestic forts, palaces, and vibrant bazaars.",                 "🏯", 22.9, "Winter",        "history,culture,shopping,food"),
    ("Kerala",       "India",       "South Asia",   "Backwaters, ayurveda, tea plantations, and pristine beaches.",                 "🌿", 26.5, "Winter",        "nature,wellness,culture,beach"),
    ("Agra",         "India",       "South Asia",   "Home of the Taj Mahal — one of the world's most iconic monuments.",           "🕌", 22.1, "Winter",        "history,culture,romance"),
    ("Taipei",       "Taiwan",      "East Asia",    "Night markets, hot springs, Jiufen village, and bubble tea culture.",         "🧋", 22.0, "Spring/Autumn", "city,food,culture,shopping,nature"),
    ("Hong Kong",    "Hong Kong",   "East Asia",    "World-class shopping, dim sum, and stunning Victoria Harbour skyline.",       "🌃", 22.8, "Autumn/Spring", "city,shopping,food,nightlife,culture"),
    ("Macau",        "Macau",       "East Asia",    "Former Portuguese colony with casinos, egg tarts, and historic churches.",     "🎰", 22.3, "Autumn/Spring", "culture,food,entertainment,history"),
    ("Maldives",     "Maldives",    "South Asia",   "Overwater bungalows, crystal lagoons, and world-class diving.",               "🐠", 28.2, "Winter",        "beach,luxury,diving,romance,relaxation"),
    ("Ulaanbaatar",  "Mongolia",    "East Asia",    "Gateway to the Mongolian steppe, Genghis Khan sites, and nomadic culture.",   "🐎", 0.4,  "Summer",        "adventure,culture,nature,history"),
]

SAMPLE_USERS = [
    ("alice_wonder",  "alice@example.com",  "Alice Johnson",   28),
    ("bob_traveler",  "bob@example.com",    "Bob Smith",       34),
    ("carol_trips",   "carol@example.com",  "Carol Lee",       25),
    ("david_globe",   "david@example.com",  "David Park",      42),
    ("eva_explorer",  "eva@example.com",    "Eva Chen",        30),
    ("frank_wander",  "frank@example.com",  "Frank Kim",       38),
    ("grace_roam",    "grace@example.com",  "Grace Wang",      27),
    ("henry_voyage",  "henry@example.com",  "Henry Tanaka",    45),
    ("iris_journey",  "iris@example.com",   "Iris Patel",      31),
    ("james_trek",    "james@example.com",  "James Nguyen",    29),
    ("karen_nomad",   "karen@example.com",  "Karen Yamamoto",  36),
    ("leo_pilgrim",   "leo@example.com",    "Leo Santos",      33),
    ("mia_escape",    "mia@example.com",    "Mia Choi",        24),
    ("noah_drift",    "noah@example.com",   "Noah Sharma",     40),
    ("olivia_roam",   "olivia@example.com", "Olivia Martinez", 26),
    ("peter_venture", "peter@example.com",  "Peter Tanaka",    52),
    ("quinn_seeks",   "quinn@example.com",  "Quinn Liu",       35),
    ("rosa_wander",   "rosa@example.com",   "Rosa Singh",      29),
    ("sam_discover",  "sam@example.com",    "Sam Brown",       44),
    ("tina_explore",  "tina@example.com",   "Tina Zhang",      32),
]

def seed():
    init_db()
    conn = get_db()
    c = conn.cursor()

    c.execute("DELETE FROM destination_ratings")
    c.execute("DELETE FROM group_members")
    c.execute("DELETE FROM travel_groups")
    c.execute("DELETE FROM users WHERE username != 'admin'")
    c.execute("DELETE FROM destinations")

    for d in DESTINATIONS:
        c.execute("""
            INSERT INTO destinations (name, country, region, description, image_url, avg_temp, best_season, tags)
            VALUES (?,?,?,?,?,?,?,?)
        """, d)

    dest_ids = [r[0] for r in c.execute("SELECT id FROM destinations").fetchall()]

    pw = hash_password("password123")
    user_ids = []
    for uname, email, full_name, age in SAMPLE_USERS:
        try:
            c.execute("""
                INSERT INTO users (username, email, password, full_name, age)
                VALUES (?,?,?,?,?)
            """, (uname, email, pw, full_name, age))
            user_ids.append(c.lastrowid)
        except Exception:
            uid = c.execute("SELECT id FROM users WHERE username=?", (uname,)).fetchone()[0]
            user_ids.append(uid)

    random.seed(42)
    for uid in user_ids:
        sampled = random.sample(dest_ids, random.randint(20, 35))
        for did in sampled:
            rating = round(random.gauss(3.5, 0.8), 1)
            rating = max(1.0, min(5.0, rating))
            try:
                c.execute("""
                    INSERT INTO destination_ratings (user_id, destination_id, rating)
                    VALUES (?,?,?)
                """, (uid, did, rating))
            except Exception:
                pass

    import secrets as sec
    groups = [
        ("Friends Beach Trip",  "5 college friends planning a summer beach vacation in Southeast Asia.", user_ids[0]),
        ("Family Asia Tour",    "Family of 4 exploring East Asian cultural destinations.",               user_ids[3]),
        ("Backpacker Squad",    "Budget adventurers seeking off-the-beaten-path experiences.",           user_ids[6]),
        ("Couples Retreat",     "Two couples looking for a romantic luxury getaway.",                    user_ids[9]),
    ]
    for gname, gdesc, gcreator in groups:
        code = sec.token_hex(4).upper()
        c.execute("""
            INSERT INTO travel_groups (group_name, description, created_by, invite_code)
            VALUES (?,?,?,?)
        """, (gname, gdesc, gcreator, code))
        gid = c.lastrowid
        c.execute("INSERT INTO group_members (group_id, user_id, role) VALUES (?,?,'leader')", (gid, gcreator))
        others = random.sample([u for u in user_ids if u != gcreator], 3)
        for ou in others:
            c.execute("INSERT OR IGNORE INTO group_members (group_id, user_id, role) VALUES (?,?,'member')", (gid, ou))

    conn.commit()
    conn.close()
    print(f"[SEED] {len(DESTINATIONS)} destinations, {len(SAMPLE_USERS)} users, 4 groups inserted.")

if __name__ == "__main__":
    seed()
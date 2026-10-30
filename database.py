import sqlite3
import os
import hashlib
import secrets

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'grec_tr.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split(":")
        return hashlib.sha256((salt + password).encode()).hexdigest() == hashed
    except Exception:
        return False

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            full_name   TEXT    NOT NULL,
            age         INTEGER,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel_groups (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name   TEXT    NOT NULL,
            description  TEXT,
            created_by   INTEGER NOT NULL REFERENCES users(id),
            invite_code  TEXT    NOT NULL UNIQUE,
            status       TEXT    DEFAULT 'planning',
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id   INTEGER NOT NULL REFERENCES travel_groups(id),
            user_id    INTEGER NOT NULL REFERENCES users(id),
            role       TEXT    DEFAULT 'member',
            joined_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(group_id, user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS destinations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            country     TEXT    NOT NULL,
            region      TEXT,
            description TEXT,
            image_url   TEXT,
            avg_temp    REAL,
            best_season TEXT,
            tags        TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS destination_ratings (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL REFERENCES users(id),
            destination_id INTEGER NOT NULL REFERENCES destinations(id),
            rating         REAL    NOT NULL CHECK(rating >= 1 AND rating <= 5),
            rated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, destination_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_constraints (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id         INTEGER NOT NULL REFERENCES travel_groups(id),
            user_id          INTEGER NOT NULL REFERENCES users(id),
            budget_min       REAL,
            budget_max       REAL,
            budget_delta     REAL DEFAULT 50,
            duration_min     INTEGER,
            duration_max     INTEGER,
            flight_class     TEXT DEFAULT 'economy',
            hotel_stars_min  INTEGER DEFAULT 3,
            hotel_stars_max  INTEGER DEFAULT 5,
            activity_types   TEXT,
            travel_month     TEXT,
            updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel_packages (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id       INTEGER NOT NULL REFERENCES travel_groups(id),
            destination_id INTEGER NOT NULL REFERENCES destinations(id),
            package_name   TEXT,
            flight_cost    REAL,
            hotel_cost     REAL,
            activity_cost  REAL,
            total_cost     REAL,
            duration_days  INTEGER,
            flight_class   TEXT,
            hotel_name     TEXT,
            hotel_stars    INTEGER,
            satisfaction_score REAL,
            status         TEXT DEFAULT 'candidate',
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itineraries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            package_id  INTEGER NOT NULL REFERENCES travel_packages(id),
            day_number  INTEGER NOT NULL,
            title       TEXT,
            activities  TEXT,
            meals       TEXT,
            notes       TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Initialized successfully.")

if __name__ == "__main__":
    init_db()
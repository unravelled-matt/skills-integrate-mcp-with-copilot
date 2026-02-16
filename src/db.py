from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).parent
MIGRATIONS_DIR = BASE_DIR / "migrations"
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "school.db"


DEFAULT_ACTIVITIES: dict[str, dict[str, Any]] = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
}


class ActivityNotFoundError(Exception):
    pass


class AlreadySignedUpError(Exception):
    pass


class NotSignedUpError(Exception):
    pass


def _get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _apply_migrations(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    applied = {
        row["version"]
        for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
    }

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    for migration_file in migration_files:
        version = migration_file.name
        if version in applied:
            continue
        script = migration_file.read_text(encoding="utf-8")
        connection.executescript(script)
        connection.execute(
            "INSERT INTO schema_migrations(version) VALUES (?)",
            (version,),
        )


def _seed_default_data(connection: sqlite3.Connection) -> None:
    row = connection.execute("SELECT COUNT(*) AS count FROM activities").fetchone()
    if row["count"] > 0:
        return

    for name, details in DEFAULT_ACTIVITIES.items():
        cursor = connection.execute(
            """
            INSERT INTO activities(name, description, schedule, max_participants)
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                details["description"],
                details["schedule"],
                details["max_participants"],
            ),
        )
        activity_id = cursor.lastrowid
        for email in details["participants"]:
            connection.execute(
                "INSERT INTO enrollments(activity_id, email) VALUES (?, ?)",
                (activity_id, email),
            )


def initialize_database() -> None:
    with _get_connection() as connection:
        _apply_migrations(connection)
        _seed_default_data(connection)
        connection.commit()


def get_activities() -> dict[str, dict[str, Any]]:
    with _get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                activities.id,
                activities.name,
                activities.description,
                activities.schedule,
                activities.max_participants,
                enrollments.email
            FROM activities
            LEFT JOIN enrollments ON enrollments.activity_id = activities.id
            ORDER BY activities.name, enrollments.email
            """
        ).fetchall()

    activities: dict[str, dict[str, Any]] = {}
    for row in rows:
        activity_name = row["name"]
        if activity_name not in activities:
            activities[activity_name] = {
                "description": row["description"],
                "schedule": row["schedule"],
                "max_participants": row["max_participants"],
                "participants": [],
            }
        if row["email"]:
            activities[activity_name]["participants"].append(row["email"])

    return activities


def signup_for_activity(activity_name: str, email: str) -> None:
    with _get_connection() as connection:
        activity = connection.execute(
            "SELECT id FROM activities WHERE name = ?",
            (activity_name,),
        ).fetchone()
        if activity is None:
            raise ActivityNotFoundError

        existing = connection.execute(
            "SELECT 1 FROM enrollments WHERE activity_id = ? AND email = ?",
            (activity["id"], email),
        ).fetchone()
        if existing:
            raise AlreadySignedUpError

        connection.execute(
            "INSERT INTO enrollments(activity_id, email) VALUES (?, ?)",
            (activity["id"], email),
        )
        connection.commit()


def unregister_from_activity(activity_name: str, email: str) -> None:
    with _get_connection() as connection:
        activity = connection.execute(
            "SELECT id FROM activities WHERE name = ?",
            (activity_name,),
        ).fetchone()
        if activity is None:
            raise ActivityNotFoundError

        deleted = connection.execute(
            "DELETE FROM enrollments WHERE activity_id = ? AND email = ?",
            (activity["id"], email),
        )

        if deleted.rowcount == 0:
            raise NotSignedUpError

        connection.commit()

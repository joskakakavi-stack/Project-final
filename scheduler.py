from __future__ import annotations

import sqlite3
from typing import Any

DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
SLOTS = [("08:00", "10:00"), ("10:00", "12:00"), ("13:00", "15:00"), ("15:00", "17:00")]


def split_csv(value: str | None) -> list[str]:
    """Return normalized comma-separated values without empty entries."""
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def init_schema(db: sqlite3.Connection) -> None:
    """Create the lightweight SQLite tables used by Scheduler Maker."""
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS professors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL DEFAULT '',
            unavailable_days TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            capacity INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            credits INTEGER NOT NULL,
            total_hours INTEGER NOT NULL,
            professor_id INTEGER NOT NULL,
            cohorts TEXT NOT NULL,
            departments TEXT NOT NULL,
            semester TEXT NOT NULL,
            FOREIGN KEY (professor_id) REFERENCES professors(id)
        );
        CREATE TABLE IF NOT EXISTS schedule_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            professor_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses(id),
            FOREIGN KEY (professor_id) REFERENCES professors(id),
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        );
        """
    )
    db.commit()


def rows(db: sqlite3.Connection, query: str, args: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    return db.execute(query, args).fetchall()


def slot_conflicts(entry: sqlite3.Row, candidate: dict[str, str | int]) -> bool:
    """Check whether a candidate session violates professor, room, or student-group constraints."""
    if entry["day"] != candidate["day"] or entry["start_time"] != candidate["start_time"]:
        return False

    same_professor = entry["professor_id"] == candidate["professor_id"]
    same_room = entry["room_id"] == candidate["room_id"]
    same_cohort = bool(set(split_csv(entry["cohorts"])) & set(split_csv(str(candidate["cohorts"]))))
    same_department = bool(set(split_csv(entry["departments"])) & set(split_csv(str(candidate["departments"]))))

    return same_professor or same_room or (same_cohort and same_department)


def generate_schedule(db: sqlite3.Connection) -> list[str]:
    """Generate a timetable from faculty-provided assignments and return placement warnings."""
    db.execute("DELETE FROM schedule_entries")
    courses = rows(
        db,
        """
        SELECT courses.*, professors.unavailable_days
        FROM courses JOIN professors ON professors.id = courses.professor_id
        ORDER BY semester, name
        """,
    )
    rooms = rows(db, "SELECT * FROM rooms ORDER BY capacity DESC, name")
    if not rooms:
        db.commit()
        return ["Ajoutez au moins une salle avant de générer l'emploi du temps."]
    if not courses:
        db.commit()
        return ["Ajoutez au moins un cours déjà affecté avant de générer l'emploi du temps."]

    warnings: list[str] = []
    scheduled: list[sqlite3.Row] = []
    for course in courses:
        sessions_needed = max(1, (int(course["total_hours"]) + 1) // 2)
        sessions_done = 0
        unavailable = set(split_csv(course["unavailable_days"]))
        for _session_number in range(sessions_needed):
            placed = False
            for day in DAYS:
                if day in unavailable:
                    continue
                for start_time, end_time in SLOTS:
                    for room in rooms:
                        candidate = {
                            "course_id": course["id"],
                            "professor_id": course["professor_id"],
                            "room_id": room["id"],
                            "day": day,
                            "start_time": start_time,
                            "end_time": end_time,
                            "cohorts": course["cohorts"],
                            "departments": course["departments"],
                        }
                        if any(slot_conflicts(entry, candidate) for entry in scheduled):
                            continue
                        db.execute(
                            """
                            INSERT INTO schedule_entries
                            (course_id, professor_id, room_id, day, start_time, end_time)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (course["id"], course["professor_id"], room["id"], day, start_time, end_time),
                        )
                        scheduled = rows(
                            db,
                            """
                            SELECT schedule_entries.*, courses.cohorts, courses.departments
                            FROM schedule_entries JOIN courses ON courses.id = schedule_entries.course_id
                            """,
                        )
                        sessions_done += 1
                        placed = True
                        break
                    if placed:
                        break
                if placed:
                    break
        if sessions_done < sessions_needed:
            warnings.append(f"{course['name']} : {sessions_done}/{sessions_needed} séances placées.")
    db.commit()
    return warnings

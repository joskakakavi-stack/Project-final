import sqlite3
import unittest

from scheduler import generate_schedule, init_schema, split_csv


class SchedulerTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        init_schema(self.db)

    def tearDown(self):
        self.db.close()

    def add_professor(self, name="Prof A", unavailable_days=""):
        cursor = self.db.execute(
            "INSERT INTO professors (name, email, unavailable_days) VALUES (?, ?, ?)",
            (name, f"{name.lower().replace(' ', '.')}@example.test", unavailable_days),
        )
        return cursor.lastrowid

    def add_room(self, name="Salle 1"):
        cursor = self.db.execute("INSERT INTO rooms (name, capacity) VALUES (?, ?)", (name, 40))
        return cursor.lastrowid

    def add_course(self, name, professor_id, cohorts="L1", departments="GI", hours=2):
        self.db.execute(
            """
            INSERT INTO courses (name, credits, total_hours, professor_id, cohorts, departments, semester)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, 2, hours, professor_id, cohorts, departments, "S1"),
        )

    def schedule_entries(self):
        return self.db.execute(
            """
            SELECT schedule_entries.*, courses.cohorts, courses.departments
            FROM schedule_entries JOIN courses ON courses.id = schedule_entries.course_id
            ORDER BY day, start_time
            """
        ).fetchall()

    def test_split_csv_trims_empty_parts(self):
        self.assertEqual(split_csv(" L0, GI, ,GE "), ["L0", "GI", "GE"])

    def test_generation_uses_existing_professor_assignment_without_conflict(self):
        prof = self.add_professor()
        self.add_room("Salle 1")
        self.add_room("Salle 2")
        self.add_course("Cours A", prof, cohorts="L0", departments="GI")
        self.add_course("Cours B", prof, cohorts="L1", departments="GE")

        warnings = generate_schedule(self.db)
        entries = self.schedule_entries()

        self.assertEqual(warnings, [])
        self.assertEqual(len(entries), 2)
        self.assertNotEqual((entries[0]["day"], entries[0]["start_time"]), (entries[1]["day"], entries[1]["start_time"]))

    def test_generation_respects_professor_unavailable_days(self):
        prof = self.add_professor(unavailable_days="Lundi,Mardi,Mercredi,Jeudi,Vendredi")
        self.add_room()
        self.add_course("Cours du samedi", prof)

        warnings = generate_schedule(self.db)
        entries = self.schedule_entries()

        self.assertEqual(warnings, [])
        self.assertEqual(entries[0]["day"], "Samedi")

    def test_generation_reports_warning_when_no_room_exists(self):
        prof = self.add_professor()
        self.add_course("Cours A", prof)

        warnings = generate_schedule(self.db)

        self.assertIn("Ajoutez au moins une salle", warnings[0])
        self.assertEqual(self.schedule_entries(), [])


if __name__ == "__main__":
    unittest.main()

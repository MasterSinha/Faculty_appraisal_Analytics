import unittest
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.services.faculty_performance_analytics_service import FacultyPerformanceAnalyticsService


class TestFacultyPerformanceAnalyticsModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        metadata = MetaData()

        faculty = Table(
            "faculty_profiles",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("full_name", String),
            Column("employee_id", String),
            Column("email", String),
            Column("school", String),
            Column("department", String),
            Column("designation", String),
            Column("is_active", Boolean, default=True),
        )

        journals = Table(
            "journal_publications",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("publication_year", Integer),
            Column("score", Float),
            Column("vc_score", Float),
        )

        books = Table(
            "book_publications",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("publication_year", Integer),
            Column("score", Float),
        )

        patents = Table(
            "patents",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("academic_year", String),
            Column("patent_status", String),
            Column("score", Float),
        )

        projects = Table(
            "research_projects",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("amount", Float),
            Column("academic_year", String),
            Column("score", Float),
        )

        metadata.create_all(cls.engine)

        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()

        # Insert faculty profiles (1 highly active, 1 inactive)
        cls.session.execute(
            faculty.insert(),
            [
                {
                    "id": 1,
                    "full_name": "Dr. Alice Smith",
                    "employee_id": "EMP101",
                    "email": "  ALICE@university.edu  ",
                    "school": "School of Engineering",
                    "department": "Computer Science",
                    "designation": "Professor",
                    "is_active": True,
                },
                {
                    "id": 2,
                    "full_name": "Dr. Bob Jones",
                    "employee_id": "EMP102",
                    "email": "bob@university.edu",
                    "school": "School of Sciences",
                    "department": "Physics",
                    "designation": "Associate Professor",
                    "is_active": True,
                },
            ],
        )

        # Insert research activities for Alice
        cls.session.execute(
            journals.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Deep Learning Frontiers",
                    "publication_year": 2023,
                    "score": 10.0,
                    "vc_score": 15.0,
                }
            ],
        )

        cls.session.execute(
            books.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Modern AI Textbook",
                    "publication_year": 2023,
                    "score": 20.0,
                }
            ],
        )

        cls.session.execute(
            patents.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Neural Hardware Accelerator",
                    "academic_year": "2024",
                    "patent_status": "Patent Granted",
                    "score": 25.0,
                }
            ],
        )

        cls.session.execute(
            projects.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Edge AI Research Project",
                    "amount": 750000.0,
                    "academic_year": "2024",
                    "score": 30.0,
                }
            ],
        )

        cls.session.commit()
        cls.service = FacultyPerformanceAnalyticsService(cls.session)

    def test_get_analytics_structure(self):
        res = self.service.get_analytics(1, 500, {})
        self.assertIn("items", res)
        self.assertIn("summary", res)
        self.assertIn("segments", res)
        self.assertIn("charts", res)
        self.assertEqual(res["total"], 2)

    def test_faculty_item_and_drawer(self):
        res = self.service.get_analytics(1, 500, {})
        items = res["items"]
        alice = next(item for item in items if item["faculty_email"] == "alice@university.edu")

        self.assertEqual(alice["journal_papers"], 1)
        self.assertEqual(alice["books"], 1)
        self.assertEqual(alice["patents"], 1)
        self.assertEqual(alice["projects"], 1)
        self.assertEqual(alice["funding"], 750000.0)
        self.assertGreaterEqual(alice["diversity_score"], 4)

        # Drawer records presence
        self.assertIn("journals", alice["records"])
        self.assertEqual(len(alice["records"]["journals"]), 1)

    def test_inactive_faculty_label(self):
        res = self.service.get_analytics(1, 500, {})
        items = res["items"]
        bob = next(item for item in items if item["faculty_email"] == "bob@university.edu")

        self.assertEqual(bob["total_output"], 0)
        self.assertEqual(bob["segment"], "Inactive Researchers")
        self.assertEqual(bob["status_label"], "No recorded research activity for the selected period.")

    def test_charts_presence(self):
        res = self.service.get_analytics(1, 500, {})
        charts = res["charts"]
        self.assertIn("top_faculty_by_output", charts)
        self.assertIn("top_faculty_by_validated_score", charts)
        self.assertIn("research_diversity_distribution", charts)
        self.assertIn("faculty_performance_trend", charts)
        self.assertIn("output_vs_participation_scatter", charts)
        self.assertIn("self_vs_final_score_comparison", charts)


if __name__ == "__main__":
    unittest.main()

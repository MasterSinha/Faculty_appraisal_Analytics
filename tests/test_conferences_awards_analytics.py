import unittest
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.services.conferences_awards_analytics_service import ConferencesAwardsAnalyticsService


class TestConferencesAwardsAnalyticsModule(unittest.TestCase):
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

        conferences = Table(
            "conferences",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("type", String),
            Column("organisation", String),
            Column("level", String),
            Column("academic_year", String),
            Column("score", Float),
            Column("hod_score", Float),
            Column("director_score", Float),
            Column("dean_score", Float),
            Column("vc_score", Float),
        )

        awards = Table(
            "awards",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("award_date", String),
            Column("agency", String),
            Column("level", String),
            Column("academic_year", String),
            Column("score", Float),
            Column("hod_score", Float),
            Column("director_score", Float),
            Column("dean_score", Float),
            Column("vc_score", Float),
        )

        journal = Table(
            "journal_publications",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("publication_year", Integer),
        )

        metadata.create_all(cls.engine)

        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()

        # Insert faculty profiles
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

        # Insert conferences
        cls.session.execute(
            conferences.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "International AI Conference 2023",
                    "type": "Oral Presentation",
                    "organisation": "IEEE",
                    "level": "International",
                    "academic_year": "2023-24",
                    "score": 10.0,
                    "hod_score": 10.0,
                    "director_score": 10.0,
                    "dean_score": 10.0,
                    "vc_score": 10.0,
                },
                {
                    "id": 2,
                    "faculty_email": "alice@university.edu",
                    "title": "National Software Workshop",
                    "type": "Poster",
                    "organisation": "ACM",
                    "level": "National",
                    "academic_year": "2023-24",
                    "score": 5.0,
                    "hod_score": 5.0,
                    "director_score": 5.0,
                    "dean_score": 5.0,
                    "vc_score": 5.0,
                },
            ],
        )

        # Insert awards
        cls.session.execute(
            awards.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "bob@university.edu",
                    "title": "Young Scientist National Award",
                    "award_date": "2024-02-15",
                    "agency": "DST",
                    "level": "National",
                    "academic_year": "2023-24",
                    "score": 20.0,
                    "hod_score": 20.0,
                    "director_score": 20.0,
                    "dean_score": 20.0,
                    "vc_score": 20.0,
                }
            ],
        )

        # Insert journal publications
        cls.session.execute(
            journal.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "bob@university.edu",
                    "title": "Quantum Optics Research",
                    "publication_year": 2022,  # Research recorded before award in 2024
                },
                {
                    "id": 2,
                    "faculty_email": "alice@university.edu",
                    "title": "Deep Neural Network Benchmarks",
                    "publication_year": 2023,
                },
            ],
        )

        cls.session.commit()
        cls.service = ConferencesAwardsAnalyticsService(cls.session)

    def test_get_analytics(self):
        res = self.service.get_analytics({})
        self.assertEqual(len(res["conferences"]), 2)

        self.assertEqual(len(res["awards"]), 1)

        summary = res["summary"]
        self.assertEqual(summary["total_conferences"], 2)
        self.assertEqual(summary["conference_participating_faculty"], 1)
        self.assertEqual(summary["total_awards"], 1)
        self.assertEqual(summary["award_receiving_faculty"], 1)
        self.assertEqual(summary["international_level_activities"], 1)

        # Verify journal_publications count attached to records
        c_item = res["conferences"][0]
        self.assertEqual(c_item["journal_publications"], 1)

        a_item = res["awards"][0]
        self.assertEqual(a_item["journal_publications"], 1)

        # Verify department comparison
        self.assertGreaterEqual(len(res["department_comparison"]), 2)

        # Verify faculty details
        self.assertEqual(len(res["faculty_details"]), 2)

        # Verify faculty receiving awards after research contributions association
        self.assertIn("Dr. Bob Jones", summary["faculty_receiving_awards_after_recorded_research_contributions"])

    def test_filters(self):
        res = self.service.get_analytics({"department": "Computer Science"})
        self.assertEqual(len(res["conferences"]), 2)
        self.assertEqual(len(res["awards"]), 0)


if __name__ == "__main__":
    unittest.main()

import unittest
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.services.school_performance_analytics_service import SchoolPerformanceAnalyticsService


class TestSchoolPerformanceAnalyticsModule(unittest.TestCase):
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

        external_projects = Table(
            "external_research_projects",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("agency", String),
            Column("amount", Float),
            Column("academic_year", String),
            Column("score", Float),
        )

        metadata.create_all(cls.engine)

        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()

        # Insert faculty profiles across 2 schools
        cls.session.execute(
            faculty.insert(),
            [
                {
                    "id": 1,
                    "full_name": "Dr. Alice Smith",
                    "employee_id": "EMP101",
                    "email": "alice@university.edu",
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

        # Insert research activities
        cls.session.execute(
            journals.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Quantum Computing Frontiers",
                    "publication_year": 2023,
                    "score": 10.0,
                }
            ],
        )

        cls.session.execute(
            patents.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "AI Neural Processor Patent",
                    "academic_year": "2024",
                    "patent_status": "Granted",
                    "score": 20.0,
                }
            ],
        )

        cls.session.execute(
            external_projects.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "ISRO External Satellite Research",
                    "agency": "ISRO",
                    "amount": 1000000.0,
                    "academic_year": "2024",
                    "score": 25.0,
                }
            ],
        )

        cls.session.commit()
        cls.service = SchoolPerformanceAnalyticsService(cls.session)

    def test_get_analytics_structure(self):
        res = self.service.get_analytics(1, 500, {})
        self.assertIn("items", res)
        self.assertIn("summary", res)
        self.assertIn("charts", res)
        self.assertIn("insights", res)
        self.assertEqual(res["total"], 2)

    def test_school_item_and_summary(self):
        res = self.service.get_analytics(1, 500, {})
        items = res["items"]
        eng_school = next(item for item in items if item["school"] == "School of Engineering")

        self.assertEqual(eng_school["journal_papers"], 1)
        self.assertEqual(eng_school["patents"], 1)
        self.assertEqual(eng_school["external_projects"], 1)
        self.assertEqual(eng_school["total_funding"], 1000000.0)
        self.assertEqual(eng_school["publication_participation"], 100.0)

        # Summary KPIs check
        summary = res["summary"]
        self.assertEqual(summary["highest_research_output_school"], "School of Engineering")
        self.assertIn("School of Sciences", summary["schools_with_no_external_project"])

    def test_charts_and_insights_presence(self):
        res = self.service.get_analytics(1, 500, {})
        charts = res["charts"]
        self.assertIn("research_category_comparison_by_school", charts)
        self.assertIn("publication_participation_by_school", charts)
        self.assertIn("funding_by_school", charts)
        self.assertIn("patent_ipr_contribution_by_school", charts)
        self.assertIn("academic_year_trend", charts)
        self.assertIn("school_research_diversity", charts)
        self.assertIn("school_contribution_percentage_to_university_output", charts)

        self.assertIsInstance(res["insights"], list)
        self.assertGreater(len(res["insights"]), 0)


if __name__ == "__main__":
    unittest.main()

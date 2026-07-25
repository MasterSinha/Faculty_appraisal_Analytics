import unittest
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.services.department_performance_analytics_service import DepartmentPerformanceAnalyticsService


class TestDepartmentPerformanceAnalyticsModule(unittest.TestCase):
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
            Column("issn", String),
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
            Column("agency", String),
            Column("amount", Float),
            Column("academic_year", String),
            Column("score", Float),
        )

        metadata.create_all(cls.engine)

        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()

        # Insert faculty profiles across 2 departments
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

        # Insert activities for Computer Science
        cls.session.execute(
            journals.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Quantum AI Systems",
                    "publication_year": 2023,
                    "issn": "1234-5678",
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
                    "title": "Quantum Chip Invention",
                    "academic_year": "2024",
                    "patent_status": "Granted",
                    "score": 20.0,
                }
            ],
        )

        cls.session.execute(
            projects.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Quantum Supercomputer Project",
                    "agency": "DST",
                    "amount": 500000.0,
                    "academic_year": "2024",
                    "score": 25.0,
                }
            ],
        )

        cls.session.commit()
        cls.service = DepartmentPerformanceAnalyticsService(cls.session)

    def test_get_analytics_structure(self):
        res = self.service.get_analytics(1, 500, {})
        self.assertIn("items", res)
        self.assertIn("summary", res)
        self.assertIn("charts", res)
        self.assertEqual(res["total"], 2)

    def test_department_item_and_health_components(self):
        res = self.service.get_analytics(1, 500, {})
        items = res["items"]
        cs_dept = next(item for item in items if item["department"] == "Computer Science")

        self.assertEqual(cs_dept["journal_papers"], 1)
        self.assertEqual(cs_dept["patents"], 1)
        self.assertEqual(cs_dept["projects"], 1)
        self.assertEqual(cs_dept["funding"], 500000.0)
        self.assertEqual(cs_dept["publication_participation_rate"], 100.0)

        # Health components breakdown presence
        comp = cs_dept["health_components"]
        self.assertIn("publication_participation", comp)
        self.assertIn("output_per_faculty", comp)
        self.assertIn("funding_performance", comp)
        self.assertIn("patent_ipr_performance", comp)

        self.assertGreater(cs_dept["research_health_score"], 0.0)
        self.assertIn(cs_dept["health_category"], ["Excellent", "Strong", "Developing", "Needs Attention"])

    def test_charts_presence(self):
        res = self.service.get_analytics(1, 500, {})
        charts = res["charts"]
        self.assertIn("department_output_ranking", charts)
        self.assertIn("participation_rate_by_department", charts)
        self.assertIn("funding_by_department", charts)
        self.assertIn("patent_ipr_activity", charts)
        self.assertIn("department_category_heatmap", charts)
        self.assertIn("year_over_year_growth", charts)
        self.assertIn("research_health_score_breakdown", charts)


if __name__ == "__main__":
    unittest.main()

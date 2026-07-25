import unittest
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.services.research_data_quality_analytics_service import ResearchDataQualityAnalyticsService


class TestResearchDataQualityAnalyticsModule(unittest.TestCase):
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
            Column("indexing", String),
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
        )

        metadata.create_all(cls.engine)

        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()

        # Insert faculty profiles (1 complete, 1 missing department)
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
                    "department": "",  # Blank department (Check 7)
                    "designation": "Associate Professor",
                    "is_active": True,
                },
            ],
        )

        # Insert journals (1 missing ISSN and indexing - Check 2 & 3)
        cls.session.execute(
            journals.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Quantum AI Computing",
                    "publication_year": 2023,
                    "issn": "",
                    "indexing": "",
                    "score": 10.0,
                }
            ],
        )

        # Insert projects (1 negative funding - Check 16)
        cls.session.execute(
            projects.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Corrupted Grant Project",
                    "amount": -50000.0,
                    "academic_year": "2023-24",
                }
            ],
        )

        cls.session.commit()
        cls.service = ResearchDataQualityAnalyticsService(cls.session)

    def test_get_analytics_structure(self):
        res = self.service.get_analytics({})
        self.assertIn("items", res)
        self.assertIn("alerts", res)
        self.assertIn("summary", res)
        self.assertIn("charts", res)
        self.assertIn("completeness_percentage", res)
        self.assertFalse(res["review_supported"])

    def test_detected_data_quality_alerts(self):
        res = self.service.get_analytics({})
        alerts = res["alerts"]
        summary = res["summary"]

        self.assertGreater(summary["total_alerts"], 0)

        # Check for negative funding critical alert
        neg_alert = next((a for a in alerts if a["alert_type"] == "Outlier" and "negative" in a["issue_description"]), None)
        self.assertIsNotNone(neg_alert)
        self.assertEqual(neg_alert["severity"], "Critical")

        # Check for blank department informational alert
        blank_dept_alert = next((a for a in alerts if "missing department" in a["issue_description"]), None)
        self.assertIsNotNone(blank_dept_alert)
        self.assertEqual(blank_dept_alert["severity"], "Informational")

    def test_charts_presence(self):
        res = self.service.get_analytics({})
        charts = res["charts"]
        self.assertIn("alerts_by_severity", charts)
        self.assertIn("alerts_by_category", charts)
        self.assertIn("completeness_by_department", charts)
        self.assertIn("top_issue_types", charts)
        self.assertIn("alert_trend_by_year", charts)


if __name__ == "__main__":
    unittest.main()

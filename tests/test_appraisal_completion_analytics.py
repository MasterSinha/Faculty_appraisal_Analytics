import unittest
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.services.appraisal_completion_analytics_service import AppraisalCompletionAnalyticsService


class TestAppraisalCompletionAnalyticsModule(unittest.TestCase):
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

        declarations = Table(
            "declarations",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("status", String),
            Column("submission_date", String),
        )

        documents = Table(
            "appraisal_documents",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("doc_key", String),
            Column("section", String),
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

        metadata.create_all(cls.engine)

        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()

        # Insert faculty profiles (1 submitted, 1 not submitted)
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

        # Insert declarations (Alice submitted, Bob pending)
        cls.session.execute(
            declarations.insert(),
            [
                {"id": 1, "faculty_email": "alice@university.edu", "status": "Submitted to HOD", "submission_date": "2024-03-01"},
            ],
        )

        # Insert documents for Alice
        cls.session.execute(
            documents.insert(),
            [
                {"id": 1, "faculty_email": "alice@university.edu", "doc_key": "1", "section": "journals"},
            ],
        )

        # Insert research activity for Alice and Bob
        cls.session.execute(
            journals.insert(),
            [
                {"id": 1, "faculty_email": "alice@university.edu", "title": "AI Research Paper", "publication_year": 2023, "score": 10.0},
                {"id": 2, "faculty_email": "bob@university.edu", "title": "Quantum Physics Paper", "publication_year": 2023, "score": 10.0},
            ],
        )

        cls.session.commit()
        cls.service = AppraisalCompletionAnalyticsService(cls.session)

    def test_get_analytics_structure(self):
        res = self.service.get_analytics({})
        self.assertIn("items", res)
        self.assertIn("appraisals", res)
        self.assertIn("summary", res)
        self.assertIn("status_analytics", res)
        self.assertIn("department_metrics", res)
        self.assertIn("tables", res)
        self.assertIn("charts", res)

    def test_summary_and_followup_tables(self):
        res = self.service.get_analytics({})
        summary = res["summary"]

        self.assertEqual(summary["active_faculty"], 2)
        self.assertEqual(summary["submitted_appraisals"], 1)
        self.assertEqual(summary["pending_appraisals"], 1)
        self.assertEqual(summary["completion_percentage"], 50.0)
        self.assertEqual(summary["research_active_faculty_not_submitted"], 1)

        # Follow up tables test
        tbls = res["tables"]
        self.assertEqual(len(tbls["not_submitted"]), 1)
        self.assertEqual(tbls["not_submitted"][0]["faculty_email"], "bob@university.edu")

        # Record without evidence test (Bob has no evidence document)
        self.assertGreaterEqual(len(tbls["records_without_evidence"]), 1)
        bob_rec = next(r for r in tbls["records_without_evidence"] if r["faculty_email"] == "bob@university.edu")
        self.assertEqual(bob_rec["evidence_mapping_status"], "Unmapped")

    def test_charts_presence(self):
        res = self.service.get_analytics({})
        charts = res["charts"]
        self.assertIn("submission_status_by_department", charts)
        self.assertIn("completion_rate_by_school", charts)
        self.assertIn("submission_trend_by_academic_year", charts)
        self.assertIn("research_active_versus_submitted_faculty", charts)
        self.assertIn("evidence_completion_by_department", charts)
        self.assertIn("review_stage_distribution", charts)


if __name__ == "__main__":
    unittest.main()

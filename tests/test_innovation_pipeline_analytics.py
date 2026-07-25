import unittest
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.services.innovation_pipeline_analytics_service import InnovationPipelineAnalyticsService


class TestInnovationPipelineAnalyticsModule(unittest.TestCase):
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

        proposals = Table(
            "research_proposals",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("agency", String),
            Column("duration", String),
            Column("amount", Float),
            Column("academic_year", String),
            Column("score", Float),
        )

        internal_projects = Table(
            "research_projects",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("agency", String),
            Column("sanction_date", String),
            Column("amount", Float),
            Column("role", String),
            Column("project_status", String),
            Column("academic_year", String),
            Column("score", Float),
        )

        external_projects = Table(
            "external_research_projects",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("agency", String),
            Column("sanction_date", String),
            Column("amount", Float),
            Column("role", String),
            Column("project_status", String),
            Column("academic_year", String),
            Column("score", Float),
        )

        patents = Table(
            "patents",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("type", String),
            Column("scope", String),
            Column("patent_date", String),
            Column("patent_status", String),
            Column("file_no", String),
            Column("academic_year", String),
            Column("score", Float),
        )

        ipr = Table(
            "ipr_records",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("scope", String),
            Column("ipr_date", String),
            Column("ipr_status", String),
            Column("file_no", String),
            Column("score", Float),
        )

        products = Table(
            "products_developed",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("faculty_email", String),
            Column("title", String),
            Column("development_date", String),
            Column("status", String),
            Column("academic_year", String),
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

        # Insert test data across 6 innovation categories
        cls.session.execute(
            proposals.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "AI Healthcare Proposal",
                    "agency": "DST",
                    "duration": "2 Years",
                    "amount": 500000.0,
                    "academic_year": "2023-24",
                    "score": 10.0,
                }
            ],
        )

        cls.session.execute(
            internal_projects.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "AI Medical Diagnosis Lab",
                    "agency": "DST",
                    "sanction_date": "2023-05-10",
                    "amount": 500000.0,
                    "role": "PI",
                    "project_status": "Sanctioned",
                    "academic_year": "2023-24",
                    "score": 15.0,
                }
            ],
        )

        cls.session.execute(
            external_projects.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "bob@university.edu",
                    "title": "Quantum Sensor External Project",
                    "agency": "ISRO",
                    "sanction_date": "2023-06-15",
                    "amount": 1000000.0,
                    "role": "Co-PI",
                    "project_status": "Sanctioned",
                    "academic_year": "2023-24",
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
                    "title": "AI Neural Chip Patent",
                    "type": "Utility",
                    "scope": "International",
                    "patent_date": "2024-01-20",
                    "patent_status": "Patent Granted",
                    "file_no": "PAT-2024-001",
                    "academic_year": "2023-24",
                    "score": 25.0,
                }
            ],
        )

        cls.session.execute(
            ipr.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "bob@university.edu",
                    "title": "Quantum Algorithm Copyright",
                    "scope": "Domestic",
                    "ipr_date": "2024-02-10",
                    "ipr_status": "Registered",
                    "file_no": "IPR-2024-001",
                    "score": 10.0,
                }
            ],
        )

        cls.session.execute(
            products.insert(),
            [
                {
                    "id": 1,
                    "faculty_email": "alice@university.edu",
                    "title": "Smart Diagnostic Device V1",
                    "development_date": "2024-03-01",
                    "status": "Deployed",
                    "academic_year": "2023-24",
                }
            ],
        )

        cls.session.commit()
        cls.service = InnovationPipelineAnalyticsService(cls.session)

    def test_get_analytics_structure(self):
        res = self.service.get_analytics({})
        expected_keys = [
            "research_proposals",
            "research_projects",
            "external_research_projects",
            "patents",
            "ipr_records",
            "products_developed",
            "summary",
            "department_contribution",
            "school_contribution",
            "academic_year_comparison",
            "faculty_innovation_diversity",
            "gap_analytics",
        ]
        for key in expected_keys:
            self.assertIn(key, res)

    def test_summary_metrics_and_funnel(self):
        res = self.service.get_analytics({})
        summary = res["summary"]

        self.assertEqual(summary["proposals_submitted"], 1)
        self.assertEqual(summary["projects_sanctioned"], 2)
        self.assertEqual(summary["patent_or_ipr_records"], 2)
        self.assertEqual(summary["patents_granted"], 1)
        self.assertEqual(summary["products_developed"], 1)
        self.assertEqual(summary["innovation_active_faculty"], 2)

        # Limitation note check
        self.assertIn("Pipeline stages represent aggregate institutional counts", summary["limitation_note"])

        # Funnel stage check
        funnel = summary["aggregate_funnel"]
        self.assertEqual(len(funnel), 5)
        self.assertEqual(funnel[0]["stage"], "Research Proposals")
        self.assertEqual(funnel[1]["stage"], "Sanctioned Projects")
        self.assertEqual(funnel[1]["percentage_change_from_previous_stage"], 100.0)

    def test_gap_analytics(self):
        res = self.service.get_analytics({})
        gap = res["gap_analytics"]

        self.assertIn("proposals_without_corresponding_aggregate_project_activity", gap)
        self.assertIn("departments_with_projects_but_no_patents", gap)
        self.assertIn("faculty_with_patents_but_no_products", gap)
        self.assertIn("departments_with_no_products_developed", gap)

    def test_record_fields(self):
        res = self.service.get_analytics({})
        patent = res["patents"][0]
        self.assertEqual(patent["title"], "AI Neural Chip Patent")
        self.assertEqual(patent["patent_status"], "Patent Granted")
        self.assertEqual(patent["file_number"], "PAT-2024-001")

        product = res["products_developed"][0]
        self.assertEqual(product["product_title"], "Smart Diagnostic Device V1")


if __name__ == "__main__":
    unittest.main()

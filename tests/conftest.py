import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Column, Float, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app


@pytest.fixture(scope="session")
def engine():
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()

    faculty = Table(
        "faculty",
        metadata,
        Column("faculty_id", Integer, primary_key=True),
        Column("faculty_name", String),
        Column("employee_id", String),
        Column("email", String),
        Column("school", String),
        Column("department", String),
    )

    journal = Table(
        "journal_publications",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("faculty_id", Integer),
        Column("journal_name", String),
        Column("indexing", String),
        Column("publication_year", Integer),
        Column("vc_score", Float),
        Column("self_score", Float),
        Column("director_score", Float),
        Column("dean_score", Float),
    )

    projects = Table(
        "research_projects",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("faculty_id", Integer),
        Column("project_title", String),
        Column("status", String),
        Column("funding_agency", String),
        Column("amount", Float),
        Column("project_type", String),
        Column("vc_score", Float),
    )

    metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    session.execute(
        faculty.insert(),
        [
            {
                "faculty_id": 1,
                "faculty_name": "Dr. Alice Smith",
                "employee_id": "EMP101",
                "email": "alice@university.edu",
                "school": "School of Engineering",
                "department": "Computer Science",
            },
            {
                "faculty_id": 2,
                "faculty_name": "Dr. Bob Jones",
                "employee_id": "EMP102",
                "email": "bob@university.edu",
                "school": "School of Sciences",
                "department": "Physics",
            },
        ],
    )

    session.execute(
        journal.insert(),
        [
            {
                "id": 1,
                "faculty_id": 1,
                "journal_name": "IEEE Transactions on Software Engineering",
                "indexing": "SCI",
                "publication_year": 2024,
                "vc_score": 10.0,
                "self_score": 10.0,
                "director_score": 10.0,
                "dean_score": 10.0,
            },
            {
                "id": 2,
                "faculty_id": 1,
                "journal_name": "ACM Computing Surveys",
                "indexing": "Scopus",
                "publication_year": 2023,
                "vc_score": 8.0,
                "self_score": 10.0,
                "director_score": 8.0,
                "dean_score": 8.0,
            },
        ],
    )

    session.execute(
        projects.insert(),
        [
            {
                "id": 1,
                "faculty_id": 1,
                "project_title": "Quantum AI Systems",
                "status": "Ongoing",
                "funding_agency": "DST",
                "amount": 750000.0,
                "project_type": "External",
                "vc_score": 15.0,
            }
        ],
    )

    session.commit()
    yield engine


@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

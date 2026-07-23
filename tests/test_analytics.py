def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_schema_endpoint(client):
    response = client.get("/api/v1/research-analytics/schema")
    assert response.status_code == 200
    data = response.json()
    assert "faculty_table" in data
    assert "research_tables" in data


def test_overview_endpoint(client):
    response = client.get("/api/v1/research-analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_faculty"] == 2
    assert data["total_research_papers"] == 2
    assert data["total_projects"] == 1
    assert data["total_funding"] == 750000.0


def test_indexing_distribution(client):
    response = client.get("/api/v1/research-analytics/publications/indexing")
    assert response.status_code == 200
    data = response.json().get("data", [])
    assert len(data) >= 2


def test_faculty_summary(client):
    response = client.get("/api/v1/research-analytics/faculty?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_faculty_detail(client):
    response = client.get("/api/v1/research-analytics/faculty/1")
    assert response.status_code == 200
    data = response.json()
    assert "faculty" in data
    assert "records" in data
    assert data["faculty"]["faculty_id"] == 1


def test_publication_trend(client):
    response = client.get("/api/v1/research-analytics/publications/trend")
    assert response.status_code == 200
    data = response.json().get("data", [])
    assert len(data) >= 2


def test_projects_summary(client):
    response = client.get("/api/v1/research-analytics/projects/summary")
    assert response.status_code == 200
    data = response.json().get("data", [])
    assert len(data) > 0


def test_scores_comparison(client):
    response = client.get("/api/v1/research-analytics/scores/comparison")
    assert response.status_code == 200
    data = response.json()
    assert data["self_score"] > 0


def test_filters(client):
    response = client.get("/api/v1/research-analytics/filters")
    assert response.status_code == 200
    data = response.json()
    assert "School of Engineering" in data["schools"]
    assert "Computer Science" in data["departments"]


def test_export_csv(client):
    response = client.get("/api/v1/research-analytics/export?format=csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert b"Dr. Alice Smith" in response.content


def test_export_xlsx(client):
    response = client.get("/api/v1/research-analytics/export?format=xlsx")
    assert response.status_code == 200
    assert "spreadsheetml" in response.headers["content-type"]

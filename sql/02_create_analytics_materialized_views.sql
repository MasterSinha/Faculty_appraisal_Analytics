-- =============================================================================
-- FACULTY RESEARCH ANALYTICS - MATERIALIZED VIEWS
-- Optimized pre-aggregated summary data for high-performance VM deployment
-- =============================================================================

-- 1. MATERIALIZED VIEW: Faculty Research Summary
DROP MATERIALIZED VIEW IF EXISTS mv_research_faculty_summary CASCADE;
CREATE MATERIALIZED VIEW mv_research_faculty_summary AS
SELECT 
    LOWER(TRIM(fp.email)) AS faculty_email,
    fp.employee_id,
    fp.full_name AS faculty_name,
    fp.school,
    fp.department,
    fp.designation,
    fp.is_active,
    
    COUNT(DISTINCT jp.id) FILTER (WHERE jp.title IS NOT NULL AND TRIM(jp.title) <> '') AS total_journals,
    COUNT(DISTINCT bp.id) FILTER (WHERE COALESCE(NULLIF(TRIM(bp.title), ''), NULLIF(TRIM(bp.book), '')) IS NOT NULL) AS total_books,
    COUNT(DISTINCT p.id) FILTER (WHERE p.title IS NOT NULL AND TRIM(p.title) <> '') AS total_patents,
    COUNT(DISTINCT p.id) FILTER (WHERE LOWER(COALESCE(p.patent_status, '')) LIKE '%grant%') AS patents_granted,
    COUNT(DISTINCT ipr.id) FILTER (WHERE ipr.title IS NOT NULL AND TRIM(ipr.title) <> '') AS total_ipr,
    COUNT(DISTINCT rp.id) FILTER (WHERE rp.title IS NOT NULL AND TRIM(rp.title) <> '') AS total_projects,
    COALESCE(SUM(DISTINCT rp.amount), 0) AS total_funding,
    COUNT(DISTINCT rp.id) FILTER (WHERE LOWER(COALESCE(rp.project_type, '')) LIKE '%external%' OR LOWER(COALESCE(rp.agency, '')) NOT LIKE '%internal%') AS external_projects,
    COALESCE(SUM(DISTINCT CASE WHEN LOWER(COALESCE(rp.project_type, '')) LIKE '%external%' THEN rp.amount ELSE 0 END), 0) AS external_funding,
    COUNT(DISTINCT rpr.id) FILTER (WHERE rpr.title IS NOT NULL AND TRIM(rpr.title) <> '') AS total_proposals,
    COALESCE(SUM(DISTINCT rpr.amount), 0) AS total_proposal_amount,
    COUNT(DISTINCT rg.id) AS total_scholars_guided,
    COUNT(DISTINCT c.id) FILTER (WHERE c.title IS NOT NULL AND TRIM(c.title) <> '') AS total_conferences,
    COUNT(DISTINCT a.id) FILTER (WHERE a.title IS NOT NULL AND TRIM(a.title) <> '') AS total_awards,
    COUNT(DISTINCT pd.id) FILTER (WHERE pd.details IS NOT NULL AND TRIM(pd.details) <> '') AS total_products,
    
    (COALESCE(SUM(DISTINCT jp.score), 0) + COALESCE(SUM(DISTINCT bp.score), 0) + COALESCE(SUM(DISTINCT p.score), 0) + COALESCE(SUM(DISTINCT rp.score), 0)) AS total_research_score
FROM faculty_profiles fp
LEFT JOIN journal_publications jp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(jp.faculty_email))
LEFT JOIN book_publications bp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(bp.faculty_email))
LEFT JOIN patents p ON LOWER(TRIM(fp.email)) = LOWER(TRIM(p.faculty_email))
LEFT JOIN ipr_records ipr ON LOWER(TRIM(fp.email)) = LOWER(TRIM(ipr.faculty_email))
LEFT JOIN research_projects rp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rp.faculty_email))
LEFT JOIN research_proposals rpr ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rpr.faculty_email))
LEFT JOIN research_guidance rg ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rg.faculty_email))
LEFT JOIN conferences c ON LOWER(TRIM(fp.email)) = LOWER(TRIM(c.faculty_email))
LEFT JOIN awards a ON LOWER(TRIM(fp.email)) = LOWER(TRIM(a.faculty_email))
LEFT JOIN products_developed pd ON LOWER(TRIM(fp.email)) = LOWER(TRIM(pd.faculty_email))
WHERE fp.is_active = TRUE
GROUP BY fp.email, fp.employee_id, fp.full_name, fp.school, fp.department, fp.designation, fp.is_active;

CREATE UNIQUE INDEX idx_mv_faculty_summary_email ON mv_research_faculty_summary(faculty_email);
CREATE INDEX idx_mv_faculty_summary_school_dept ON mv_research_faculty_summary(school, department);


-- 2. MATERIALIZED VIEW: Department Research Summary
DROP MATERIALIZED VIEW IF EXISTS mv_research_department_summary CASCADE;
CREATE MATERIALIZED VIEW mv_research_department_summary AS
SELECT 
    fp.school,
    fp.department,
    COUNT(DISTINCT fp.faculty_email) AS total_active_faculty,
    COUNT(DISTINCT CASE WHEN fp.total_journals > 0 OR fp.total_books > 0 OR fp.total_patents > 0 OR fp.total_projects > 0 THEN fp.faculty_email END) AS research_active_faculty,
    SUM(fp.total_journals) AS journal_publications,
    SUM(fp.total_books) AS book_publications,
    SUM(fp.total_patents) AS patents,
    SUM(fp.patents_granted) AS patents_granted,
    SUM(fp.total_projects) AS research_projects,
    SUM(fp.total_funding) AS total_project_funding,
    SUM(fp.total_proposals) AS research_proposals,
    SUM(fp.total_proposal_amount) AS total_proposal_amount,
    SUM(fp.total_scholars_guided) AS research_scholars_guided,
    SUM(fp.total_conferences) AS conferences,
    SUM(fp.total_awards) AS awards,
    SUM(fp.total_products) AS products_developed,
    SUM(fp.total_research_score) AS total_research_score,
    ROUND(
        (COUNT(DISTINCT CASE WHEN fp.total_journals > 0 OR fp.total_projects > 0 OR fp.total_patents > 0 THEN fp.faculty_email END)::numeric 
        / NULLIF(COUNT(DISTINCT fp.faculty_email), 0)::numeric) * 100, 2
    ) AS participation_rate
FROM mv_research_faculty_summary fp
GROUP BY fp.school, fp.department;

CREATE UNIQUE INDEX idx_mv_dept_summary_school_dept ON mv_research_department_summary(school, department);


-- 3. MATERIALIZED VIEW: School Research Summary
DROP MATERIALIZED VIEW IF EXISTS mv_research_school_summary CASCADE;
CREATE MATERIALIZED VIEW mv_research_school_summary AS
SELECT 
    school,
    SUM(total_active_faculty) AS total_active_faculty,
    SUM(research_active_faculty) AS research_active_faculty,
    SUM(journal_publications) AS journal_publications,
    SUM(book_publications) AS book_publications,
    SUM(patents) AS patents,
    SUM(research_projects) AS research_projects,
    SUM(total_project_funding) AS total_project_funding,
    SUM(total_research_score) AS total_research_score,
    ROUND((SUM(research_active_faculty)::numeric / NULLIF(SUM(total_active_faculty), 0)::numeric) * 100, 2) AS participation_rate
FROM mv_research_department_summary
GROUP BY school;

CREATE UNIQUE INDEX idx_mv_school_summary_school ON mv_research_school_summary(school);


-- 4. MATERIALIZED VIEW: Yearly Trend
DROP MATERIALIZED VIEW IF EXISTS mv_research_yearly_trend CASCADE;
CREATE MATERIALIZED VIEW mv_research_yearly_trend AS
WITH yearly_data AS (
    SELECT publication_year::text AS academic_year, 'journal' AS category, id::text AS rec_id, 0::numeric AS amount FROM journal_publications WHERE title IS NOT NULL AND TRIM(title) <> '' AND publication_year IS NOT NULL
    UNION ALL
    SELECT publication_year::text, 'book', id::text, 0::numeric FROM book_publications WHERE COALESCE(NULLIF(TRIM(title), ''), NULLIF(TRIM(book), '')) IS NOT NULL AND publication_year IS NOT NULL
    UNION ALL
    SELECT academic_year::text, 'patent', id::text, 0::numeric FROM patents WHERE title IS NOT NULL AND TRIM(title) <> '' AND academic_year IS NOT NULL
    UNION ALL
    SELECT academic_year::text, 'project', id::text, COALESCE(amount, 0) FROM research_projects WHERE title IS NOT NULL AND TRIM(title) <> '' AND academic_year IS NOT NULL
)
SELECT 
    academic_year,
    COUNT(DISTINCT CASE WHEN category = 'journal' THEN rec_id END) AS publications,
    COUNT(DISTINCT CASE WHEN category = 'book' THEN rec_id END) AS books,
    COUNT(DISTINCT CASE WHEN category = 'patent' THEN rec_id END) AS patents,
    COUNT(DISTINCT CASE WHEN category = 'project' THEN rec_id END) AS projects,
    SUM(CASE WHEN category = 'project' THEN amount ELSE 0 END) AS funding
FROM yearly_data
GROUP BY academic_year
ORDER BY academic_year;

CREATE UNIQUE INDEX idx_mv_yearly_trend_year ON mv_research_yearly_trend(academic_year);


-- 5. MATERIALIZED VIEW: Category Summary
DROP MATERIALIZED VIEW IF EXISTS mv_research_category_summary CASCADE;
CREATE MATERIALIZED VIEW mv_research_category_summary AS
SELECT 'journal_publication' AS category, COUNT(*) AS count, COALESCE(SUM(score), 0) AS total_score, 0::numeric AS total_amount FROM journal_publications WHERE title IS NOT NULL AND TRIM(title) <> ''
UNION ALL
SELECT 'book_publication' AS category, COUNT(*), COALESCE(SUM(score), 0), 0::numeric FROM book_publications WHERE COALESCE(NULLIF(TRIM(title), ''), NULLIF(TRIM(book), '')) IS NOT NULL
UNION ALL
SELECT 'patent' AS category, COUNT(*), COALESCE(SUM(score), 0), 0::numeric FROM patents WHERE title IS NOT NULL AND TRIM(title) <> ''
UNION ALL
SELECT 'ipr' AS category, COUNT(*), COALESCE(SUM(score), 0), 0::numeric FROM ipr_records WHERE title IS NOT NULL AND TRIM(title) <> ''
UNION ALL
SELECT 'research_project' AS category, COUNT(*), COALESCE(SUM(score), 0), COALESCE(SUM(amount), 0) FROM research_projects WHERE title IS NOT NULL AND TRIM(title) <> ''
UNION ALL
SELECT 'research_proposal' AS category, COUNT(*), COALESCE(SUM(score), 0), COALESCE(SUM(amount), 0) FROM research_proposals WHERE title IS NOT NULL AND TRIM(title) <> '';

CREATE UNIQUE INDEX idx_mv_category_summary_cat ON mv_research_category_summary(category);


-- 6. MATERIALIZED VIEW: Data Quality Summary
DROP MATERIALIZED VIEW IF EXISTS mv_research_data_quality_summary CASCADE;
CREATE MATERIALIZED VIEW mv_research_data_quality_summary AS
SELECT 'unmatched_faculty_email' AS check_name, COUNT(*) AS alert_count FROM journal_publications jp LEFT JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(jp.faculty_email)) WHERE fp.email IS NULL
UNION ALL
SELECT 'missing_journal_title', COUNT(*) FROM journal_publications WHERE NULLIF(TRIM(title), '') IS NULL
UNION ALL
SELECT 'missing_book_isbn', COUNT(*) FROM book_publications WHERE NULLIF(TRIM(isbn), '') IS NULL
UNION ALL
SELECT 'missing_patent_status', COUNT(*) FROM patents WHERE NULLIF(TRIM(patent_status), '') IS NULL
UNION ALL
SELECT 'missing_project_amount', COUNT(*) FROM research_projects WHERE amount IS NULL;

CREATE UNIQUE INDEX idx_mv_data_quality_check ON mv_research_data_quality_summary(check_name);


-- 7. MATERIALIZED VIEW: Dynamic Filter Options
DROP MATERIALIZED VIEW IF EXISTS mv_research_filter_options CASCADE;
CREATE MATERIALIZED VIEW mv_research_filter_options AS
SELECT 
    ARRAY(SELECT DISTINCT academic_year FROM faculty_profiles WHERE NULLIF(TRIM(academic_year), '') IS NOT NULL ORDER BY academic_year) AS academic_years,
    ARRAY(SELECT DISTINCT school FROM faculty_profiles WHERE NULLIF(TRIM(school), '') IS NOT NULL ORDER BY school) AS schools,
    ARRAY(SELECT DISTINCT department FROM faculty_profiles WHERE NULLIF(TRIM(department), '') IS NOT NULL ORDER BY department) AS departments,
    ARRAY(SELECT DISTINCT designation FROM faculty_profiles WHERE NULLIF(TRIM(designation), '') IS NOT NULL ORDER BY designation) AS designations,
    ARRAY(SELECT DISTINCT indexing FROM journal_publications WHERE NULLIF(TRIM(indexing), '') IS NOT NULL ORDER BY indexing) AS indexing_options;

-- Function to refresh all materialized views safely
CREATE OR REPLACE FUNCTION refresh_analytics_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_research_faculty_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_research_department_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_research_school_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_research_yearly_trend;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_research_category_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_research_data_quality_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_research_filter_options;
END;
$$ LANGUAGE plpgsql;

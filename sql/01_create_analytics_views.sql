-- =============================================================================
-- FACULTY APPRAISAL RESEARCH ANALYTICS - POSTGRESQL VIEWS
-- Schema-safe, whitespace & case-insensitive email join architecture
-- =============================================================================

-- 1. UNIFIED RESEARCH ACTIVITY VIEW (UNION ALL across activity tables)
CREATE OR REPLACE VIEW vw_research_activity_union AS
SELECT 
    'journal_publication' AS category,
    j.id::text AS activity_id,
    LOWER(TRIM(j.faculty_email)) AS faculty_email,
    j.publication_year::text AS academic_year,
    j.journal_name AS title,
    j.indexing AS indexing_type,
    NULL::text AS scope,
    NULL::numeric AS amount,
    NULL::text AS status,
    NULL::text AS agency,
    NULL::text AS role,
    COALESCE(j.self_score, 0) AS self_score,
    COALESCE(j.hod_score, 0) AS hod_score,
    COALESCE(j.director_score, 0) AS director_score,
    COALESCE(j.dean_score, 0) AS dean_score,
    COALESCE(j.vc_score, 0) AS vc_score,
    j.created_at
FROM journal_publications j
WHERE j.journal_name IS NOT NULL AND TRIM(j.journal_name) <> ''

UNION ALL

SELECT 
    'book_publication' AS category,
    b.id::text AS activity_id,
    LOWER(TRIM(b.faculty_email)) AS faculty_email,
    b.publication_year::text AS academic_year,
    b.book_title AS title,
    NULL::text AS indexing_type,
    NULL::text AS scope,
    NULL::numeric AS amount,
    NULL::text AS status,
    NULL::text AS agency,
    b.role AS role,
    COALESCE(b.self_score, 0) AS self_score,
    COALESCE(b.hod_score, 0) AS hod_score,
    COALESCE(b.director_score, 0) AS director_score,
    COALESCE(b.dean_score, 0) AS dean_score,
    COALESCE(b.vc_score, 0) AS vc_score,
    b.created_at
FROM book_publications b
WHERE b.book_title IS NOT NULL AND TRIM(b.book_title) <> ''

UNION ALL

SELECT 
    'patent' AS category,
    p.id::text AS activity_id,
    LOWER(TRIM(p.faculty_email)) AS faculty_email,
    p.academic_year::text AS academic_year,
    p.patent_title AS title,
    NULL::text AS indexing_type,
    p.scope AS scope,
    NULL::numeric AS amount,
    p.status AS status,
    NULL::text AS agency,
    NULL::text AS role,
    COALESCE(p.self_score, 0) AS self_score,
    COALESCE(p.hod_score, 0) AS hod_score,
    COALESCE(p.director_score, 0) AS director_score,
    COALESCE(p.dean_score, 0) AS dean_score,
    COALESCE(p.vc_score, 0) AS vc_score,
    p.created_at
FROM patents p
WHERE p.patent_title IS NOT NULL AND TRIM(p.patent_title) <> ''

UNION ALL

SELECT 
    'ipr' AS category,
    ipr.id::text AS activity_id,
    LOWER(TRIM(ipr.faculty_email)) AS faculty_email,
    ipr.academic_year::text AS academic_year,
    ipr.title AS title,
    NULL::text AS indexing_type,
    NULL::text AS scope,
    NULL::numeric AS amount,
    ipr.status AS status,
    NULL::text AS agency,
    NULL::text AS role,
    COALESCE(ipr.self_score, 0) AS self_score,
    COALESCE(ipr.hod_score, 0) AS hod_score,
    COALESCE(ipr.director_score, 0) AS director_score,
    COALESCE(ipr.dean_score, 0) AS dean_score,
    COALESCE(ipr.vc_score, 0) AS vc_score,
    ipr.created_at
FROM ipr_records ipr
WHERE ipr.title IS NOT NULL AND TRIM(ipr.title) <> ''

UNION ALL

SELECT 
    'research_project' AS category,
    proj.id::text AS activity_id,
    LOWER(TRIM(proj.faculty_email)) AS faculty_email,
    proj.academic_year::text AS academic_year,
    proj.project_title AS title,
    NULL::text AS indexing_type,
    NULL::text AS scope,
    proj.amount AS amount,
    proj.status AS status,
    proj.funding_agency AS agency,
    proj.role AS role,
    COALESCE(proj.self_score, 0) AS self_score,
    COALESCE(proj.hod_score, 0) AS hod_score,
    COALESCE(proj.director_score, 0) AS director_score,
    COALESCE(proj.dean_score, 0) AS dean_score,
    COALESCE(proj.vc_score, 0) AS vc_score,
    proj.created_at
FROM research_projects proj
WHERE proj.project_title IS NOT NULL AND TRIM(proj.project_title) <> ''

UNION ALL

SELECT 
    'research_proposal' AS category,
    prop.id::text AS activity_id,
    LOWER(TRIM(prop.faculty_email)) AS faculty_email,
    prop.academic_year::text AS academic_year,
    prop.proposal_title AS title,
    NULL::text AS indexing_type,
    NULL::text AS scope,
    prop.amount AS amount,
    prop.status AS status,
    prop.funding_agency AS agency,
    prop.role AS role,
    COALESCE(prop.self_score, 0) AS self_score,
    COALESCE(prop.hod_score, 0) AS hod_score,
    COALESCE(prop.director_score, 0) AS director_score,
    COALESCE(prop.dean_score, 0) AS dean_score,
    COALESCE(prop.vc_score, 0) AS vc_score,
    prop.created_at
FROM research_proposals prop
WHERE prop.proposal_title IS NOT NULL AND TRIM(prop.proposal_title) <> '';


-- 2. FACULTY RESEARCH SUMMARY VIEW
CREATE OR REPLACE VIEW vw_faculty_research_summary AS
SELECT 
    LOWER(TRIM(fp.email)) AS faculty_email,
    fp.employee_id,
    fp.full_name AS faculty_name,
    fp.school,
    fp.department,
    fp.designation,
    fp.is_active,
    COUNT(DISTINCT CASE WHEN act.category = 'journal_publication' THEN act.activity_id END) AS total_journals,
    COUNT(DISTINCT CASE WHEN act.category = 'book_publication' THEN act.activity_id END) AS total_books,
    COUNT(DISTINCT CASE WHEN act.category = 'patent' THEN act.activity_id END) AS total_patents,
    COUNT(DISTINCT CASE WHEN act.category = 'ipr' THEN act.activity_id END) AS total_ipr,
    COUNT(DISTINCT CASE WHEN act.category = 'research_project' THEN act.activity_id END) AS total_projects,
    COUNT(DISTINCT CASE WHEN act.category = 'research_proposal' THEN act.activity_id END) AS total_proposals,
    COALESCE(SUM(CASE WHEN act.category = 'research_project' THEN act.amount ELSE 0 END), 0) AS total_funding,
    COALESCE(SUM(act.vc_score), 0) AS total_vc_score,
    COUNT(DISTINCT act.category) AS research_diversity_score
FROM faculty_profiles fp
LEFT JOIN vw_research_activity_union act 
    ON LOWER(TRIM(fp.email)) = act.faculty_email
GROUP BY fp.email, fp.employee_id, fp.full_name, fp.school, fp.department, fp.designation, fp.is_active;


-- 3. DEPARTMENT RESEARCH SUMMARY VIEW
CREATE OR REPLACE VIEW vw_department_research_summary AS
SELECT 
    fp.school,
    fp.department,
    COUNT(DISTINCT fp.email) AS total_active_faculty,
    COUNT(DISTINCT CASE WHEN fsum.total_journals > 0 OR fsum.total_projects > 0 OR fsum.total_patents > 0 THEN fp.email END) AS research_active_faculty,
    COALESCE(SUM(fsum.total_journals), 0) AS total_journals,
    COALESCE(SUM(fsum.total_books), 0) AS total_books,
    COALESCE(SUM(fsum.total_patents), 0) AS total_patents,
    COALESCE(SUM(fsum.total_projects), 0) AS total_projects,
    COALESCE(SUM(fsum.total_funding), 0) AS total_funding,
    COALESCE(SUM(fsum.total_vc_score), 0) AS total_vc_score,
    ROUND(
        (COUNT(DISTINCT CASE WHEN fsum.total_journals > 0 OR fsum.total_projects > 0 OR fsum.total_patents > 0 THEN fp.email END)::numeric 
        / NULLIF(COUNT(DISTINCT fp.email), 0)::numeric) * 100, 2
    ) AS participation_rate
FROM faculty_profiles fp
LEFT JOIN vw_faculty_research_summary fsum 
    ON LOWER(TRIM(fp.email)) = fsum.faculty_email
WHERE fp.is_active = true
GROUP BY fp.school, fp.department;


-- 4. SCORE VARIANCE VIEW
CREATE OR REPLACE VIEW vw_research_score_variance AS
SELECT 
    act.activity_id,
    act.category,
    act.title,
    act.faculty_email,
    fp.full_name AS faculty_name,
    fp.department,
    fp.school,
    act.self_score,
    act.hod_score,
    act.director_score,
    act.dean_score,
    act.vc_score,
    (act.self_score - act.vc_score) AS self_to_vc_variance,
    CASE 
        WHEN act.self_score > 0 THEN ROUND((act.vc_score / act.self_score) * 100, 2)
        ELSE 100.0 
    END AS validation_ratio
FROM vw_research_activity_union act
JOIN faculty_profiles fp ON act.faculty_email = LOWER(TRIM(fp.email))
WHERE act.self_score <> act.vc_score;


-- 5. DATA QUALITY ALERTS VIEW
CREATE OR REPLACE VIEW vw_research_data_quality AS
SELECT 
    'Unmatched Faculty Email' AS alert_type,
    'Critical' AS severity,
    act.category,
    act.title,
    act.faculty_email,
    'Faculty email does not exist in faculty_profiles directory' AS description
FROM vw_research_activity_union act
LEFT JOIN faculty_profiles fp ON act.faculty_email = LOWER(TRIM(fp.email))
WHERE fp.email IS NULL

UNION ALL

SELECT 
    'Possible Duplicate Title' AS alert_type,
    'Warning' AS severity,
    act.category,
    act.title,
    act.faculty_email,
    'Duplicate title recorded multiple times for the same faculty' AS description
FROM vw_research_activity_union act
GROUP BY act.category, act.title, act.faculty_email
HAVING COUNT(*) > 1;

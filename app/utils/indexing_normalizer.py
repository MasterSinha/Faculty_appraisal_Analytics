def normalize_indexing(value: object) -> str:
    if value is None:
        return "Not specified"

    text = str(value).strip().lower()
    if not text:
        return "Not specified"

    if any(token in text for token in ("sci", "scie", "web of science", "wos")):
        return "SCI / Web of Science"
    if "scopus" in text:
        return "Scopus"
    if "ugc" in text:
        return "UGC"

    return "Other"


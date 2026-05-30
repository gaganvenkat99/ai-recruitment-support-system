-- ==============================
-- RESUMES TABLE (EXISTING)
-- ==============================
CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_name TEXT,
    email TEXT,
    skills TEXT,
    experience TEXT,
    education TEXT,
    resume_text TEXT,
    source TEXT
);

-- ==============================
-- JOBS TABLE (EXISTING)
-- ==============================
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_title TEXT,
    job_description TEXT
);

-- ==============================
-- USERS TABLE (NEW - FOR LOGIN)
-- ==============================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
);
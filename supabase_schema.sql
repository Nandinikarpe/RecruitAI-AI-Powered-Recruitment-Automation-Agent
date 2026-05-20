-- ============================================================
-- RecruitAI — Supabase Schema
-- Run this in your Supabase SQL Editor
-- ============================================================

-- Users (HR staff)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Jobs
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    required_skills TEXT[] DEFAULT '{}',
    experience_years INT DEFAULT 0,
    location TEXT NOT NULL,
    salary_range TEXT,
    created_by TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Candidates
CREATE TABLE IF NOT EXISTS candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    skills TEXT[] DEFAULT '{}',
    skills_missing TEXT[] DEFAULT '{}',
    experience_years FLOAT,
    education TEXT,
    resume_text TEXT,
    resume_url TEXT,
    ai_score FLOAT,
    ai_summary TEXT,
    ai_strengths TEXT[] DEFAULT '{}',
    ai_weaknesses TEXT[] DEFAULT '{}',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending','scheduled','completed','rejected','selected')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Interviews
CREATE TABLE IF NOT EXISTS interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    scheduled_at TIMESTAMPTZ NOT NULL,
    interview_type TEXT DEFAULT 'video',
    meeting_link TEXT,
    notes TEXT,
    status TEXT DEFAULT 'scheduled',
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Interview Questions (AI-generated)
CREATE TABLE IF NOT EXISTS interview_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    questions JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email Logs
CREATE TABLE IF NOT EXISTS email_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    email_type TEXT NOT NULL,
    to_email TEXT NOT NULL,
    subject TEXT,
    sent_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Storage bucket for resumes
INSERT INTO storage.buckets (id, name, public)
VALUES ('resumes', 'resumes', true)
ON CONFLICT (id) DO NOTHING;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_candidates_job_id ON candidates(job_id);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_interviews_candidate_id ON interviews(candidate_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_candidate_id ON email_logs(candidate_id);

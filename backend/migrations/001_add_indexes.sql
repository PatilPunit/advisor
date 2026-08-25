-- Deliverable 10: Database Optimization
-- ----------------------------------------
-- Run this directly against your EXISTING Postgres database:
--   psql -U postgres -d career_advisor -f migrations/001_add_indexes.sql
--
-- Why this is a separate SQL file instead of just editing models.py:
-- SQLAlchemy's Base.metadata.create_all() only creates tables that don't
-- exist yet - it NEVER alters existing tables to add indexes or columns.
-- (This is the exact same reason completed_at had to be added via ALTER
-- TABLE earlier in this project.) Editing index=True in models.py only
-- affects a brand-new database - it silently does nothing on your real,
-- already-running one. This script is what actually applies to your
-- live data.

-- Foreign key lookups (every "get all X for this user" query hits these)
CREATE INDEX IF NOT EXISTS idx_user_skills_user_id ON user_skills(user_id);
CREATE INDEX IF NOT EXISTS idx_user_projects_user_id ON user_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_resume_history_user_id ON resume_history(user_id);
CREATE INDEX IF NOT EXISTS idx_mentor_chats_user_id ON mentor_chats(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_career_recommendations_user_id ON career_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_job_matches_user_id ON job_matches(user_id);
CREATE INDEX IF NOT EXISTS idx_project_recommendations_user_id ON project_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_career_score_snapshots_user_id ON career_score_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_feedback_user_id ON recommendation_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);

-- Timestamp columns used in "last 7 days" / "this week" filters everywhere
-- (dashboard, weekly reports, notifications, admin analytics)
CREATE INDEX IF NOT EXISTS idx_user_activity_created_at ON user_activity(created_at);
CREATE INDEX IF NOT EXISTS idx_user_skills_completed_at ON user_skills(completed_at);
CREATE INDEX IF NOT EXISTS idx_user_projects_completed_at ON user_projects(completed_at);
CREATE INDEX IF NOT EXISTS idx_resume_history_upload_date ON resume_history(upload_date);
CREATE INDEX IF NOT EXISTS idx_career_score_snapshots_date ON career_score_snapshots(snapshot_date);

-- Career/skill grouping columns (admin analytics: "top careers", "top missing skills")
CREATE INDEX IF NOT EXISTS idx_career_recommendations_career ON career_recommendations(career);
CREATE INDEX IF NOT EXISTS idx_career_profile_target_career ON career_profile(target_career);

-- Composite index for the most common query shape: "this user's rows,
-- ordered by/filtered by time" - covers weekly report + notification checks
-- in a single index scan instead of two.
CREATE INDEX IF NOT EXISTS idx_user_skills_user_completed
  ON user_skills(user_id, completed, completed_at);
CREATE INDEX IF NOT EXISTS idx_user_projects_user_completed
  ON user_projects(user_id, completed, completed_at);

-- Users table - email is already unique+indexed by SQLAlchemy's
-- unique=True, index=True, but role is checked on every protected-route
-- request now (Deliverable 6/7), so index it too.
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
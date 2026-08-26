"""
file_storage.py
------------------
Deliverable 9: File Storage Architecture.

Local filesystem storage with per-user versioning, organized as:

    uploads/
      resumes/
        {user_id}/
          {timestamp}_{original_filename}.pdf   <- every version kept
      reports/
        {user_id}/
          weekly_report_{date}.json

This gives you real version history "for free" (every upload is a new
timestamped file, nothing is ever overwritten) - so a user's resume
history isn't just scores, it's the actual files too, which the current
resume_history table doesn't store.

CLOUD MIGRATION PATH (Deliverable 9's alternative: AWS S3 / Cloudinary /
Supabase Storage): every function here takes/returns a relative path
string, never assumes local disk elsewhere in the codebase. To move to
S3 later, you only need to change the internals of save_resume_file() /
get_resume_file_path() to upload/fetch from a bucket instead of local
disk - nothing calling this module needs to change.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
RESUMES_DIR = os.path.join(UPLOADS_DIR, "resumes")
REPORTS_DIR = os.path.join(UPLOADS_DIR, "reports")

os.makedirs(RESUMES_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def _safe_filename(filename: str) -> str:
    """Strips path separators etc. so a malicious filename can't escape the uploads directory."""
    return os.path.basename(filename).replace("..", "")


def save_resume_file(user_id: int, filename: str, file_bytes: bytes) -> str:
    """
    Saves a resume PDF under uploads/resumes/{user_id}/, timestamped so
    every version is preserved (never overwritten). Returns the relative
    path stored, suitable for saving in the database.
    """
    user_dir = os.path.join(RESUMES_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = _safe_filename(filename)
    stored_filename = f"{timestamp}_{safe_name}"
    full_path = os.path.join(user_dir, stored_filename)

    with open(full_path, "wb") as f:
        f.write(file_bytes)

    return os.path.relpath(full_path, BASE_DIR)


def list_resume_versions(user_id: int) -> List[dict]:
    """Returns every resume version on file for a user, newest first."""
    user_dir = os.path.join(RESUMES_DIR, str(user_id))
    if not os.path.isdir(user_dir):
        return []

    versions = []
    for filename in os.listdir(user_dir):
        full_path = os.path.join(user_dir, filename)
        versions.append({
            "filename": filename,
            "path": os.path.relpath(full_path, BASE_DIR),
            "uploaded_at": datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat(),
            "size_bytes": os.path.getsize(full_path),
        })

    versions.sort(key=lambda v: v["uploaded_at"], reverse=True)
    return versions


def get_resume_file_path(user_id: int, filename: str) -> Optional[str]:
    """Returns the full path to a specific stored resume version, or None if it doesn't exist."""
    safe_name = _safe_filename(filename)
    full_path = os.path.join(RESUMES_DIR, str(user_id), safe_name)
    return full_path if os.path.isfile(full_path) else None
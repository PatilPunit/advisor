import { useEffect, useState } from "react";

function SkillTracker({ userId, token, onProgressChange }) {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updatingSkill, setUpdatingSkill] = useState(null);

  const fetchSkills = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`http://127.0.0.1:8000/users/${userId}/skills`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Could not load your roadmap skills");
      const data = await response.json();
      setSkills(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId) fetchSkills();
  }, [userId]);

  const toggleSkill = async (skill) => {
    setUpdatingSkill(skill.skill_name);
    const newCompleted = !skill.completed;

    // Optimistic update - flips instantly in the UI
    setSkills((prev) =>
      prev.map((s) =>
        s.skill_name === skill.skill_name ? { ...s, completed: newCompleted } : s
      )
    );

    try {
      const response = await fetch(`http://127.0.0.1:8000/users/${userId}/skills`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ skill_name: skill.skill_name, completed: newCompleted }),
      });
      if (!response.ok) throw new Error("Could not save progress");

      // Let the parent (App.jsx) know, so it can refresh the Dashboard stats
      if (onProgressChange) onProgressChange();
    } catch (err) {
      // Roll back on failure
      setSkills((prev) =>
        prev.map((s) =>
          s.skill_name === skill.skill_name ? { ...s, completed: !newCompleted } : s
        )
      );
      setError(err.message);
    } finally {
      setUpdatingSkill(null);
    }
  };

  if (loading) return <p style={styles.status}>Loading your roadmap...</p>;

  if (skills.length === 0) {
    return (
      <div style={styles.card}>
        <h3 style={styles.heading}>Your Roadmap</h3>
        <p style={styles.status}>
          Set a career goal above to generate your personal skill roadmap.
        </p>
      </div>
    );
  }

  const completedCount = skills.filter((s) => s.completed).length;

  return (
    <div style={styles.card}>
      <div style={styles.headerRow}>
        <h3 style={styles.heading}>Your Roadmap</h3>
        <span style={styles.countLabel}>
          {completedCount}/{skills.length} completed
        </span>
      </div>

      {error && <p style={styles.error}>{error}</p>}

      <ul style={styles.list}>
        {skills.map((skill) => (
          <li key={skill.skill_name} style={styles.listItem}>
            <label style={styles.checkboxRow}>
              <input
                type="checkbox"
                checked={skill.completed}
                disabled={updatingSkill === skill.skill_name}
                onChange={() => toggleSkill(skill)}
                style={styles.checkbox}
              />
              <span
                style={{
                  ...styles.skillText,
                  color: skill.completed ? "#4ade80" : "#f5f5f5",
                  textDecoration: skill.completed ? "line-through" : "none",
                }}
              >
                {skill.skill_name}
              </span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}

const styles = {
  card: {
    width: "100%",
    maxWidth: "720px",
    padding: "20px",
    borderRadius: "10px",
    border: "1px solid #2a2a2a",
    backgroundColor: "#161616",
    fontFamily: "sans-serif",
  },
  headerRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "12px",
  },
  heading: {
    fontSize: "16px",
    fontWeight: 600,
    color: "#f5f5f5",
    margin: 0,
  },
  countLabel: {
    fontSize: "13px",
    color: "#999",
  },
  list: {
    listStyle: "none",
    padding: 0,
    margin: 0,
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  listItem: {
    display: "flex",
  },
  checkboxRow: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    cursor: "pointer",
  },
  checkbox: {
    width: "16px",
    height: "16px",
    cursor: "pointer",
    accentColor: "#4ade80",
  },
  skillText: {
    fontSize: "14px",
  },
  status: {
    color: "#999",
    fontSize: "13px",
  },
  error: {
    color: "#f87171",
    fontSize: "13px",
  },
};

export default SkillTracker;
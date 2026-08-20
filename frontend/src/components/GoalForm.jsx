import { useState } from "react";

const CAREER_OPTIONS = [
  "Data Scientist",
  "ML Engineer",
  "Data Analyst",
  "Full Stack Developer",
  "Cyber Security Analyst",
  "Android Developer",
  "Cloud Engineer",
  "AI Engineer",
];

function GoalForm({ userId, currentGoal, onGoalSet }) {
  const [career, setCareer] = useState(currentGoal || CAREER_OPTIONS[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSetGoal = async () => {
    setError("");
    setLoading(true);
    try {
      const response = await fetch(`http://127.0.0.1:8000/users/${userId}/goal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ career }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Could not set career goal");
      }
      onGoalSet();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.row}>
      <select
        value={career}
        onChange={(e) => setCareer(e.target.value)}
        style={styles.select}
      >
        {CAREER_OPTIONS.map((c) => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
      <button onClick={handleSetGoal} disabled={loading} style={styles.button}>
        {loading ? "Saving..." : currentGoal ? "Update Goal" : "Set Career Goal"}
      </button>
      {error && <span style={styles.error}>{error}</span>}
    </div>
  );
}

const styles = {
  row: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    flexWrap: "wrap",
  },
  select: {
    padding: "8px",
    fontSize: "13px",
    borderRadius: "6px",
    border: "1px solid #333",
    backgroundColor: "#0d0d0d",
    color: "#f5f5f5",
  },
  button: {
    padding: "8px 14px",
    fontSize: "13px",
    fontWeight: 600,
    color: "#fff",
    backgroundColor: "#2563eb",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
  },
  error: {
    color: "#f87171",
    fontSize: "12px",
  },
};

export default GoalForm;
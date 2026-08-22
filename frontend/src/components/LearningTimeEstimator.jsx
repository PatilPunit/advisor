import { useState } from "react";

const CAREER_OPTIONS = [
  "Data Scientist", "ML Engineer", "Data Analyst", "Full Stack Developer",
  "Cyber Security Analyst", "Android Developer", "Cloud Engineer", "AI Engineer",
];

function LearningTimeEstimator() {
  const [career, setCareer] = useState(CAREER_OPTIONS[0]);
  const [skillsInput, setSkillsInput] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleEstimate = async () => {
    const skills = skillsInput.split(",").map((s) => s.trim()).filter(Boolean);
    setError("");
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch("http://127.0.0.1:8000/learning-time", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ career, current_skills: skills }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not estimate");
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.card}>
      <h2 style={styles.heading}>Learning Time Predictor</h2>

      <select value={career} onChange={(e) => setCareer(e.target.value)} style={styles.select}>
        {CAREER_OPTIONS.map((c) => <option key={c} value={c}>{c}</option>)}
      </select>

      <input
        type="text"
        placeholder="Your current skills, e.g. Python, Pandas"
        value={skillsInput}
        onChange={(e) => setSkillsInput(e.target.value)}
        style={styles.input}
      />

      {error && <p style={styles.error}>{error}</p>}

      <button onClick={handleEstimate} disabled={loading} style={styles.button}>
        {loading ? "Estimating..." : "Estimate Timeline"}
      </button>

      {result && (
        <div style={styles.resultRow}>
          <div style={styles.statBox}>
            <p style={styles.statValue}>{result.estimated_duration}</p>
            <p style={styles.statLabel}>Estimated Duration</p>
          </div>
          <div style={styles.statBox}>
            <p style={styles.statValue}>{result.weekly_hours} hrs</p>
            <p style={styles.statLabel}>Weekly Hours</p>
          </div>
          <div style={styles.statBox}>
            <p style={styles.statValue}>{result.difficulty}</p>
            <p style={styles.statLabel}>Difficulty</p>
          </div>
        </div>
      )}
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
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  heading: { fontSize: "16px", fontWeight: 600, color: "#f5f5f5", margin: 0 },
  select: {
    padding: "8px",
    fontSize: "13px",
    borderRadius: "6px",
    border: "1px solid #333",
    backgroundColor: "#0d0d0d",
    color: "#f5f5f5",
  },
  input: {
    padding: "10px",
    fontSize: "14px",
    borderRadius: "6px",
    border: "1px solid #333",
    backgroundColor: "#0d0d0d",
    color: "#f5f5f5",
  },
  error: { color: "#f87171", fontSize: "13px", margin: 0 },
  button: {
    padding: "10px",
    fontSize: "14px",
    fontWeight: 600,
    color: "#fff",
    backgroundColor: "#2563eb",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
  },
  resultRow: {
    display: "flex",
    gap: "12px",
    paddingTop: "10px",
    borderTop: "1px solid #2a2a2a",
  },
  statBox: {
    flex: 1,
    textAlign: "center",
    padding: "12px",
    borderRadius: "8px",
    backgroundColor: "#0d0d0d",
    border: "1px solid #262626",
  },
  statValue: { fontSize: "16px", fontWeight: 700, color: "#4ade80", margin: "0 0 4px 0" },
  statLabel: { fontSize: "11px", color: "#999", margin: 0 },
};

export default LearningTimeEstimator;
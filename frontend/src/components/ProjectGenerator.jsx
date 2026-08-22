import { useState } from "react";

const DOMAINS = [
  "Data Science", "Data Analytics", "Machine Learning", "Full Stack + AI",
  "Cyber Security", "Android Development", "Cloud Computing", "AI",
];
const LEVELS = ["Beginner", "Intermediate", "Advanced"];

function ProjectGenerator({ userId }) {
  const [domain, setDomain] = useState(DOMAINS[0]);
  const [level, setLevel] = useState(LEVELS[0]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setError("");
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch("http://127.0.0.1:8000/backend/project-generator", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain, level, user_id: userId || null }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "No project found");
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.card}>
      <h2 style={styles.heading}>AI Project Generator</h2>

      <div style={styles.row}>
        <select value={domain} onChange={(e) => setDomain(e.target.value)} style={styles.select}>
          {DOMAINS.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
        <select value={level} onChange={(e) => setLevel(e.target.value)} style={styles.select}>
          {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>
        <button onClick={handleGenerate} disabled={loading} style={styles.button}>
          {loading ? "..." : "Generate"}
        </button>
      </div>

      {error && <p style={styles.error}>{error}</p>}

      {result && (
        <div style={styles.resultCard}>
          <p style={styles.projectName}>{result.project_name}</p>
          <div style={styles.metaRow}>
            <span style={styles.metaItem}>Domain: {result.domain}</span>
            <span style={styles.metaItem}>Difficulty: {result.difficulty}</span>
            <span style={styles.metaItem}>Timeline: {result.timeline}</span>
          </div>
          <p style={styles.datasetLine}>Dataset: {result.dataset}</p>
          <div style={styles.chipRow}>
            {result.skills.map((s) => (
              <span key={s} style={styles.chip}>{s}</span>
            ))}
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
    gap: "12px",
  },
  heading: { fontSize: "16px", fontWeight: 600, color: "#f5f5f5", margin: 0 },
  row: { display: "flex", gap: "10px", flexWrap: "wrap" },
  select: {
    padding: "8px",
    fontSize: "13px",
    borderRadius: "6px",
    border: "1px solid #333",
    backgroundColor: "#0d0d0d",
    color: "#f5f5f5",
  },
  button: {
    padding: "8px 16px",
    fontSize: "13px",
    fontWeight: 600,
    color: "#fff",
    backgroundColor: "#2563eb",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
  },
  error: { color: "#f87171", fontSize: "13px", margin: 0 },
  resultCard: {
    paddingTop: "14px",
    borderTop: "1px solid #2a2a2a",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  projectName: { fontSize: "17px", fontWeight: 700, color: "#f5f5f5", margin: 0 },
  metaRow: { display: "flex", gap: "16px", flexWrap: "wrap" },
  metaItem: { fontSize: "13px", color: "#999" },
  datasetLine: { fontSize: "13px", color: "#ccc", margin: 0 },
  chipRow: { display: "flex", flexWrap: "wrap", gap: "8px" },
  chip: {
    fontSize: "12px",
    fontWeight: 600,
    color: "#4ade80",
    border: "1px solid #4ade80",
    borderRadius: "999px",
    padding: "3px 10px",
  },
};

export default ProjectGenerator;
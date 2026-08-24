import { useEffect, useState } from "react";

const FACTOR_LABELS = {
  skills: "Skills",
  projects: "Projects",
  resume: "Resume",
  roadmap: "Roadmap",
  job_match: "Job Match",
};

function CareerTwin({ userId, refreshKey }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTwin = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(`http://127.0.0.1:8000/career-twin/${userId}`);
        const json = await response.json();
        if (!response.ok) throw new Error(json.detail || "Could not load Career Twin");
        setData(json);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    if (userId) fetchTwin();
  }, [userId, refreshKey]);

  if (loading) return <p style={styles.status}>Loading Career Twin...</p>;
  if (error) return <p style={styles.error}>{error}</p>;
  if (!data) return null;

  return (
    <div style={styles.card}>
      <div style={styles.headerRow}>
        <h2 style={styles.heading}>Career Twin</h2>
        <div style={styles.scoreCircle}>{data.readiness_score}</div>
      </div>
      <p style={styles.subtitle}>
        {data.name}'s digital career profile - targeting <strong>{data.target_career}</strong>
      </p>

      <div style={styles.breakdownList}>
        {Object.entries(data.readiness_breakdown).map(([key, val]) => (
          <div key={key} style={styles.breakdownRow}>
            <span style={styles.breakdownLabel}>{FACTOR_LABELS[key] || key}</span>
            <div style={styles.breakdownTrack}>
              <div
                style={{
                  ...styles.breakdownFill,
                  width: `${(val.points / val.max) * 100}%`,
                }}
              />
            </div>
            <span style={styles.breakdownValue}>{val.points}/{val.max}</span>
          </div>
        ))}
      </div>

      <div style={styles.skillChips}>
        {data.current_skills.length === 0 ? (
          <span style={styles.noSkills}>No skills marked complete yet</span>
        ) : (
          data.current_skills.map((s) => (
            <span key={s} style={styles.chip}>{s}</span>
          ))
        )}
      </div>
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
  },
  heading: { fontSize: "16px", fontWeight: 600, color: "#f5f5f5", margin: 0 },
  scoreCircle: {
    width: "48px",
    height: "48px",
    borderRadius: "50%",
    backgroundColor: "#2563eb",
    color: "#fff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: 700,
    fontSize: "16px",
  },
  subtitle: { fontSize: "13px", color: "#999", margin: "4px 0 16px 0" },
  breakdownList: { display: "flex", flexDirection: "column", gap: "10px", marginBottom: "16px" },
  breakdownRow: { display: "grid", gridTemplateColumns: "80px 1fr 50px", alignItems: "center", gap: "10px" },
  breakdownLabel: { fontSize: "13px", color: "#ccc" },
  breakdownTrack: { height: "8px", backgroundColor: "#2a2a2a", borderRadius: "999px", overflow: "hidden" },
  breakdownFill: { height: "100%", backgroundColor: "#4ade80", borderRadius: "999px" },
  breakdownValue: { fontSize: "12px", color: "#999", textAlign: "right" },
  skillChips: { display: "flex", flexWrap: "wrap", gap: "8px" },
  chip: {
    fontSize: "12px",
    fontWeight: 600,
    color: "#4ade80",
    border: "1px solid #4ade80",
    borderRadius: "999px",
    padding: "3px 10px",
  },
  noSkills: { fontSize: "13px", color: "#666", fontStyle: "italic" },
  status: { color: "#ccc", fontSize: "14px" },
  error: { color: "#f87171", fontSize: "14px" },
};

export default CareerTwin;
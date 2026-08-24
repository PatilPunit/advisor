import { useState } from "react";

function CareerSimulator({ userId }) {
  const [skillsInput, setSkillsInput] = useState("");
  const [steps, setSteps] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    const skills = skillsInput.split(",").map((s) => s.trim()).filter(Boolean);
    if (skills.length === 0) {
      setError("Enter at least one skill to simulate, e.g. Machine Learning, Deep Learning");
      return;
    }
    setError("");
    setLoading(true);
    setSteps(null);
    try {
      const response = await fetch("http://127.0.0.1:8000/career-simulator", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, hypothetical_skills: skills }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not run simulation");
      setSteps(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const maxScore = steps ? Math.max(...steps.map((s) => s.score), 1) : 1;

  return (
    <div style={styles.card}>
      <h2 style={styles.heading}>Career Simulator</h2>
      <p style={styles.subheading}>
        "What happens if I learn X, then Y?" - see your readiness score climb step by step.
      </p>

      <input
        type="text"
        placeholder="Machine Learning, Deep Learning"
        value={skillsInput}
        onChange={(e) => setSkillsInput(e.target.value)}
        style={styles.input}
      />

      {error && <p style={styles.error}>{error}</p>}

      <button onClick={handleSimulate} disabled={loading} style={styles.button}>
        {loading ? "Simulating..." : "Simulate"}
      </button>

      {steps && (
        <div style={styles.chartArea}>
          {steps.map((step, i) => (
            <div key={i} style={styles.barColumn}>
              <div style={styles.scoreLabel}>{step.score}</div>
              <div
                style={{
                  ...styles.bar,
                  height: `${(step.score / maxScore) * 140}px`,
                  backgroundColor: i === 0 ? "#60a5fa" : "#4ade80",
                }}
              />
              <div style={styles.stepLabel}>{step.label}</div>
            </div>
          ))}
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
  subheading: { fontSize: "13px", color: "#999", margin: 0 },
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
  chartArea: {
    display: "flex",
    alignItems: "flex-end",
    gap: "20px",
    paddingTop: "20px",
    borderTop: "1px solid #2a2a2a",
    minHeight: "200px",
    overflowX: "auto",
  },
  barColumn: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "6px",
    minWidth: "70px",
  },
  scoreLabel: { fontSize: "13px", fontWeight: 700, color: "#f5f5f5" },
  bar: { width: "36px", borderRadius: "6px 6px 0 0", transition: "height 0.4s ease" },
  stepLabel: { fontSize: "11px", color: "#999", textAlign: "center" },
};

export default CareerSimulator;
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

function SkillForm({ onResult }) {
  const [skillsInput, setSkillsInput] = useState("");
  const [interest, setInterest] = useState(CAREER_OPTIONS[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    const skills = skillsInput
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    if (skills.length === 0) {
      setError("Enter at least one skill, e.g. Python, Pandas, SQL");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ skills, interest }),
      });

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }

      const data = await response.json();
      onResult(data);
    } catch (err) {
      setError("Could not reach the advisor. Is the backend running on port 8000?");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.card}>
      <label style={styles.label} htmlFor="skills">
        Your skills
      </label>
      <input
        id="skills"
        type="text"
        placeholder="Python, Pandas, SQL"
        value={skillsInput}
        onChange={(e) => setSkillsInput(e.target.value)}
        style={styles.input}
      />

      <label style={styles.label} htmlFor="interest">
        Career interest
      </label>
      <select
        id="interest"
        value={interest}
        onChange={(e) => setInterest(e.target.value)}
        style={styles.input}
      >
        {CAREER_OPTIONS.map((career) => (
          <option key={career} value={career}>
            {career}
          </option>
        ))}
      </select>

      {error && <p style={styles.error}>{error}</p>}

      <button onClick={handleAnalyze} disabled={loading} style={styles.button}>
        {loading ? "Analyzing..." : "Analyze"}
      </button>
    </div>
  );
}

const styles = {
  card: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    maxWidth: "420px",
    padding: "20px",
    border: "1px solid #ddd",
    borderRadius: "10px",
    fontFamily: "sans-serif",
  },
  label: {
    fontSize: "14px",
    fontWeight: 600,
    marginTop: "8px",
  },
  input: {
    padding: "10px",
    fontSize: "14px",
    borderRadius: "6px",
    border: "1px solid #ccc",
  },
  button: {
    marginTop: "12px",
    padding: "10px",
    fontSize: "15px",
    fontWeight: 600,
    color: "#fff",
    backgroundColor: "#2563eb",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
  },
  error: {
    color: "#dc2626",
    fontSize: "13px",
    margin: 0,
  },
};

export default SkillForm;
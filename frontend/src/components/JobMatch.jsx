import { useState, useRef } from "react";

function JobMatch({ userId }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError("Please choose a resume PDF.");
      return;
    }
    if (!jobDescription.trim()) {
      setError("Please paste a job description.");
      return;
    }

    setError("");
    setLoading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("job_description", jobDescription);
      if (userId) formData.append("user_id", userId);

      const response = await fetch("http://127.0.0.1:8000/job-match", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (!response.ok) throw new Error(data.detail || "Could not match resume to job");

      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.card}>
      <h2 style={styles.heading}>Resume vs Job Matching</h2>

      <div style={styles.uploadRow}>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          style={styles.chooseButton}
        >
          Choose Resume PDF
        </button>
        <span style={styles.fileName}>
          {selectedFile ? selectedFile.name : "No file selected"}
        </span>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          onChange={(e) => setSelectedFile(e.target.files[0] || null)}
          style={{ display: "none" }}
        />
      </div>

      <textarea
        value={jobDescription}
        onChange={(e) => setJobDescription(e.target.value)}
        placeholder="Paste the job description here..."
        style={styles.textarea}
        rows={5}
      />

      {error && <p style={styles.error}>{error}</p>}

      <button onClick={handleAnalyze} disabled={loading} style={styles.analyzeButton}>
        {loading ? "Analyzing..." : "Match Resume to Job"}
      </button>

      {result && (
        <div style={styles.resultCard}>
          <div style={styles.scoreRow}>
            <span style={styles.scoreLabel}>Match Score</span>
            <span style={styles.scoreValue}>{result.match_score}%</span>
          </div>
          {result.note && <p style={styles.noteText}>{result.note}</p>}
          <div style={styles.progressTrack}>
            <div style={{ ...styles.progressFill, width: `${result.match_score}%` }} />
          </div>

          <h4 style={styles.subHeading}>Missing Keywords</h4>
          {result.missing_keywords.length === 0 ? (
            <p style={styles.goodNews}>None - great coverage!</p>
          ) : (
            <div style={styles.chipRow}>
              {result.missing_keywords.map((k) => (
                <span key={k} style={styles.chip}>{k}</span>
              ))}
            </div>
          )}

          <h4 style={styles.subHeading}>Recommended Actions</h4>
          <ul style={styles.actionList}>
            {result.recommended_actions.map((action, i) => (
              <li key={i} style={styles.actionItem}>{action}</li>
            ))}
          </ul>
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
  heading: {
    fontSize: "16px",
    fontWeight: 600,
    color: "#f5f5f5",
    margin: 0,
  },
  uploadRow: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  chooseButton: {
    padding: "8px 14px",
    fontSize: "13px",
    fontWeight: 600,
    color: "#f5f5f5",
    backgroundColor: "#262626",
    border: "1px solid #333",
    borderRadius: "6px",
    cursor: "pointer",
  },
  fileName: {
    fontSize: "13px",
    color: "#999",
  },
  textarea: {
    padding: "10px",
    fontSize: "14px",
    borderRadius: "6px",
    border: "1px solid #333",
    backgroundColor: "#0d0d0d",
    color: "#f5f5f5",
    fontFamily: "sans-serif",
    resize: "vertical",
  },
  analyzeButton: {
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
    color: "#f87171",
    fontSize: "13px",
    margin: 0,
  },
  resultCard: {
    marginTop: "8px",
    paddingTop: "16px",
    borderTop: "1px solid #2a2a2a",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  scoreRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "baseline",
  },
  scoreLabel: {
    fontSize: "14px",
    color: "#ccc",
  },
  scoreValue: {
    fontSize: "22px",
    fontWeight: 700,
    color: "#4ade80",
  },
  noteText: {
    fontSize: "12px",
    color: "#facc15",
    fontStyle: "italic",
    margin: 0,
  },
  progressTrack: {
    width: "100%",
    height: "10px",
    backgroundColor: "#2a2a2a",
    borderRadius: "999px",
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    backgroundColor: "#4ade80",
    borderRadius: "999px",
  },
  subHeading: {
    fontSize: "13px",
    fontWeight: 600,
    color: "#ccc",
    margin: "8px 0 4px 0",
  },
  goodNews: {
    fontSize: "13px",
    color: "#4ade80",
    margin: 0,
  },
  chipRow: {
    display: "flex",
    flexWrap: "wrap",
    gap: "8px",
  },
  chip: {
    fontSize: "12px",
    fontWeight: 600,
    color: "#f87171",
    border: "1px solid #f87171",
    borderRadius: "999px",
    padding: "3px 10px",
  },
  actionList: {
    margin: 0,
    paddingLeft: "18px",
    fontSize: "13px",
    color: "#f5f5f5",
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  actionItem: {},
};

export default JobMatch;
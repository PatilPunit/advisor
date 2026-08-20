import { useState, useRef } from "react";

function ResumeUpload({ userId }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setSelectedFile(file || null);
    setResult(null);
    setError("");
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError("Please choose a resume PDF first.");
      return;
    }
    if (!selectedFile.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      return;
    }

    setError("");
    setLoading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      if (userId) {
        formData.append("user_id", userId);
      }

      const response = await fetch("http://127.0.0.1:8000/resume-analyze", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Server responded with ${response.status}`);
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Could not analyze the resume. Is the backend running?");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.card}>
      <h2 style={styles.heading}>Resume Analyzer</h2>

      <div style={styles.uploadRow}>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          style={styles.chooseButton}
        >
          Choose PDF
        </button>
        <span style={styles.fileName}>
          {selectedFile ? selectedFile.name : "No file selected"}
        </span>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          style={{ display: "none" }}
        />
      </div>

      {error && <p style={styles.error}>{error}</p>}

      <button onClick={handleAnalyze} disabled={loading} style={styles.analyzeButton}>
        {loading ? "Analyzing..." : "Upload Resume"}
      </button>

      {result && (
        <div style={styles.resultCard}>
          <div style={styles.scoreRow}>
            <span style={styles.scoreLabel}>Resume Score</span>
            <span style={styles.scoreValue}>{result.score}%</span>
          </div>

          <div style={styles.progressTrack}>
            <div style={{ ...styles.progressFill, width: `${result.score}%` }} />
          </div>

          <p style={styles.recommendedCareer}>
            Recommended Career: <strong>{result.recommended_career}</strong>
          </p>

          <div style={styles.skillColumns}>
            <div>
              <h4 style={styles.skillHeading}>Detected Skills</h4>
              <ul style={styles.skillList}>
                {result.skills.map((skill) => (
                  <li key={skill} style={styles.detectedItem}>
                    ✓ {skill}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 style={styles.skillHeading}>Missing Skills</h4>
              <ul style={styles.skillList}>
                {result.missing.length === 0 ? (
                  <li style={styles.detectedItem}>None - great coverage!</li>
                ) : (
                  result.missing.map((skill) => (
                    <li key={skill} style={styles.missingItem}>
                      ✗ {skill}
                    </li>
                  ))
                )}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  card: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    maxWidth: "420px",
    padding: "20px",
    borderRadius: "10px",
    border: "1px solid #2a2a2a",
    backgroundColor: "#161616",
    fontFamily: "sans-serif",
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
  analyzeButton: {
    marginTop: "4px",
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
    marginTop: "10px",
    paddingTop: "16px",
    borderTop: "1px solid #2a2a2a",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
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
    transition: "width 0.4s ease",
  },
  recommendedCareer: {
    fontSize: "14px",
    color: "#f5f5f5",
    margin: 0,
  },
  skillColumns: {
    display: "flex",
    gap: "24px",
  },
  skillHeading: {
    fontSize: "13px",
    fontWeight: 600,
    color: "#ccc",
    margin: "0 0 6px 0",
  },
  skillList: {
    listStyle: "none",
    padding: 0,
    margin: 0,
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    fontSize: "13px",
  },
  detectedItem: {
    color: "#4ade80",
  },
  missingItem: {
    color: "#f87171",
  },
};

export default ResumeUpload;
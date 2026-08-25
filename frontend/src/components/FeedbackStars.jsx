import { useEffect, useState } from "react";

function WeeklyReport({ userId }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/learning-report/${userId}`);
        const json = await response.json();
        if (!response.ok) throw new Error(json.detail || "Could not load report");
        setData(json);
      } catch (err) {
        setError(err.message);
      }
    };
    if (userId) fetchReport();
  }, [userId]);

  if (error) return <p style={styles.error}>{error}</p>;
  if (!data) return <p style={styles.status}>Loading weekly report...</p>;

  const hasActivity = data.skills_completed.length > 0 || data.projects_completed.length > 0;

  return (
    <div style={styles.card}>
      <h2 style={styles.heading}>Weekly Report</h2>

      {data.career_score_delta !== null && (
        <p style={styles.deltaText}>
          Career Score: {data.career_score_delta >= 0 ? "+" : ""}{data.career_score_delta}
        </p>
      )}

      {!hasActivity ? (
        <p style={styles.emptyState}>No skills or projects completed this week yet.</p>
      ) : (
        <>
          {data.skills_completed.length > 0 && (
            <div>
              <h4 style={styles.subHeading}>Skills Completed</h4>
              <ul style={styles.list}>
                {data.skills_completed.map((s) => (
                  <li key={s} style={styles.listItem}>✓ {s}</li>
                ))}
              </ul>
            </div>
          )}
          {data.projects_completed.length > 0 && (
            <div>
              <h4 style={styles.subHeading}>Projects Completed</h4>
              <ul style={styles.list}>
                {data.projects_completed.map((p) => (
                  <li key={p} style={styles.listItem}>✓ {p}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      <p style={styles.engagementText}>
        Active on {data.engagement_days} day{data.engagement_days === 1 ? "" : "s"} this week
      </p>
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
  deltaText: { fontSize: "20px", fontWeight: 700, color: "#4ade80", margin: 0 },
  subHeading: { fontSize: "13px", fontWeight: 600, color: "#ccc", margin: "0 0 6px 0" },
  list: { margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "4px" },
  listItem: { fontSize: "13px", color: "#4ade80" },
  emptyState: { fontSize: "13px", color: "#666", fontStyle: "italic", margin: 0 },
  engagementText: { fontSize: "12px", color: "#999", margin: 0, paddingTop: "8px", borderTop: "1px solid #2a2a2a" },
  status: { color: "#ccc", fontSize: "14px" },
  error: { color: "#f87171", fontSize: "14px" },
};

export default WeeklyReport;
import { useEffect, useState } from "react";

function StatCard({ label, value }) {
  return (
    <div style={styles.statCard}>
      <p style={styles.statValue}>{value}</p>
      <p style={styles.statLabel}>{label}</p>
    </div>
  );
}

function Dashboard({ userId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!userId) return;

    const fetchDashboard = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(`http://127.0.0.1:8000/dashboard/${userId}`);
        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || "Could not load dashboard");
        }
        const json = await response.json();
        setData(json);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [userId]);

  if (!userId) return null;
  if (loading) return <p style={styles.status}>Loading dashboard...</p>;
  if (error) return <p style={styles.error}>{error}</p>;
  if (!data) return null;

  return (
    <div style={styles.card}>
      <h2 style={styles.welcome}>Welcome, {data.name}</h2>
      <p style={styles.goal}>
        Career Goal: <strong>{data.career_goal || "Not set yet"}</strong>
      </p>

      <div style={styles.statGrid}>
        <StatCard label="Career Match" value={`${Math.round(data.career_match)}%`} />
        <StatCard
          label="Resume Score"
          value={data.resume_score !== null ? `${data.resume_score}%` : "N/A"}
        />
        <StatCard
          label="Skills Completed"
          value={`${data.completed_skills}/${data.total_skills}`}
        />
        <StatCard
          label="Projects Completed"
          value={`${data.completed_projects}/${data.total_projects}`}
        />
        <StatCard label="Roadmap Progress" value={`${data.roadmap_progress}%`} />
      </div>

      {data.resume_history.length > 0 && (
        <div style={styles.historySection}>
          <h3 style={styles.historyHeading}>Resume Score History</h3>
          <div style={styles.historyRow}>
            {data.resume_history.map((entry, i) => (
              <div key={i} style={styles.historyPoint}>
                <div
                  style={{
                    ...styles.historyBar,
                    height: `${Math.max(entry.score, 5)}px`,
                  }}
                />
                <span style={styles.historyScore}>{entry.score}%</span>
              </div>
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
    padding: "24px",
    borderRadius: "12px",
    border: "1px solid #2a2a2a",
    backgroundColor: "#161616",
    fontFamily: "sans-serif",
    color: "#f5f5f5",
  },
  welcome: {
    fontSize: "22px",
    fontWeight: 700,
    margin: "0 0 4px 0",
  },
  goal: {
    fontSize: "14px",
    color: "#ccc",
    marginBottom: "20px",
  },
  statGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
    gap: "14px",
  },
  statCard: {
    padding: "16px",
    borderRadius: "10px",
    backgroundColor: "#0d0d0d",
    border: "1px solid #262626",
    textAlign: "center",
  },
  statValue: {
    fontSize: "24px",
    fontWeight: 700,
    color: "#4ade80",
    margin: "0 0 4px 0",
  },
  statLabel: {
    fontSize: "12px",
    color: "#999",
    margin: 0,
  },
  historySection: {
    marginTop: "24px",
    paddingTop: "20px",
    borderTop: "1px solid #2a2a2a",
  },
  historyHeading: {
    fontSize: "14px",
    fontWeight: 600,
    color: "#ccc",
    marginBottom: "14px",
  },
  historyRow: {
    display: "flex",
    alignItems: "flex-end",
    gap: "12px",
    height: "120px",
  },
  historyPoint: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "flex-end",
    gap: "6px",
    height: "100%",
  },
  historyBar: {
    width: "24px",
    backgroundColor: "#60a5fa",
    borderRadius: "4px 4px 0 0",
  },
  historyScore: {
    fontSize: "11px",
    color: "#999",
  },
  status: {
    color: "#ccc",
    fontSize: "14px",
  },
  error: {
    color: "#f87171",
    fontSize: "14px",
  },
};

export default Dashboard;
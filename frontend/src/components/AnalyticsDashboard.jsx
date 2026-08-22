import { useEffect, useState } from "react";

function StatCard({ label, value }) {
  return (
    <div style={styles.statCard}>
      <p style={styles.statValue}>{value ?? "N/A"}</p>
      <p style={styles.statLabel}>{label}</p>
    </div>
  );
}

function AnalyticsDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/analytics/summary");
        if (!response.ok) throw new Error("Could not load analytics");
        setData(await response.json());
      } catch (err) {
        setError(err.message);
      }
    };
    fetchSummary();
  }, []);

  if (error) return <p style={styles.error}>{error}</p>;
  if (!data) return <p style={styles.status}>Loading analytics...</p>;

  return (
    <div style={styles.card}>
      <h2 style={styles.heading}>Analytics Dashboard</h2>
      <div style={styles.statGrid}>
        <StatCard label="Most Chosen Career" value={data.most_chosen_career} />
        <StatCard label="Most Missing Skill" value={data.most_missing_skill} />
        <StatCard
          label="Average Resume Score"
          value={data.average_resume_score !== null ? `${data.average_resume_score}%` : null}
        />
        <StatCard label="Daily Active Users" value={data.daily_active_users} />
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
  heading: {
    fontSize: "16px",
    fontWeight: 600,
    color: "#f5f5f5",
    marginTop: 0,
    marginBottom: "14px",
  },
  statGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
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
    fontSize: "18px",
    fontWeight: 700,
    color: "#4ade80",
    margin: "0 0 4px 0",
  },
  statLabel: {
    fontSize: "12px",
    color: "#999",
    margin: 0,
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

export default AnalyticsDashboard;
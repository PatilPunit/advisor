import { useEffect, useState } from "react";

function StatCard({ label, value }) {
  return (
    <div style={styles.statCard}>
      <p style={styles.statValue}>{value ?? "N/A"}</p>
      <p style={styles.statLabel}>{label}</p>
    </div>
  );
}

function BarRow({ label, count, maxCount, color }) {
  return (
    <div style={styles.barRow}>
      <span style={styles.barLabel}>{label}</span>
      <div style={styles.barTrack}>
        <div style={{ ...styles.barFill, width: `${(count / maxCount) * 100}%`, backgroundColor: color }} />
      </div>
      <span style={styles.barCount}>{count}</span>
    </div>
  );
}

function AdminDashboard({ token }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/admin/analytics", {
          headers: { Authorization: `Bearer ${token}` },
        });
        const json = await response.json();
        if (!response.ok) throw new Error(json.detail || "Could not load admin analytics");
        setData(json);
      } catch (err) {
        setError(err.message);
      }
    };
    fetchData();
  }, []);

  if (error) return <p style={styles.error}>{error}</p>;
  if (!data) return <p style={styles.status}>Loading admin analytics...</p>;

  const maxCareerCount = Math.max(...data.top_careers.map((c) => c.count), 1);
  const maxSkillCount = Math.max(...data.top_missing_skills.map((s) => s.count), 1);

  return (
    <div style={styles.card}>
      <h2 style={styles.heading}>Admin Analytics</h2>
      <p style={styles.subtitle}>Founder-level metrics - not the user-facing dashboard.</p>

      <div style={styles.statGrid}>
        <StatCard label="Total Users" value={data.total_users} />
        <StatCard label="Active Users (7d)" value={data.active_users_7d} />
        <StatCard label="Retention" value={data.retention_pct !== null ? `${data.retention_pct}%` : null} />
        <StatCard label="Avg Resume Score" value={data.average_resume_score !== null ? `${data.average_resume_score}%` : null} />
        <StatCard label="Avg Feedback Rating" value={data.average_feedback_rating !== null ? `${data.average_feedback_rating}★` : null} />
      </div>

      <div style={styles.chartsRow}>
        <div style={styles.chartBlock}>
          <h4 style={styles.chartHeading}>Top Careers</h4>
          {data.top_careers.length === 0 ? (
            <p style={styles.emptyState}>No data yet</p>
          ) : (
            data.top_careers.map((c) => (
              <BarRow key={c.career} label={c.career} count={c.count} maxCount={maxCareerCount} color="#60a5fa" />
            ))
          )}
        </div>

        <div style={styles.chartBlock}>
          <h4 style={styles.chartHeading}>Top Missing Skills</h4>
          {data.top_missing_skills.length === 0 ? (
            <p style={styles.emptyState}>No data yet</p>
          ) : (
            data.top_missing_skills.map((s) => (
              <BarRow key={s.skill} label={s.skill} count={s.count} maxCount={maxSkillCount} color="#f87171" />
            ))
          )}
        </div>
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
  heading: { fontSize: "16px", fontWeight: 600, color: "#f5f5f5", margin: 0 },
  subtitle: { fontSize: "12px", color: "#666", margin: "2px 0 16px 0" },
  statGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
    gap: "12px",
    marginBottom: "20px",
  },
  statCard: {
    padding: "14px",
    borderRadius: "10px",
    backgroundColor: "#0d0d0d",
    border: "1px solid #262626",
    textAlign: "center",
  },
  statValue: { fontSize: "17px", fontWeight: 700, color: "#4ade80", margin: "0 0 4px 0" },
  statLabel: { fontSize: "11px", color: "#999", margin: 0 },
  chartsRow: { display: "flex", gap: "24px", flexWrap: "wrap" },
  chartBlock: { flex: 1, minWidth: "260px" },
  chartHeading: { fontSize: "13px", fontWeight: 600, color: "#ccc", marginBottom: "10px" },
  barRow: { display: "grid", gridTemplateColumns: "110px 1fr 30px", alignItems: "center", gap: "8px", marginBottom: "8px" },
  barLabel: { fontSize: "12px", color: "#f5f5f5", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  barTrack: { height: "8px", backgroundColor: "#2a2a2a", borderRadius: "999px", overflow: "hidden" },
  barFill: { height: "100%", borderRadius: "999px" },
  barCount: { fontSize: "12px", color: "#999", textAlign: "right" },
  emptyState: { fontSize: "12px", color: "#666", fontStyle: "italic" },
  status: { color: "#ccc", fontSize: "14px" },
  error: { color: "#f87171", fontSize: "14px" },
};

export default AdminDashboard;
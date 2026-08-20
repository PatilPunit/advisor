const DIFFICULTY_COLORS = {
  beginner: "#4ade80",
  intermediate: "#facc15",
  advanced: "#f87171",
};

function ProjectCard({ projectName, domain, difficulty }) {
  const difficultyColor =
    DIFFICULTY_COLORS[(difficulty || "").toLowerCase()] || "#999";

  return (
    <div style={styles.card}>
      <p style={styles.name}>{projectName}</p>
      {domain && <p style={styles.domain}>{domain}</p>}
      <span style={{ ...styles.badge, color: difficultyColor, borderColor: difficultyColor }}>
        {difficulty || "N/A"}
      </span>
    </div>
  );
}

const styles = {
  card: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    padding: "16px 18px",
    borderRadius: "10px",
    border: "1px solid #2a2a2a",
    backgroundColor: "#161616",
    minWidth: "180px",
  },
  name: {
    fontSize: "15px",
    fontWeight: 600,
    color: "#f5f5f5",
    margin: 0,
  },
  domain: {
    fontSize: "13px",
    color: "#999",
    margin: 0,
  },
  badge: {
    alignSelf: "flex-start",
    fontSize: "12px",
    fontWeight: 600,
    padding: "3px 10px",
    borderRadius: "999px",
    border: "1px solid",
  },
};

export default ProjectCard;
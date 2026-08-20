function SkillGapCard({ requiredSkills, userSkills }) {
  const userSkillsLower = userSkills.map((s) => s.trim().toLowerCase());

  const hasSkill = (skill) => userSkillsLower.includes(skill.trim().toLowerCase());

  const matchedCount = requiredSkills.filter(hasSkill).length;
  const totalCount = requiredSkills.length;
  const percent = totalCount > 0 ? Math.round((matchedCount / totalCount) * 100) : 0;

  return (
    <div style={styles.card}>
      <h3 style={styles.heading}>Required Skills</h3>

      <ul style={styles.list}>
        {requiredSkills.map((skill) => {
          const has = hasSkill(skill);
          return (
            <li key={skill} style={styles.listItem}>
              <span style={{ color: has ? "#4ade80" : "#f87171", fontWeight: 700 }}>
                {has ? "✓" : "✗"}
              </span>
              <span style={{ color: has ? "#f5f5f5" : "#999" }}>{skill}</span>
            </li>
          );
        })}
      </ul>

      <div style={styles.progressSection}>
        <div style={styles.progressLabel}>
          <span>Skill Match Progress</span>
          <span>{matchedCount} / {totalCount} ({percent}%)</span>
        </div>
        <div style={styles.progressTrack}>
          <div
            style={{
              ...styles.progressFill,
              width: `${percent}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
}

const styles = {
  card: {
    padding: "20px",
    borderRadius: "10px",
    border: "1px solid #2a2a2a",
    backgroundColor: "#161616",
  },
  heading: {
    fontSize: "16px",
    fontWeight: 600,
    color: "#f5f5f5",
    marginTop: 0,
    marginBottom: "12px",
  },
  list: {
    listStyle: "none",
    padding: 0,
    margin: "0 0 20px 0",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  listItem: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    fontSize: "14px",
  },
  progressSection: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  progressLabel: {
    display: "flex",
    justifyContent: "space-between",
    fontSize: "13px",
    color: "#ccc",
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
};

export default SkillGapCard;
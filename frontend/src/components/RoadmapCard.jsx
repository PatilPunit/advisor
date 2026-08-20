function RoadmapCard({ roadmap }) {
  return (
    <div style={styles.card}>
      <h3 style={styles.heading}>Learning Roadmap</h3>

      <div style={styles.timeline}>
        {roadmap.map((skill, index) => {
          const isLast = index === roadmap.length - 1;
          return (
            <div key={skill} style={styles.step}>
              <div style={styles.markerColumn}>
                <div style={styles.dot} />
                {!isLast && <div style={styles.line} />}
              </div>
              <span style={styles.skillText}>{skill}</span>
            </div>
          );
        })}
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
    marginBottom: "16px",
  },
  timeline: {
    display: "flex",
    flexDirection: "column",
  },
  step: {
    display: "flex",
    alignItems: "flex-start",
    gap: "14px",
  },
  markerColumn: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  dot: {
    width: "12px",
    height: "12px",
    borderRadius: "50%",
    backgroundColor: "#60a5fa",
    flexShrink: 0,
  },
  line: {
    width: "2px",
    flexGrow: 1,
    minHeight: "24px",
    backgroundColor: "#2a2a2a",
  },
  skillText: {
    fontSize: "14px",
    color: "#f5f5f5",
    paddingBottom: "24px",
  },
};

export default RoadmapCard;
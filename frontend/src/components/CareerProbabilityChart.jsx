function CareerProbabilityChart({ probabilities }) {
  const sorted = [...probabilities].sort((a, b) => b.probability - a.probability);

  return (
    <div style={styles.card}>
      <h3 style={styles.heading}>Career Probabilities</h3>
      <div style={styles.barList}>
        {sorted.map((item) => (
          <div key={item.career} style={styles.barRow}>
            <span style={styles.careerLabel}>{item.career}</span>
            <div style={styles.barTrack}>
              <div style={{ ...styles.barFill, width: `${item.probability}%` }} />
            </div>
            <span style={styles.percentLabel}>{item.probability}%</span>
          </div>
        ))}
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
  barList: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  barRow: {
    display: "grid",
    gridTemplateColumns: "140px 1fr 44px",
    alignItems: "center",
    gap: "10px",
  },
  careerLabel: {
    fontSize: "13px",
    color: "#f5f5f5",
  },
  barTrack: {
    height: "10px",
    backgroundColor: "#2a2a2a",
    borderRadius: "999px",
    overflow: "hidden",
  },
  barFill: {
    height: "100%",
    backgroundColor: "#60a5fa",
    borderRadius: "999px",
  },
  percentLabel: {
    fontSize: "12px",
    color: "#999",
    textAlign: "right",
  },
};

export default CareerProbabilityChart;
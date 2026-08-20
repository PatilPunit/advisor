function CareerCard({ career, score }) {
  return (
    <div style={styles.card}>
      <p style={styles.career}>{career}</p>
      <p style={styles.score}>Match: {score}%</p>
    </div>
  );
}

const styles = {
  card: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
    padding: "16px 20px",
    borderRadius: "10px",
    border: "1px solid #2a2a2a",
    backgroundColor: "#161616",
    minWidth: "160px",
  },
  career: {
    fontSize: "15px",
    fontWeight: 600,
    color: "#f5f5f5",
    margin: 0,
  },
  score: {
    fontSize: "14px",
    color: "#4ade80",
    margin: 0,
    fontWeight: 500,
  },
};

export default CareerCard;
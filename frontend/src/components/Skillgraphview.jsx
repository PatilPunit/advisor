import { useEffect, useState } from "react";

const CAREER_OPTIONS = [
  "Data Scientist", "ML Engineer", "Data Analyst", "Full Stack Developer",
  "Cyber Security Analyst", "Android Developer", "Cloud Engineer", "AI Engineer",
];

function SkillGraphView() {
  const [career, setCareer] = useState(CAREER_OPTIONS[0]);
  const [graph, setGraph] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchGraph = async () => {
      setError("");
      try {
        const response = await fetch(`http://127.0.0.1:8000/skill-graph/${encodeURIComponent(career)}`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Could not load skill graph");
        setGraph(data);
      } catch (err) {
        setError(err.message);
      }
    };
    fetchGraph();
  }, [career]);

  // Layout: root at top, level-by-level using edge depth from root (BFS)
  const layout = graph ? computeLayout(graph) : null;

  return (
    <div style={styles.card}>
      <h2 style={styles.heading}>Skill Graph</h2>

      <select value={career} onChange={(e) => setCareer(e.target.value)} style={styles.select}>
        {CAREER_OPTIONS.map((c) => <option key={c} value={c}>{c}</option>)}
      </select>

      {error && <p style={styles.error}>{error}</p>}

      {layout && (
        <svg width="100%" height={layout.height} viewBox={`0 0 ${layout.width} ${layout.height}`} style={styles.svg}>
          {layout.edges.map((e, i) => (
            <line
              key={i}
              x1={e.x1} y1={e.y1} x2={e.x2} y2={e.y2}
              stroke="#333" strokeWidth="2"
            />
          ))}
          {layout.nodes.map((n) => (
            <g key={n.label}>
              <circle cx={n.x} cy={n.y} r="8" fill={n.isRoot ? "#60a5fa" : "#4ade80"} />
              <text x={n.x} y={n.y - 16} textAnchor="middle" fill="#f5f5f5" fontSize="12" fontFamily="sans-serif">
                {n.label}
              </text>
            </g>
          ))}
        </svg>
      )}
    </div>
  );
}

// Simple BFS-based tree layout: assigns each node a depth (row) and spreads
// nodes at the same depth evenly across the width.
function computeLayout(graph) {
  const { nodes, edges } = graph;
  const childrenOf = {};
  edges.forEach((e) => {
    if (!childrenOf[e.from]) childrenOf[e.from] = [];
    childrenOf[e.from].push(e.to);
  });

  const root = nodes[0];
  const depths = { [root]: 0 };
  const queue = [root];
  while (queue.length) {
    const current = queue.shift();
    (childrenOf[current] || []).forEach((child) => {
      if (!(child in depths)) {
        depths[child] = depths[current] + 1;
        queue.push(child);
      }
    });
  }

  const levelCounts = {};
  nodes.forEach((n) => {
    const d = depths[n] ?? 0;
    levelCounts[d] = (levelCounts[d] || 0) + 1;
  });

  const width = 600;
  const rowHeight = 90;
  const maxDepth = Math.max(...Object.values(depths));
  const height = (maxDepth + 1) * rowHeight + 40;

  const levelIndex = {};
  const positions = {};
  nodes.forEach((n) => {
    const d = depths[n] ?? 0;
    const countAtLevel = levelCounts[d];
    const idx = levelIndex[d] || 0;
    levelIndex[d] = idx + 1;
    const x = ((idx + 1) / (countAtLevel + 1)) * width;
    const y = d * rowHeight + 40;
    positions[n] = { x, y };
  });

  const layoutNodes = nodes.map((n) => ({
    label: n,
    x: positions[n].x,
    y: positions[n].y,
    isRoot: n === root,
  }));

  const layoutEdges = edges.map((e) => ({
    x1: positions[e.from].x, y1: positions[e.from].y,
    x2: positions[e.to].x, y2: positions[e.to].y,
  }));

  return { nodes: layoutNodes, edges: layoutEdges, width, height };
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
    gap: "12px",
  },
  heading: { fontSize: "16px", fontWeight: 600, color: "#f5f5f5", margin: 0 },
  select: {
    padding: "8px",
    fontSize: "13px",
    borderRadius: "6px",
    border: "1px solid #333",
    backgroundColor: "#0d0d0d",
    color: "#f5f5f5",
    alignSelf: "flex-start",
  },
  error: { color: "#f87171", fontSize: "13px", margin: 0 },
  svg: { backgroundColor: "#0d0d0d", borderRadius: "8px" },
};

export default SkillGraphView;
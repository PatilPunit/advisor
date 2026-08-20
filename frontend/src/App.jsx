import { useState } from "react";
import SkillForm from "./components/SkillForm";
import CareerCard from "./components/CareerCard";
import Skillgapcard from "./components/Skillgapcard";
import RoadmapCard from "./components/RoadmapCard";
import ProjectCard from "./components/ProjectCard";
import ResumeUpload from "./components/ResumeUpload";

function App() {
  const [result, setResult] = useState(null);

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>AI Career Advisor</h1>

      <SkillForm onResult={setResult} />

      <ResumeUpload />

      {result && (
        <div style={styles.results}>

          <section>
            <h2 style={styles.sectionHeading}>Top Career Matches</h2>
            <div style={styles.cardRow}>
              {result.top_matches.map((match) => (
                <CareerCard
                  key={match.career}
                  career={match.career}
                  score={match.score}
                />
              ))}
            </div>
          </section>

          <section>
            <Skillgapcard
              requiredSkills={result.required_skills}
              userSkills={result.user_skills}
            />
          </section>

          <section>
            <RoadmapCard roadmap={result.roadmap} />
          </section>

          <section>
            <h2 style={styles.sectionHeading}>Recommended Projects</h2>
            <div style={styles.cardRow}>
              {result.projects.map((p) => (
                <ProjectCard
                  key={p.project_name}
                  projectName={p.project_name}
                  domain={p.domain}
                  difficulty={p.difficulty}
                />
              ))}
            </div>
          </section>

        </div>
      )}
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    backgroundColor: "#0d0d0d",
    color: "#f5f5f5",
    fontFamily: "sans-serif",
    padding: "40px 24px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "28px",
  },
  title: {
    fontSize: "32px",
    fontWeight: 700,
    margin: 0,
  },
  results: {
    width: "100%",
    maxWidth: "720px",
    display: "flex",
    flexDirection: "column",
    gap: "28px",
  },
  sectionHeading: {
    fontSize: "16px",
    fontWeight: 600,
    color: "#ccc",
    marginBottom: "12px",
  },
  cardRow: {
    display: "flex",
    gap: "14px",
    flexWrap: "wrap",
  },
};

export default App;
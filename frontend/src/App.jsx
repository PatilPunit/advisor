import { useState } from "react";
import SkillForm from "./components/SkillForm";

function App() {
  const [result, setResult] = useState(null);

  return (
    <div>
      <h1>AI Career Advisor</h1>
      <SkillForm onResult={setResult} />

      {result && (
        <div style={{ marginTop: "20px" }}>
          <h2>Recommended Career: {result.career}</h2>
          <p>Match Score: {result.match_score}%</p>

          <h3>Missing Skills</h3>
          <ul>
            {result.missing_skills.map((skill) => (
              <li key={skill}>{skill}</li>
            ))}
          </ul>

          <h3>Roadmap</h3>
          <ol>
            {result.roadmap.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>

          <h3>Suggested Projects</h3>
          <ul>
            {result.projects.map((p) => (
              <li key={p.project_name}>
                {p.project_name} ({p.difficulty || "N/A"} - {p.domain || "N/A"})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
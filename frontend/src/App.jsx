import { useState, useCallback } from "react";
import AuthForm from "./components/AuthForm";
import GoalForm from "./components/GoalForm";
import Dashboard from "./components/Dashboard";
import SkillTracker from "./components/SkillTracker";
import SkillForm from "./components/SkillForm";
import CareerCard from "./components/CareerCard";
import SkillGapCard from "./components/SkillGapCard";
import RoadmapCard from "./components/RoadmapCard";
import ProjectCard from "./components/ProjectCard";
import ResumeUpload from "./components/ResumeUpload";

function App() {
  const [user, setUser] = useState(null); // { id, name } once logged in
  const [dashboardKey, setDashboardKey] = useState(0); // bump to force Dashboard refetch
  const [result, setResult] = useState(null); // /recommend result (guest tool, no login required)

  const handleLogin = (loggedInUser) => {
    setUser(loggedInUser);
  };

  const handleLogout = () => {
    setUser(null);
    setResult(null);
  };

  const refreshDashboard = useCallback(() => {
    setDashboardKey((k) => k + 1);
  }, []);

  return (
    <div style={styles.page}>
      <div style={styles.headerRow}>
        <h1 style={styles.title}>AI Career Advisor</h1>
        {user && (
          <button onClick={handleLogout} style={styles.logoutButton}>
            Log Out
          </button>
        )}
      </div>

      {!user ? (
        <AuthForm onLogin={handleLogin} />
      ) : (
        <>
          <GoalForm userId={user.id} currentGoal={null} onGoalSet={refreshDashboard} />
          <SkillTracker key={dashboardKey} userId={user.id} onProgressChange={refreshDashboard} />
          <Dashboard key={dashboardKey} userId={user.id} />
          <ResumeUpload userId={user.id} />
        </>
      )}

      {/* Guest-friendly quick skill check - works with or without login */}
      <SkillForm onResult={setResult} />

      {result && (
        <div style={styles.results}>
          <section>
            <h2 style={styles.sectionHeading}>Top Career Matches</h2>
            <div style={styles.cardRow}>
              {result.top_matches.map((match) => (
                <CareerCard key={match.career} career={match.career} score={match.score} />
              ))}
            </div>
          </section>

          <section>
            <SkillGapCard
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
    gap: "24px",
  },
  headerRow: {
    width: "100%",
    maxWidth: "720px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  title: {
    fontSize: "32px",
    fontWeight: 700,
    margin: 0,
  },
  logoutButton: {
    padding: "8px 14px",
    fontSize: "13px",
    fontWeight: 600,
    color: "#f5f5f5",
    backgroundColor: "#262626",
    border: "1px solid #333",
    borderRadius: "6px",
    cursor: "pointer",
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
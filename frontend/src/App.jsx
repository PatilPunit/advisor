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
import MentorChat from "./components/MentorChat";
import JobMatch from "./components/JobMatch";
import AnalyticsDashboard from "./components/AnalyticsDashboard";
import ProjectGenerator from "./components/ProjectGenerator";
import LearningTimeEstimator from "./components/LearningTimeEstimator";

const TABS = ["Advisor", "Mentor", "Resume", "Job Match", "Projects", "Timeline", "Analytics"];

function App() {
  const [user, setUser] = useState(null);
  const [dashboardKey, setDashboardKey] = useState(0);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState("Advisor");

  const handleLogin = (loggedInUser) => setUser(loggedInUser);
  const handleLogout = () => {
    setUser(null);
    setResult(null);
  };
  const refreshDashboard = useCallback(() => setDashboardKey((k) => k + 1), []);

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

      {!user && <AuthForm onLogin={handleLogin} />}

      {user && (
        <>
          <div style={styles.tabRow}>
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  ...styles.tabButton,
                  ...(activeTab === tab ? styles.tabButtonActive : {}),
                }}
              >
                {tab}
              </button>
            ))}
          </div>

          {activeTab === "Advisor" && (
            <>
              <GoalForm userId={user.id} currentGoal={null} onGoalSet={refreshDashboard} />
              <SkillTracker key={`tracker-${dashboardKey}`} userId={user.id} onProgressChange={refreshDashboard} />
              <Dashboard key={`dashboard-${dashboardKey}`} userId={user.id} />

              <SkillForm onResult={setResult} />
              {result && (
                <div style={styles.results}>
                  <section>
                    <h2 style={styles.sectionHeading}>Top Career Matches</h2>
                    <div style={styles.cardRow}>
                      {result.top_matches.map((m) => (
                        <CareerCard key={m.career} career={m.career} score={m.score} />
                      ))}
                    </div>
                  </section>
                  <section>
                    <SkillGapCard requiredSkills={result.required_skills} userSkills={result.user_skills} />
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
            </>
          )}

          {activeTab === "Mentor" && <MentorChat userId={user.id} />}
          {activeTab === "Resume" && <ResumeUpload userId={user.id} />}
          {activeTab === "Job Match" && <JobMatch userId={user.id} />}
          {activeTab === "Projects" && <ProjectGenerator userId={user.id} />}
          {activeTab === "Timeline" && <LearningTimeEstimator />}
          {activeTab === "Analytics" && <AnalyticsDashboard />}
        </>
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
    gap: "20px",
  },
  headerRow: {
    width: "100%",
    maxWidth: "720px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  title: { fontSize: "32px", fontWeight: 700, margin: 0 },
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
  tabRow: {
    width: "100%",
    maxWidth: "720px",
    display: "flex",
    gap: "8px",
    flexWrap: "wrap",
  },
  tabButton: {
    padding: "8px 14px",
    fontSize: "13px",
    fontWeight: 600,
    color: "#999",
    backgroundColor: "#161616",
    border: "1px solid #2a2a2a",
    borderRadius: "6px",
    cursor: "pointer",
  },
  tabButtonActive: {
    color: "#fff",
    backgroundColor: "#2563eb",
    borderColor: "#2563eb",
  },
  results: {
    width: "100%",
    maxWidth: "720px",
    display: "flex",
    flexDirection: "column",
    gap: "28px",
  },
  sectionHeading: { fontSize: "16px", fontWeight: 600, color: "#ccc", marginBottom: "12px" },
  cardRow: { display: "flex", gap: "14px", flexWrap: "wrap" },
};

export default App;
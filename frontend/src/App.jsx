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
import CareerTwin from "./components/CareerTwin";
import CareerSimulator from "./components/CareerSimulator";
import WeeklyReport from "./components/WeeklyReport";
import NotificationBanner from "./components/NotificationBanner";
import SkillGraphView from "./components/SkillGraphView";
import AdminDashboard from "./components/AdminDashboard";
import FeedbackStars from "./components/FeedbackStars";

const TABS = [
  "Advisor", "Career Twin", "Simulator", "Mentor", "Companion",
  "Resume", "Job Match", "Projects", "Timeline", "Skill Graph",
  "Analytics", "Admin",
];

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
          <NotificationBanner userId={user.id} />

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
                    <div style={{ marginTop: "10px" }}>
                      <FeedbackStars userId={user.id} recommendationType="roadmap" reference={result.career} />
                    </div>
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

          {activeTab === "Career Twin" && (
            <CareerTwin userId={user.id} refreshKey={dashboardKey} />
          )}

          {activeTab === "Simulator" && <CareerSimulator userId={user.id} />}

          {activeTab === "Mentor" && <MentorChat userId={user.id} />}

          {activeTab === "Companion" && (
            <MentorChat
              userId={user.id}
              endpoint="http://127.0.0.1:8000/companion/chat"
              title="AI Learning Companion"
              subtitle="I know your resume, roadmap, projects, and career goal - ask me things like 'what project should I do next?'"
            />
          )}

          {activeTab === "Resume" && <ResumeUpload userId={user.id} />}
          {activeTab === "Job Match" && <JobMatch userId={user.id} />}
          {activeTab === "Projects" && (
            <>
              <ProjectGenerator userId={user.id} />
              <div style={{ maxWidth: "720px", width: "100%" }}>
                <FeedbackStars userId={user.id} recommendationType="project" />
              </div>
            </>
          )}
          {activeTab === "Timeline" && <LearningTimeEstimator />}
          {activeTab === "Skill Graph" && <SkillGraphView />}

          {activeTab === "Analytics" && (
            <>
              <WeeklyReport userId={user.id} />
              <AnalyticsDashboard />
            </>
          )}

          {activeTab === "Admin" && <AdminDashboard />}
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
    borderWidth: "1px",
    borderStyle: "solid",
    borderColor: "#333",
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
    borderWidth: "1px",
    borderStyle: "solid",
    borderColor: "#2a2a2a",
    borderRadius: "6px",
    cursor: "pointer",
  },
  tabButtonActive: {
    color: "#fff",
    backgroundColor: "#2563eb",
    borderWidth: "1px",
    borderStyle: "solid",
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
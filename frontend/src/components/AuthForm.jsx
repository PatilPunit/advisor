import { useState } from "react";

function AuthForm({ onLogin }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const resetFields = () => {
    setError("");
  };

  const switchMode = (newMode) => {
    setMode(newMode);
    resetFields();
  };

  const handleSubmit = async () => {
    if (!email.trim() || !password.trim() || (mode === "register" && !name.trim())) {
      setError("Please fill in all fields.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      if (mode === "register") {
        const response = await fetch("http://127.0.0.1:8000/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, email, password }),
        });
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Registration failed");
        }

        // Auto-login right after successful registration
        onLogin({ id: data.id, name: data.name });
      } else {
        const response = await fetch("http://127.0.0.1:8000/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Login failed");
        }
        if (!data.success) {
          throw new Error(data.message || "Invalid email or password");
        }

        onLogin({ id: data.user_id, name: data.name });
      }
    } catch (err) {
      setError(err.message || "Could not reach the server. Is the backend running?");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.card}>
      <div style={styles.tabRow}>
        <button
          onClick={() => switchMode("login")}
          style={{
            ...styles.tab,
            ...(mode === "login" ? styles.tabActive : {}),
          }}
        >
          Log In
        </button>
        <button
          onClick={() => switchMode("register")}
          style={{
            ...styles.tab,
            ...(mode === "register" ? styles.tabActive : {}),
          }}
        >
          Register
        </button>
      </div>

      {mode === "register" && (
        <>
          <label style={styles.label} htmlFor="name">Name</label>
          <input
            id="name"
            type="text"
            placeholder="Jarad"
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={styles.input}
          />
        </>
      )}

      <label style={styles.label} htmlFor="email">Email</label>
      <input
        id="email"
        type="email"
        placeholder="jarad@gmail.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        style={styles.input}
      />

      <label style={styles.label} htmlFor="password">Password</label>
      <input
        id="password"
        type="password"
        placeholder="••••••••"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        style={styles.input}
      />

      {error && <p style={styles.error}>{error}</p>}

      <button onClick={handleSubmit} disabled={loading} style={styles.submitButton}>
        {loading ? "Please wait..." : mode === "login" ? "Log In" : "Create Account"}
      </button>
    </div>
  );
}

const styles = {
  card: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    maxWidth: "380px",
    padding: "20px",
    borderRadius: "10px",
    border: "1px solid #2a2a2a",
    backgroundColor: "#161616",
    fontFamily: "sans-serif",
  },
  tabRow: {
    display: "flex",
    gap: "8px",
    marginBottom: "6px",
  },
  tab: {
    flex: 1,
    padding: "8px",
    fontSize: "13px",
    fontWeight: 600,
    color: "#999",
    backgroundColor: "#0d0d0d",
    border: "1px solid #262626",
    borderRadius: "6px",
    cursor: "pointer",
  },
  tabActive: {
    color: "#fff",
    backgroundColor: "#2563eb",
    borderColor: "#2563eb",
  },
  label: {
    fontSize: "13px",
    fontWeight: 600,
    color: "#ccc",
  },
  input: {
    padding: "10px",
    fontSize: "14px",
    borderRadius: "6px",
    border: "1px solid #333",
    backgroundColor: "#0d0d0d",
    color: "#f5f5f5",
  },
  submitButton: {
    marginTop: "10px",
    padding: "10px",
    fontSize: "15px",
    fontWeight: 600,
    color: "#fff",
    backgroundColor: "#2563eb",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
  },
  error: {
    color: "#f87171",
    fontSize: "13px",
    margin: 0,
  },
};

export default AuthForm;
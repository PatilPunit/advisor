import { useState, useRef, useEffect } from "react";

function MentorChat({
  userId,
  endpoint = "http://127.0.0.1:8000/mentor/chat",
  title = "AI Mentor",
  subtitle = 'Ask things like: "I know Python and SQL. Should I learn Data Science or ML Engineering?"',
}) {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleAsk = async () => {
    const q = question.trim();
    if (!q) return;

    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, user_id: userId || null }),
      });
      const data = await response.json();

      if (!response.ok) throw new Error(data.detail || "Mentor could not respond");

      setMessages((prev) => [...prev, { role: "mentor", text: data.answer }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "mentor", text: `Error: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  return (
    <div style={styles.card}>
      <h2 style={styles.heading}>{title}</h2>
      <p style={styles.subheading}>{subtitle}</p>

      <div style={styles.chatBox}>
        {messages.length === 0 && (
          <p style={styles.emptyState}>No messages yet - ask your first career question.</p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              ...styles.bubble,
              ...(m.role === "user" ? styles.userBubble : styles.mentorBubble),
            }}
          >
            {m.text}
          </div>
        ))}
        {loading && <div style={{ ...styles.bubble, ...styles.mentorBubble }}>Thinking...</div>}
        <div ref={bottomRef} />
      </div>

      <div style={styles.inputRow}>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask your career question..."
          style={styles.textarea}
          rows={2}
        />
        <button onClick={handleAsk} disabled={loading} style={styles.sendButton}>
          {loading ? "..." : "Ask"}
        </button>
      </div>
    </div>
  );
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
  heading: {
    fontSize: "16px",
    fontWeight: 600,
    color: "#f5f5f5",
    margin: 0,
  },
  subheading: {
    fontSize: "13px",
    color: "#999",
    margin: 0,
  },
  chatBox: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    maxHeight: "320px",
    overflowY: "auto",
    padding: "4px",
  },
  emptyState: {
    fontSize: "13px",
    color: "#666",
    fontStyle: "italic",
  },
  bubble: {
    padding: "10px 14px",
    borderRadius: "10px",
    fontSize: "14px",
    lineHeight: 1.5,
    maxWidth: "85%",
    whiteSpace: "pre-wrap",
  },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: "#2563eb",
    color: "#fff",
  },
  mentorBubble: {
    alignSelf: "flex-start",
    backgroundColor: "#0d0d0d",
    border: "1px solid #262626",
    color: "#f5f5f5",
  },
  inputRow: {
    display: "flex",
    gap: "10px",
  },
  textarea: {
    flex: 1,
    padding: "10px",
    fontSize: "14px",
    borderRadius: "6px",
    border: "1px solid #333",
    backgroundColor: "#0d0d0d",
    color: "#f5f5f5",
    resize: "none",
    fontFamily: "sans-serif",
  },
  sendButton: {
    padding: "0 18px",
    fontSize: "14px",
    fontWeight: 600,
    color: "#fff",
    backgroundColor: "#2563eb",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
  },
};

export default MentorChat;
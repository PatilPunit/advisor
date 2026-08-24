import { useEffect, useState } from "react";

function NotificationBanner({ userId }) {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/notifications/${userId}`);
        if (!response.ok) return;
        const data = await response.json();
        setNotifications(data.filter((n) => !n.is_read));
      } catch {
        // silently ignore - notifications are non-critical
      }
    };
    if (userId) fetchNotifications();
  }, [userId]);

  const dismiss = async (id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
    try {
      await fetch(`http://127.0.0.1:8000/notifications/${id}/read`, { method: "POST" });
    } catch {
      // best-effort - already removed from UI
    }
  };

  if (notifications.length === 0) return null;

  return (
    <div style={styles.container}>
      {notifications.map((n) => (
        <div key={n.id} style={styles.banner}>
          <span style={styles.message}>{n.message}</span>
          <button onClick={() => dismiss(n.id)} style={styles.dismissButton}>
            Dismiss
          </button>
        </div>
      ))}
    </div>
  );
}

const styles = {
  container: {
    width: "100%",
    maxWidth: "720px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  banner: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 16px",
    borderRadius: "8px",
    backgroundColor: "#2a1e05",
    border: "1px solid #facc15",
    fontFamily: "sans-serif",
  },
  message: { fontSize: "13px", color: "#facc15" },
  dismissButton: {
    padding: "4px 10px",
    fontSize: "12px",
    fontWeight: 600,
    color: "#facc15",
    backgroundColor: "transparent",
    border: "1px solid #facc15",
    borderRadius: "6px",
    cursor: "pointer",
  },
};

export default NotificationBanner;
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";
import { saveAuth } from "@/lib/auth";
import { Bot, Eye, EyeOff, Loader2 } from "lucide-react";

type Mode = "login" | "register";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [form, setForm] = useState({ username: "", password: "", email: "" });
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res =
        mode === "login"
          ? await auth.login(form.username, form.password)
          : await auth.register(form.username, form.password, form.email || undefined);
      saveAuth(res.access_token, res.username, res.role);
      router.push("/chat");
    } catch (err: any) {
      setError(err.message || "Đã có lỗi xảy ra");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      {/* Background glow */}
      <div style={styles.glow} />

      <div className="glass-card" style={styles.card}>
        {/* Header */}
        <div style={styles.header}>
          <div style={styles.logoWrap}>
            <Bot size={32} color="#6c63ff" />
          </div>
          <h1 style={styles.title}>AI Chatbot Điện Tử</h1>
          <p style={styles.subtitle}>Trợ lý mua sắm thông minh</p>
        </div>

        {/* Tabs */}
        <div style={styles.tabs}>
          {(["login", "register"] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => { setMode(m); setError(""); }}
              style={{ ...styles.tab, ...(mode === m ? styles.tabActive : {}) }}
            >
              {m === "login" ? "Đăng nhập" : "Đăng ký"}
            </button>
          ))}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.field}>
            <label style={styles.label}>Tên đăng nhập</label>
            <input
              style={styles.input}
              type="text"
              placeholder="username"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              required
              autoFocus
            />
          </div>

          {mode === "register" && (
            <div style={styles.field}>
              <label style={styles.label}>Email (tuỳ chọn)</label>
              <input
                style={styles.input}
                type="email"
                placeholder="email@example.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
          )}

          <div style={styles.field}>
            <label style={styles.label}>Mật khẩu</label>
            <div style={{ position: "relative" }}>
              <input
                style={{ ...styles.input, paddingRight: 44 }}
                type={showPwd ? "text" : "password"}
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
                minLength={4}
              />
              <button
                type="button"
                onClick={() => setShowPwd(!showPwd)}
                style={styles.eyeBtn}
              >
                {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {error && <p style={styles.error}>⚠️ {error}</p>}

          <button className="btn-accent" type="submit" disabled={loading} style={{ width: "100%", marginTop: 8 }}>
            {loading ? (
              <span style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "center" }}>
                <Loader2 size={16} style={{ animation: "spin 1s linear infinite" }} />
                Đang xử lý...
              </span>
            ) : mode === "login" ? "Đăng nhập" : "Tạo tài khoản"}
          </button>
        </form>

        <p style={styles.switchText}>
          {mode === "login" ? "Chưa có tài khoản? " : "Đã có tài khoản? "}
          <button onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
            style={styles.switchBtn}>
            {mode === "login" ? "Đăng ký ngay" : "Đăng nhập"}
          </button>
        </p>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "var(--bg-primary)",
    position: "relative",
    overflow: "hidden",
  },
  glow: {
    position: "absolute",
    width: 600,
    height: 600,
    borderRadius: "50%",
    background: "radial-gradient(circle, rgba(108,99,255,0.15) 0%, transparent 70%)",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    pointerEvents: "none",
  },
  card: {
    width: "100%",
    maxWidth: 420,
    padding: "40px 36px",
    position: "relative",
    zIndex: 1,
  },
  header: { textAlign: "center", marginBottom: 28 },
  logoWrap: {
    width: 60, height: 60,
    borderRadius: 16,
    background: "rgba(108,99,255,0.15)",
    border: "1px solid rgba(108,99,255,0.3)",
    display: "inline-flex", alignItems: "center", justifyContent: "center",
    marginBottom: 14,
  },
  title: { fontSize: 22, fontWeight: 700, margin: "0 0 6px", color: "var(--text-primary)" },
  subtitle: { fontSize: 13, color: "var(--text-secondary)", margin: 0 },
  tabs: {
    display: "flex",
    background: "var(--bg-secondary)",
    borderRadius: 10,
    padding: 4,
    marginBottom: 28,
    gap: 4,
  },
  tab: {
    flex: 1, padding: "8px 0", border: "none", borderRadius: 8,
    background: "transparent", color: "var(--text-secondary)",
    fontSize: 14, fontWeight: 500, cursor: "pointer", transition: "all 0.2s",
  },
  tabActive: {
    background: "var(--bg-card)",
    color: "var(--text-primary)",
    boxShadow: "0 1px 6px rgba(0,0,0,0.3)",
  },
  form: { display: "flex", flexDirection: "column", gap: 16 },
  field: { display: "flex", flexDirection: "column", gap: 6 },
  label: { fontSize: 13, fontWeight: 500, color: "var(--text-secondary)" },
  input: {
    width: "100%", padding: "11px 14px",
    background: "var(--bg-secondary)", border: "1px solid var(--border)",
    borderRadius: 10, color: "var(--text-primary)", fontSize: 14,
    outline: "none", transition: "border-color 0.2s",
  },
  eyeBtn: {
    position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)",
    background: "none", border: "none", color: "var(--text-secondary)",
    cursor: "pointer", padding: 4, display: "flex", alignItems: "center",
  },
  error: {
    fontSize: 13, color: "var(--danger)",
    background: "rgba(239,68,68,0.1)", borderRadius: 8,
    padding: "8px 12px", margin: 0,
  },
  switchText: { textAlign: "center", fontSize: 13, color: "var(--text-secondary)", marginTop: 20, marginBottom: 0 },
  switchBtn: {
    background: "none", border: "none", color: "var(--accent)",
    cursor: "pointer", fontSize: 13, fontWeight: 600, padding: 0,
  },
};

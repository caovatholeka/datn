"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { getAuth, clearAuth, isAdmin } from "@/lib/auth";
import { chat, Session, Message } from "@/lib/api";
import {
  Bot, User, Send, Plus, Trash2, LogOut, ShieldCheck,
  Paperclip, X, MessageSquare, Loader2, ChevronLeft, ChevronRight,
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface LocalMessage {
  id: string;
  role: "user" | "assistant";
  content: string;         // pipeline query (enriched)
  displayText?: string;    // text hiển thị
  imageUrl?: string;       // preview ảnh
  streaming?: boolean;     // đang stream
}

export default function ChatPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [admin, setAdmin] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<(() => void) | null>(null);
  const autoLoaded = useRef(false); // tránh auto-select nhiều lần

  // ── Auth guard ─────────────────────────────────────────
  useEffect(() => {
    const auth = getAuth();
    if (!auth) { router.replace("/login"); return; }
    setUsername(auth.username);
    setAdmin(auth.role === "admin");
    loadSessions(true); // true = auto-select session gần nhất
  }, []);

  // ── Auto scroll ─────────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Load sessions ───────────────────────────────────────
  const loadSessions = async (autoSelect = false) => {
    try {
      const data = await chat.getSessions();
      setSessions(data);
      // Lần đầu vào trang: tự động mở session gần nhất
      if (autoSelect && !autoLoaded.current && data.length > 0) {
        autoLoaded.current = true;
        await selectSession(data[0].id);
      }
    } catch {
      router.replace("/login");
    }
  };

  // ── Select session ──────────────────────────────────────
  const selectSession = async (id: string) => {
    setActiveSession(id);
    const msgs = await chat.getMessages(id);
    setMessages(
      msgs.map((m) => ({
        id: String(m.id),
        role: m.role as "user" | "assistant",
        content: m.content,
        displayText: m.display_text ?? m.content,
      }))
    );
  };

  // ── New session ─────────────────────────────────────────
  const newSession = () => {
    setActiveSession(null);
    setMessages([]);
    setInput("");
    clearImage();
  };

  // ── Delete session ──────────────────────────────────────
  const deleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    await chat.deleteSession(id);
    setSessions((prev) => prev.filter((s) => s.id !== id));
    if (activeSession === id) newSession();
  };

  // ── Image ──────────────────────────────────────────────
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = () => setImagePreview(reader.result as string);
    reader.readAsDataURL(file);
  };

  const clearImage = () => {
    setImageFile(null);
    setImagePreview(null);
    if (fileRef.current) fileRef.current.value = "";
  };

  // ── Send message ────────────────────────────────────────
  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text && !imageFile) return;
    if (sending) return;

    setSending(true);
    const userMsg: LocalMessage = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      displayText: text,
      imageUrl: imagePreview ?? undefined,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    clearImage();

    // Prepare image base64
    let imageB64: string | undefined;
    if (imageFile) {
      const bytes = await imageFile.arrayBuffer();
      imageB64 = btoa(String.fromCharCode(...new Uint8Array(bytes)));
    }

    // Add streaming placeholder
    const botId = (Date.now() + 1).toString();
    setMessages((prev) => [
      ...prev,
      { id: botId, role: "assistant", content: "", streaming: true },
    ]);

    try {
      const token = localStorage.getItem("token");
      const controller = new AbortController();
      abortRef.current = () => controller.abort();

      const res = await fetch(`${API}/chat/send`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          session_id: activeSession,
          message: text || "Cho tôi biết sản phẩm trong ảnh này",
          image_b64: imageB64 ?? null,
        }),
        signal: controller.signal,
      });

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let fullText = "";
      let newSessionId = activeSession;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n").filter((l) => l.startsWith("data: "));
        for (const line of lines) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === "token") {
              fullText += data.content;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === botId ? { ...m, content: fullText } : m
                )
              );
            } else if (data.type === "done") {
              newSessionId = data.session_id;
              setActiveSession(data.session_id);
            } else if (data.type === "error") {
              fullText = "❌ " + data.content;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === botId ? { ...m, content: fullText } : m
                )
              );
            }
          } catch {}
        }
      }

      // Stop streaming cursor
      setMessages((prev) =>
        prev.map((m) => (m.id === botId ? { ...m, streaming: false } : m))
      );

      // Refresh session list (không auto-select lại)
      await loadSessions(false);
      if (newSessionId && newSessionId !== activeSession) {
        setActiveSession(newSessionId);
      }
    } catch (err: any) {
      if (err.name !== "AbortError") {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === botId
              ? { ...m, content: "❌ Lỗi kết nối. Vui lòng thử lại.", streaming: false }
              : m
          )
        );
      }
    } finally {
      setSending(false);
    }
  }, [input, imageFile, imagePreview, activeSession, sending]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const logout = () => { clearAuth(); router.push("/login"); };

  // ── RENDER ──────────────────────────────────────────────
  return (
    <div style={s.root}>
      {/* ── Sidebar ── */}
      <div style={{ ...s.sidebar, ...(sidebarOpen ? {} : s.sidebarClosed) }}>
        {sidebarOpen && (
          <>
            {/* Logo */}
            <div style={s.sidebarHeader}>
              <Bot size={22} color="#6c63ff" />
              <span style={s.sidebarTitle}>AI Chatbot</span>
            </div>

            {/* New chat */}
            <button style={s.newChatBtn} onClick={newSession}>
              <Plus size={16} />
              Cuộc trò chuyện mới
            </button>

            {/* Sessions */}
            <div style={s.sessionList}>
              {sessions.length === 0 && (
                <p style={s.emptyLabel}>Chưa có cuộc trò chuyện nào</p>
              )}
              {sessions.map((s_) => (
                <div
                  key={s_.id}
                  style={{
                    ...s.sessionItem,
                    ...(activeSession === s_.id ? s.sessionActive : {}),
                  }}
                  onClick={() => selectSession(s_.id)}
                >
                  <MessageSquare size={14} style={{ flexShrink: 0, opacity: 0.6 }} />
                  <span style={s.sessionTitle}>
                    {s_.title || "Cuộc trò chuyện"}
                  </span>
                  <button
                    style={s.deleteBtn}
                    onClick={(e) => deleteSession(s_.id, e)}
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </div>

            {/* Footer */}
            <div style={s.sidebarFooter}>
              {admin && (
                <button style={s.footerBtn} onClick={() => router.push("/admin")}>
                  <ShieldCheck size={15} />
                  Admin Panel
                </button>
              )}
              <div style={s.userRow}>
                <div style={s.avatar}>{username[0]?.toUpperCase()}</div>
                <span style={s.usernameTxt}>{username}</span>
                <button style={s.logoutBtn} onClick={logout} title="Đăng xuất">
                  <LogOut size={15} />
                </button>
              </div>
            </div>
          </>
        )}

        {/* Toggle */}
        <button
          style={s.toggleBtn}
          onClick={() => setSidebarOpen(!sidebarOpen)}
          title={sidebarOpen ? "Thu sidebar" : "Mở sidebar"}
        >
          {sidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
        </button>
      </div>

      {/* ── Main ── */}
      <div style={s.main}>
        {/* Messages */}
        <div style={s.messages}>
          {messages.length === 0 && (
            <div style={s.welcome}>
              <div style={s.welcomeIcon}><Bot size={40} color="#6c63ff" /></div>
              <h2 style={s.welcomeTitle}>Xin chào, {username}!</h2>
              <p style={s.welcomeSub}>Hỏi tôi về sản phẩm, giá, tồn kho, chính sách bảo hành...</p>
              <div style={s.hints}>
                {["iPhone 16 Pro Max giá bao nhiêu?", "Samsung Galaxy S25 còn hàng không?", "Chính sách đổi trả như thế nào?"].map((h) => (
                  <button key={h} style={s.hintBtn} onClick={() => setInput(h)}>{h}</button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className="fade-in"
              style={{ ...s.msgRow, ...(msg.role === "user" ? s.msgRowUser : {}) }}
            >
              {/* Avatar */}
              {msg.role === "assistant" && (
                <div style={s.botAvatar}><Bot size={18} color="#6c63ff" /></div>
              )}

              {/* Bubble */}
              <div style={{ ...s.bubble, ...(msg.role === "user" ? s.bubbleUser : s.bubbleBot) }}>
                {msg.imageUrl && (
                  <img src={msg.imageUrl} alt="attachment" style={s.attachImg} />
                )}
                <p style={s.bubbleText}>
                  {msg.displayText ?? msg.content}
                  {msg.streaming && <span className="cursor-blink" />}
                  {msg.streaming && !msg.content && (
                    <span style={{ color: "var(--text-secondary)", fontSize: 13 }}>
                      Đang phân tích...
                    </span>
                  )}
                </p>
              </div>

              {msg.role === "user" && (
                <div style={s.userAvatar}>{username[0]?.toUpperCase()}</div>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* ── Input area ── */}
        <div style={s.inputArea}>
          {/* Image preview */}
          {imagePreview && (
            <div style={s.imgPreviewWrap}>
              <img src={imagePreview} alt="preview" style={s.imgPreview} />
              <button style={s.imgRemoveBtn} onClick={clearImage}><X size={14} /></button>
              <span style={s.imgLabel}>📎 AI sẽ nhận dạng sản phẩm</span>
            </div>
          )}

          <div style={s.inputRow}>
            {/* Attach button */}
            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              style={{ display: "none" }}
              onChange={handleImageSelect}
            />
            <button
              style={{ ...s.iconBtn, ...(imagePreview ? s.iconBtnActive : {}) }}
              onClick={() => fileRef.current?.click()}
              title="Đính kèm ảnh sản phẩm"
            >
              <Paperclip size={18} />
            </button>

            {/* Text input */}
            <textarea
              style={s.textarea}
              placeholder="Hỏi về sản phẩm, giá, tồn kho... (Enter để gửi)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={sending}
            />

            {/* Send button */}
            <button
              style={{ ...s.sendBtn, ...(sending || (!input.trim() && !imageFile) ? s.sendBtnDisabled : {}) }}
              onClick={sendMessage}
              disabled={sending || (!input.trim() && !imageFile)}
            >
              {sending
                ? <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
                : <Send size={18} />
              }
            </button>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        textarea { resize: none; overflow: hidden; }
        textarea:focus { outline: none; border-color: var(--accent) !important; }
        input:focus { outline: none; border-color: var(--accent) !important; }
      `}</style>
    </div>
  );
}

// ── STYLES ──────────────────────────────────────────────────────────────────
const s: Record<string, React.CSSProperties> = {
  root: { display: "flex", height: "100vh", background: "var(--bg-primary)", overflow: "hidden" },

  // Sidebar
  sidebar: {
    width: 260, background: "var(--bg-secondary)", borderRight: "1px solid var(--border)",
    display: "flex", flexDirection: "column", flexShrink: 0,
    position: "relative", transition: "width 0.2s",
  },
  sidebarClosed: { width: 40 },
  sidebarHeader: {
    display: "flex", alignItems: "center", gap: 10,
    padding: "18px 16px 12px", borderBottom: "1px solid var(--border)",
  },
  sidebarTitle: { fontWeight: 700, fontSize: 15, color: "var(--text-primary)" },
  newChatBtn: {
    display: "flex", alignItems: "center", gap: 8,
    margin: "12px 10px 8px", padding: "10px 14px",
    background: "rgba(108,99,255,0.15)", border: "1px solid rgba(108,99,255,0.3)",
    borderRadius: 10, color: "var(--accent)", fontSize: 13, fontWeight: 600,
    cursor: "pointer", transition: "all 0.2s",
  },
  sessionList: { flex: 1, overflowY: "auto", padding: "4px 8px" },
  emptyLabel: { fontSize: 12, color: "var(--text-secondary)", textAlign: "center", marginTop: 20 },
  sessionItem: {
    display: "flex", alignItems: "center", gap: 8,
    padding: "9px 10px", borderRadius: 8, cursor: "pointer",
    transition: "background 0.15s", marginBottom: 2,
  },
  sessionActive: { background: "var(--bg-hover)" },
  sessionTitle: {
    flex: 1, fontSize: 13, color: "var(--text-primary)",
    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
  },
  deleteBtn: {
    background: "none", border: "none", color: "var(--text-secondary)",
    cursor: "pointer", padding: 4, opacity: 0, transition: "opacity 0.15s",
    display: "flex", alignItems: "center",
  },
  sidebarFooter: { borderTop: "1px solid var(--border)", padding: "12px 10px" },
  footerBtn: {
    display: "flex", alignItems: "center", gap: 8, width: "100%",
    padding: "8px 10px", background: "none", border: "none",
    color: "var(--accent)", fontSize: 13, cursor: "pointer", borderRadius: 8,
    marginBottom: 8,
  },
  userRow: { display: "flex", alignItems: "center", gap: 8 },
  avatar: {
    width: 30, height: 30, borderRadius: "50%",
    background: "var(--accent)", color: "white",
    display: "flex", alignItems: "center", justifyContent: "center",
    fontSize: 13, fontWeight: 700, flexShrink: 0,
  },
  usernameTxt: { flex: 1, fontSize: 13, color: "var(--text-primary)", fontWeight: 500 },
  logoutBtn: {
    background: "none", border: "none", color: "var(--text-secondary)",
    cursor: "pointer", padding: 4, display: "flex", alignItems: "center",
  },
  toggleBtn: {
    position: "absolute", top: "50%", right: -14, transform: "translateY(-50%)",
    width: 28, height: 28, borderRadius: "50%",
    background: "var(--bg-card)", border: "1px solid var(--border)",
    color: "var(--text-secondary)", cursor: "pointer",
    display: "flex", alignItems: "center", justifyContent: "center",
    zIndex: 10,
  },

  // Main
  main: { flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" },
  messages: { flex: 1, overflowY: "auto", padding: "24px 16px" },

  // Welcome
  welcome: {
    display: "flex", flexDirection: "column", alignItems: "center",
    justifyContent: "center", height: "100%", textAlign: "center", padding: 32,
  },
  welcomeIcon: {
    width: 72, height: 72, borderRadius: 20,
    background: "rgba(108,99,255,0.12)", border: "1px solid rgba(108,99,255,0.25)",
    display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 20,
  },
  welcomeTitle: { fontSize: 22, fontWeight: 700, margin: "0 0 8px", color: "var(--text-primary)" },
  welcomeSub: { fontSize: 14, color: "var(--text-secondary)", margin: "0 0 24px" },
  hints: { display: "flex", flexDirection: "column", gap: 8, width: "100%", maxWidth: 380 },
  hintBtn: {
    padding: "10px 16px", background: "var(--bg-card)", border: "1px solid var(--border)",
    borderRadius: 10, color: "var(--text-primary)", fontSize: 13, cursor: "pointer",
    textAlign: "left", transition: "all 0.2s",
  },

  // Messages
  msgRow: { display: "flex", gap: 10, marginBottom: 16, alignItems: "flex-start" },
  msgRowUser: { flexDirection: "row-reverse" },
  botAvatar: {
    width: 34, height: 34, borderRadius: 10, flexShrink: 0,
    background: "rgba(108,99,255,0.15)", border: "1px solid rgba(108,99,255,0.25)",
    display: "flex", alignItems: "center", justifyContent: "center",
  },
  userAvatar: {
    width: 34, height: 34, borderRadius: 10, flexShrink: 0,
    background: "var(--accent)", color: "white",
    display: "flex", alignItems: "center", justifyContent: "center",
    fontSize: 14, fontWeight: 700,
  },
  bubble: { maxWidth: "72%", padding: "12px 16px", borderRadius: 14 },
  bubbleBot: { background: "var(--bg-card)", border: "1px solid var(--border)" },
  bubbleUser: { background: "var(--accent)", borderRadius: "14px 14px 4px 14px" },
  bubbleText: { margin: 0, fontSize: 14, lineHeight: 1.6, whiteSpace: "pre-wrap" },
  attachImg: { width: "100%", maxWidth: 240, borderRadius: 8, marginBottom: 8, display: "block" },

  // Input area
  inputArea: {
    padding: "12px 16px 16px",
    borderTop: "1px solid var(--border)",
    background: "var(--bg-secondary)",
  },
  imgPreviewWrap: {
    display: "flex", alignItems: "center", gap: 10,
    padding: "8px 12px", background: "var(--bg-card)", borderRadius: 10,
    marginBottom: 10, border: "1px solid var(--border)",
  },
  imgPreview: { width: 48, height: 48, borderRadius: 8, objectFit: "cover" },
  imgRemoveBtn: {
    background: "none", border: "none", color: "var(--text-secondary)",
    cursor: "pointer", padding: 4, display: "flex",
  },
  imgLabel: { fontSize: 12, color: "var(--text-secondary)", flex: 1 },
  inputRow: { display: "flex", gap: 8, alignItems: "flex-end" },
  iconBtn: {
    width: 40, height: 40, borderRadius: 10, flexShrink: 0,
    background: "var(--bg-card)", border: "1px solid var(--border)",
    color: "var(--text-secondary)", cursor: "pointer",
    display: "flex", alignItems: "center", justifyContent: "center",
    transition: "all 0.2s",
  },
  iconBtnActive: { color: "var(--accent)", borderColor: "var(--accent)", background: "rgba(108,99,255,0.1)" },
  textarea: {
    flex: 1, padding: "10px 14px",
    background: "var(--bg-card)", border: "1px solid var(--border)",
    borderRadius: 10, color: "var(--text-primary)", fontSize: 14,
    fontFamily: "inherit", lineHeight: 1.5, maxHeight: 160,
  },
  sendBtn: {
    width: 40, height: 40, borderRadius: 10, flexShrink: 0,
    background: "var(--accent)", border: "none", color: "white",
    cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
    transition: "all 0.2s",
  },
  sendBtnDisabled: { opacity: 0.4, cursor: "not-allowed" },
};

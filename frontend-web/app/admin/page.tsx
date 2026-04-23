"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAuth, isAdmin } from "@/lib/auth";
import { admin } from "@/lib/api";
import { Bot, Users, MessageSquare, Package, Activity, ArrowLeft, RefreshCw } from "lucide-react";

type Tab = "stats" | "users" | "conversations" | "products";

export default function AdminPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("stats");
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [convs, setConvs] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedConv, setSelectedConv] = useState<string | null>(null);
  const [convMsgs, setConvMsgs] = useState<any[]>([]);

  useEffect(() => {
    const auth = getAuth();
    if (!auth || auth.role !== "admin") { router.replace("/chat"); return; }
    loadStats();
  }, []);

  const loadStats   = async () => { const d = await admin.getStats();         setStats(d); };
  const loadUsers   = async () => { setLoading(true); const d = await admin.getUsers();        setUsers(d);   setLoading(false); };
  const loadConvs   = async () => { setLoading(true); const d = await admin.getConversations(); setConvs(d);  setLoading(false); };
  const loadProducts= async () => { setLoading(true); const d = await admin.getProducts();     setProducts(d);setLoading(false); };

  const switchTab = (t: Tab) => {
    setTab(t); setSelectedConv(null);
    if (t === "users")         loadUsers();
    else if (t === "conversations") loadConvs();
    else if (t === "products")   loadProducts();
    else                          loadStats();
  };

  const openConv = async (id: string) => {
    setSelectedConv(id);
    const msgs = await admin.getConversationMessages(id);
    setConvMsgs(msgs);
  };

  return (
    <div style={s.root}>
      {/* Sidebar */}
      <div style={s.sidebar}>
        <div style={s.sidebarHeader}>
          <Bot size={20} color="#6c63ff" />
          <span style={s.sidebarTitle}>Admin Panel</span>
        </div>

        {([
          { id: "stats",         icon: Activity,       label: "Tổng quan" },
          { id: "users",         icon: Users,          label: "Người dùng" },
          { id: "conversations", icon: MessageSquare,  label: "Hội thoại" },
          { id: "products",      icon: Package,        label: "Sản phẩm" },
        ] as { id: Tab; icon: any; label: string }[]).map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            style={{ ...s.navBtn, ...(tab === id ? s.navBtnActive : {}) }}
            onClick={() => switchTab(id)}
          >
            <Icon size={16} /> {label}
          </button>
        ))}

        <div style={{ flex: 1 }} />
        <button style={s.backBtn} onClick={() => router.push("/chat")}>
          <ArrowLeft size={15} /> Về Chat
        </button>
      </div>

      {/* Main */}
      <div style={s.main}>
        {/* ── Stats ── */}
        {tab === "stats" && stats && (
          <div>
            <h2 style={s.heading}>📊 Tổng quan hệ thống</h2>
            <div style={s.statsGrid}>
              {[
                { label: "Người dùng",       value: stats.total_users,    color: "#6c63ff" },
                { label: "Cuộc trò chuyện",  value: stats.total_sessions, color: "#22c55e" },
                { label: "Tin nhắn",         value: stats.total_messages, color: "#f59e0b" },
                { label: "Sản phẩm",         value: stats.total_products, color: "#06b6d4" },
                { label: "Hoạt động hôm nay",value: stats.active_today,   color: "#ec4899" },
              ].map((stat) => (
                <div key={stat.label} style={{ ...s.statCard, borderTopColor: stat.color }}>
                  <div style={{ ...s.statValue, color: stat.color }}>{stat.value}</div>
                  <div style={s.statLabel}>{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Users ── */}
        {tab === "users" && (
          <div>
            <div style={s.tableHeader}>
              <h2 style={s.heading}>👥 Người dùng</h2>
              <button style={s.refreshBtn} onClick={loadUsers}><RefreshCw size={14} /></button>
            </div>
            {loading ? <LoadingSpinner /> : (
              <table style={s.table}>
                <thead>
                  <tr style={s.thead}>
                    <Th>Username</Th><Th>Email</Th><Th>Role</Th>
                    <Th>Sessions</Th><Th>Trạng thái</Th><Th>Ngày tạo</Th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} style={s.tr}>
                      <Td><b>{u.username}</b></Td>
                      <Td>{u.email || "—"}</Td>
                      <Td>
                        <span style={{ ...s.badge, background: u.role === "admin" ? "rgba(108,99,255,0.2)" : "rgba(34,197,94,0.15)", color: u.role === "admin" ? "#6c63ff" : "#22c55e" }}>
                          {u.role}
                        </span>
                      </Td>
                      <Td>{u.session_count}</Td>
                      <Td>
                        <span style={{ ...s.badge, background: u.is_active ? "rgba(34,197,94,0.15)" : "rgba(239,68,68,0.15)", color: u.is_active ? "#22c55e" : "#ef4444" }}>
                          {u.is_active ? "Active" : "Inactive"}
                        </span>
                      </Td>
                      <Td>{new Date(u.created_at).toLocaleDateString("vi-VN")}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* ── Conversations ── */}
        {tab === "conversations" && !selectedConv && (
          <div>
            <div style={s.tableHeader}>
              <h2 style={s.heading}>💬 Hội thoại</h2>
              <button style={s.refreshBtn} onClick={loadConvs}><RefreshCw size={14} /></button>
            </div>
            {loading ? <LoadingSpinner /> : (
              <table style={s.table}>
                <thead>
                  <tr style={s.thead}>
                    <Th>User</Th><Th>Tiêu đề</Th><Th>Tin nhắn</Th><Th>Cập nhật</Th><Th></Th>
                  </tr>
                </thead>
                <tbody>
                  {convs.map((c) => (
                    <tr key={c.id} style={s.tr}>
                      <Td><b>{c.username}</b></Td>
                      <Td style={{ maxWidth: 240 }}>{c.title || "—"}</Td>
                      <Td>{c.message_count}</Td>
                      <Td>{new Date(c.updated_at).toLocaleString("vi-VN")}</Td>
                      <Td>
                        <button style={s.viewBtn} onClick={() => openConv(c.id)}>Xem</button>
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* ── Conversation detail ── */}
        {tab === "conversations" && selectedConv && (
          <div>
            <button style={s.backInner} onClick={() => setSelectedConv(null)}>
              <ArrowLeft size={14} /> Quay lại danh sách
            </button>
            <div style={s.convDetail}>
              {convMsgs.map((m) => (
                <div key={m.id} style={{ ...s.convMsg, ...(m.role === "user" ? s.convMsgUser : {}) }}>
                  <span style={{ ...s.convRole, color: m.role === "user" ? "#6c63ff" : "#22c55e" }}>
                    [{m.role}]
                  </span>
                  <p style={s.convText}>{m.display_text || m.content}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Products ── */}
        {tab === "products" && (
          <div>
            <div style={s.tableHeader}>
              <h2 style={s.heading}>📦 Sản phẩm ({products.length})</h2>
              <button style={s.refreshBtn} onClick={loadProducts}><RefreshCw size={14} /></button>
            </div>
            {loading ? <LoadingSpinner /> : (
              <table style={s.table}>
                <thead>
                  <tr style={s.thead}>
                    <Th>ID</Th><Th>Tên sản phẩm</Th><Th>Thương hiệu</Th>
                    <Th>Danh mục</Th><Th>Giá (VND)</Th><Th>Giảm giá</Th><Th>Tồn kho</Th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((p) => (
                    <tr key={p.id} style={s.tr}>
                      <Td style={{ fontSize: 11 }}>{p.id}</Td>
                      <Td style={{ maxWidth: 200 }}>{p.name}</Td>
                      <Td>{p.brand}</Td>
                      <Td>{p.category}</Td>
                      <Td>{p.price?.toLocaleString("vi-VN")} ₫</Td>
                      <Td>{p.discount > 0 ? <span style={{ color: "#f59e0b" }}>-{p.discount}%</span> : "—"}</Td>
                      <Td>{p.total_stock}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th style={styles_th}>{children}</th>;
}
function Td({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return <td style={{ ...styles_td, ...style }}>{children}</td>;
}
function LoadingSpinner() {
  return <div style={{ textAlign: "center", padding: 48, color: "var(--text-secondary)" }}>Đang tải...</div>;
}

const styles_th: React.CSSProperties = {
  padding: "10px 14px", textAlign: "left", fontSize: 12,
  color: "var(--text-secondary)", fontWeight: 600, letterSpacing: "0.05em", textTransform: "uppercase",
};
const styles_td: React.CSSProperties = {
  padding: "10px 14px", fontSize: 13, color: "var(--text-primary)",
  borderTop: "1px solid var(--border)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
};

const s: Record<string, React.CSSProperties> = {
  root: { display: "flex", height: "100vh", background: "var(--bg-primary)" },
  sidebar: {
    width: 220, background: "var(--bg-secondary)", borderRight: "1px solid var(--border)",
    display: "flex", flexDirection: "column", padding: "16px 10px",
  },
  sidebarHeader: {
    display: "flex", alignItems: "center", gap: 8,
    padding: "4px 8px 16px", marginBottom: 4,
  },
  sidebarTitle: { fontWeight: 700, fontSize: 15, color: "var(--text-primary)" },
  navBtn: {
    display: "flex", alignItems: "center", gap: 10,
    padding: "10px 12px", borderRadius: 8, border: "none",
    background: "none", color: "var(--text-secondary)", fontSize: 13, fontWeight: 500,
    cursor: "pointer", transition: "all 0.15s", marginBottom: 2, width: "100%",
  },
  navBtnActive: { background: "var(--bg-hover)", color: "var(--text-primary)" },
  backBtn: {
    display: "flex", alignItems: "center", gap: 8,
    padding: "9px 12px", borderRadius: 8, border: "none",
    background: "none", color: "var(--text-secondary)", fontSize: 13, cursor: "pointer",
  },
  main: { flex: 1, overflowY: "auto", padding: "28px 32px" },
  heading: { fontSize: 18, fontWeight: 700, color: "var(--text-primary)", margin: "0 0 20px" },
  tableHeader: { display: "flex", alignItems: "center", gap: 12, marginBottom: 20 },
  refreshBtn: {
    padding: "6px 10px", background: "var(--bg-card)", border: "1px solid var(--border)",
    borderRadius: 8, color: "var(--text-secondary)", cursor: "pointer",
    display: "flex", alignItems: "center",
  },
  table: { width: "100%", borderCollapse: "collapse", background: "var(--bg-card)", borderRadius: 12, overflow: "hidden" },
  thead: { background: "var(--bg-secondary)" },
  tr: { transition: "background 0.1s" },
  badge: { padding: "2px 8px", borderRadius: 20, fontSize: 11, fontWeight: 600 },
  viewBtn: {
    padding: "4px 12px", background: "rgba(108,99,255,0.15)", border: "1px solid rgba(108,99,255,0.3)",
    borderRadius: 6, color: "var(--accent)", fontSize: 12, cursor: "pointer",
  },
  statsGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 16 },
  statCard: {
    background: "var(--bg-card)", border: "1px solid var(--border)", borderTop: "3px solid",
    borderRadius: 12, padding: "20px 24px",
  },
  statValue: { fontSize: 32, fontWeight: 700 },
  statLabel: { fontSize: 13, color: "var(--text-secondary)", marginTop: 4 },
  convDetail: { display: "flex", flexDirection: "column", gap: 12 },
  convMsg: { background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 10, padding: "12px 16px" },
  convMsgUser: { borderLeft: "3px solid var(--accent)" },
  convRole: { fontSize: 11, fontWeight: 700, letterSpacing: "0.05em" },
  convText: { margin: "6px 0 0", fontSize: 13, color: "var(--text-primary)", whiteSpace: "pre-wrap" },
  backInner: {
    display: "flex", alignItems: "center", gap: 6, marginBottom: 20,
    padding: "6px 12px", background: "none", border: "none",
    color: "var(--accent)", fontSize: 13, cursor: "pointer", borderRadius: 6,
  },
};

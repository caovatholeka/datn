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
  const [editingProduct, setEditingProduct] = useState<any | null>(null);
  const [editForm, setEditForm] = useState({ name: "", brand: "", category: "", status: "", price: "", discount: "" });
  const [saveMsg, setSaveMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createForm, setCreateForm] = useState({ name: "", brand: "", category: "", status: "active", price: "", discount: "0" });
  const [createMsg, setCreateMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    const auth = getAuth();
    if (!auth || auth.role !== "admin") { router.replace("/chat"); return; }
    loadStats();
  }, []);

  const loadStats   = async () => { const d = await admin.getStats();         setStats(d); };
  const loadUsers   = async () => { setLoading(true); const d = await admin.getUsers();        setUsers(d);   setLoading(false); };
  const loadConvs   = async () => { setLoading(true); const d = await admin.getConversations(); setConvs(d);  setLoading(false); };
  const loadProducts= async () => { setLoading(true); const d = await admin.getProducts();     setProducts(d);setLoading(false); };

  const openEdit = (p: any) => {
    setEditingProduct(p);
    setEditForm({ name: p.name || "", brand: p.brand || "", category: p.category || "", status: p.status || "active", price: p.price?.toString() || "", discount: p.discount?.toString() || "0" });
    setSaveMsg(null);
  };

  const saveProduct = async () => {
    if (!editingProduct) return;
    setSaving(true); setSaveMsg(null);
    try {
      const pd: Record<string, string> = {};
      if (editForm.name.trim())     pd.name     = editForm.name.trim();
      if (editForm.brand.trim())    pd.brand    = editForm.brand.trim();
      if (editForm.category.trim()) pd.category = editForm.category.trim();
      if (editForm.status.trim())   pd.status   = editForm.status.trim();
      const pr: { price?: number; discount?: number } = {};
      if (editForm.price !== "")    pr.price    = Number(editForm.price);
      if (editForm.discount !== "") pr.discount = Number(editForm.discount);
      if (Object.keys(pd).length > 0) await admin.updateProduct(editingProduct.id, pd);
      if (Object.keys(pr).length > 0) await admin.updatePrice(editingProduct.id, pr);
      setSaveMsg({ type: "ok", text: "Cập nhật thành công!" });
      await loadProducts();
      setTimeout(() => { setEditingProduct(null); setSaveMsg(null); }, 1200);
    } catch (e: any) {
      setSaveMsg({ type: "err", text: e.message || "Lỗi cập nhật" });
    } finally { setSaving(false); }
  };

  const doCreate = async () => {
    if (!createForm.name.trim() || !createForm.brand.trim() || !createForm.price) {
      setCreateMsg({ type: "err", text: "Vui lòng nhập đủ Tên, Thương hiệu và Giá" }); return;
    }
    setCreating(true); setCreateMsg(null);
    try {
      await admin.createProduct({
        name: createForm.name.trim(), brand: createForm.brand.trim(),
        category: createForm.category.trim(), status: createForm.status || "active",
        price: Number(createForm.price), discount: Number(createForm.discount || 0),
      });
      setCreateMsg({ type: "ok", text: "Tạo sản phẩm thành công!" });
      await loadProducts();
      setTimeout(() => { setShowCreate(false); setCreateForm({ name: "", brand: "", category: "", status: "active", price: "", discount: "0" }); setCreateMsg(null); }, 1200);
    } catch (e: any) {
      setCreateMsg({ type: "err", text: e.message || "Lỗi tạo sản phẩm" });
    } finally { setCreating(false); }
  };

  const doDelete = async (id: string, name: string) => {
    if (!confirm(`Xóa sản phẩm "${name}"?\nHành động này không thể hoàn tác.`)) return;
    setDeletingId(id);
    try {
      await admin.deleteProduct(id);
      await loadProducts();
    } catch (e: any) {
      alert("Lỗi xóa: " + (e.message || "Unknown error"));
    } finally { setDeletingId(null); }
  };

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
              <button style={{ ...s.saveBtn, marginLeft: "auto", display: "flex", alignItems: "center", gap: 6, padding: "7px 14px" }}
                onClick={() => { setShowCreate(true); setCreateMsg(null); }}>➕ Thêm sản phẩm</button>
            </div>
            {loading ? <LoadingSpinner /> : (
              <table style={s.table}>
                <thead>
                  <tr style={s.thead}>
                    <Th>ID</Th><Th>Tên sản phẩm</Th><Th>Thương hiệu</Th>
                    <Th>Danh mục</Th><Th>Giá (VND)</Th><Th>Giảm giá</Th><Th>Tồn kho</Th><Th></Th>
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
                      <Td>
                        <button style={s.viewBtn} onClick={() => openEdit(p)}>✏️ Sửa</button>
                        <button
                          style={{ ...s.viewBtn, marginLeft: 6, color: "#ef4444", border: "1px solid rgba(239,68,68,0.3)", background: "rgba(239,68,68,0.1)" }}
                          onClick={() => doDelete(p.id, p.name)}
                          disabled={deletingId === p.id}
                        >{deletingId === p.id ? "..." : "🗑️"}</button>
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>

      {/* ── Create Modal ── */}
      {showCreate && (
        <div style={s.overlay}>
          <div style={s.modal}>
            <h3 style={{ margin: "0 0 16px", fontSize: 16, fontWeight: 700, color: "var(--text-primary)" }}>➕ Thêm sản phẩm mới</h3>
            <div style={s.formGrid}>
              {([
                { label: "Tên sản phẩm *", key: "name" },
                { label: "Thương hiệu *",  key: "brand" },
                { label: "Danh mục",      key: "category" },
                { label: "Trạng thái",    key: "status" },
              ] as { label: string; key: keyof typeof createForm }[]).map(({ label, key }) => (
                <div key={key} style={s.formField}>
                  <label style={s.formLabel}>{label}</label>
                  <input style={s.formInput} value={createForm[key]}
                    onChange={e => setCreateForm(f => ({ ...f, [key]: e.target.value }))} />
                </div>
              ))}
              <div style={s.formField}>
                <label style={s.formLabel}>Giá bán (VND) *</label>
                <input style={s.formInput} type="number" value={createForm.price}
                  onChange={e => setCreateForm(f => ({ ...f, price: e.target.value }))} />
              </div>
              <div style={s.formField}>
                <label style={s.formLabel}>Giảm giá (%)</label>
                <input style={s.formInput} type="number" min="0" max="100" value={createForm.discount}
                  onChange={e => setCreateForm(f => ({ ...f, discount: e.target.value }))} />
              </div>
            </div>
            {createMsg && (
              <p style={{ margin: "12px 0 0", fontSize: 13, fontWeight: 600,
                color: createMsg.type === "ok" ? "#22c55e" : "#ef4444" }}>
                {createMsg.type === "ok" ? "✅" : "❌"} {createMsg.text}
              </p>
            )}
            <div style={{ display: "flex", gap: 10, marginTop: 20, justifyContent: "flex-end" }}>
              <button style={s.cancelBtn} onClick={() => setShowCreate(false)} disabled={creating}>Hủy</button>
              <button style={s.saveBtn} onClick={doCreate} disabled={creating}>
                {creating ? "Đang tạo..." : "✅ Tạo sản phẩm"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Edit Modal ── */}
      {editingProduct && (
        <div style={s.overlay}>
          <div style={s.modal}>
            <h3 style={{ margin: "0 0 16px", fontSize: 16, fontWeight: 700, color: "var(--text-primary)" }}>✏️ Chỉnh sửa sản phẩm</h3>
            <p style={{ margin: "0 0 16px", fontSize: 12, color: "var(--text-secondary)" }}>ID: {editingProduct.id}</p>

            <div style={s.formGrid}>
              {([
                { label: "Tên sản phẩm", key: "name" },
                { label: "Thương hiệu",  key: "brand" },
                { label: "Danh mục",     key: "category" },
                { label: "Trạng thái",   key: "status" },
              ] as { label: string; key: keyof typeof editForm }[]).map(({ label, key }) => (
                <div key={key} style={s.formField}>
                  <label style={s.formLabel}>{label}</label>
                  <input
                    style={s.formInput}
                    value={editForm[key]}
                    onChange={e => setEditForm(f => ({ ...f, [key]: e.target.value }))}
                  />
                </div>
              ))}
              <div style={s.formField}>
                <label style={s.formLabel}>Giá bán (VND)</label>
                <input style={s.formInput} type="number" value={editForm.price}
                  onChange={e => setEditForm(f => ({ ...f, price: e.target.value }))} />
              </div>
              <div style={s.formField}>
                <label style={s.formLabel}>Giảm giá (%)</label>
                <input style={s.formInput} type="number" min="0" max="100" value={editForm.discount}
                  onChange={e => setEditForm(f => ({ ...f, discount: e.target.value }))} />
              </div>
            </div>

            {saveMsg && (
              <p style={{ margin: "12px 0 0", fontSize: 13, fontWeight: 600,
                color: saveMsg.type === "ok" ? "#22c55e" : "#ef4444" }}>
                {saveMsg.type === "ok" ? "✅" : "❌"} {saveMsg.text}
              </p>
            )}

            <div style={{ display: "flex", gap: 10, marginTop: 20, justifyContent: "flex-end" }}>
              <button style={s.cancelBtn} onClick={() => setEditingProduct(null)} disabled={saving}>Hủy</button>
              <button style={s.saveBtn} onClick={saveProduct} disabled={saving}>
                {saving ? "Đang lưu..." : "💾 Lưu thay đổi"}
              </button>
            </div>
          </div>
        </div>
      )}
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
  overlay: { position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 },
  modal: { background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 16, padding: "28px 32px", width: 560, maxHeight: "85vh", overflowY: "auto", boxShadow: "0 24px 80px rgba(0,0,0,0.5)" },
  formGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px 20px" },
  formField: { display: "flex", flexDirection: "column" as const, gap: 6 },
  formLabel: { fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", letterSpacing: "0.05em", textTransform: "uppercase" as const },
  formInput: { padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg-secondary)", color: "var(--text-primary)", fontSize: 13, outline: "none" },
  saveBtn: { padding: "9px 20px", background: "#6c63ff", border: "none", borderRadius: 8, color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" },
  cancelBtn: { padding: "9px 20px", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text-secondary)", fontSize: 13, cursor: "pointer" },
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

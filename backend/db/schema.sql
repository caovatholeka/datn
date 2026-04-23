-- ============================================================
-- DATN Chatbot Bán Hàng Điện Tử — PostgreSQL Schema
-- Chạy file này trước khi seed data
-- ============================================================

-- Extension hỗ trợ UUID
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ────────────────────────────────────────────
-- PRODUCT CATALOG
-- ────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS products (
    id          VARCHAR(20)  PRIMARY KEY,
    name        VARCHAR(500) NOT NULL,
    category    VARCHAR(100),
    brand       VARCHAR(100),
    specs       TEXT,
    warranty    VARCHAR(50),
    battery     VARCHAR(50),
    status      VARCHAR(20)  DEFAULT 'active',
    updated_at  TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prices (
    product_id  VARCHAR(20) PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
    price       BIGINT      NOT NULL,
    discount    INTEGER     DEFAULT 0,
    updated_at  TIMESTAMP   DEFAULT NOW()
);

-- Hỗ trợ nhiều kho (Hà Nội, Hồ Chí Minh, ...)
CREATE TABLE IF NOT EXISTS inventory (
    id          SERIAL      PRIMARY KEY,
    product_id  VARCHAR(20) REFERENCES products(id) ON DELETE CASCADE,
    warehouse   VARCHAR(100) NOT NULL,
    stock       INTEGER     DEFAULT 0,
    updated_at  TIMESTAMP   DEFAULT NOW(),
    UNIQUE (product_id, warehouse)
);

-- ────────────────────────────────────────────
-- USER AUTHENTICATION
-- ────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    username    VARCHAR(100) UNIQUE NOT NULL,
    email       VARCHAR(255) UNIQUE,
    password    VARCHAR(255) NOT NULL,   -- bcrypt hash
    role        VARCHAR(20)  DEFAULT 'user',   -- 'user' | 'admin'
    created_at  TIMESTAMP   DEFAULT NOW(),
    is_active   BOOLEAN     DEFAULT TRUE
);

-- ────────────────────────────────────────────
-- CHAT SESSIONS & MESSAGES
-- ────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS chat_sessions (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(255),           -- Auto từ message đầu tiên
    summary     TEXT        DEFAULT '',  -- Memory summary (MemoryManager)
    created_at  TIMESTAMP   DEFAULT NOW(),
    updated_at  TIMESTAMP   DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    id           SERIAL      PRIMARY KEY,
    session_id   UUID        REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role         VARCHAR(20) NOT NULL,      -- 'user' | 'assistant'
    content      TEXT        NOT NULL,      -- Pipeline query (enriched)
    display_text TEXT,                      -- Text hiển thị thuần (clean)
    has_image    BOOLEAN     DEFAULT FALSE,
    orch_meta    JSONB       DEFAULT '{}',  -- intent, latency, tool_result
    created_at   TIMESTAMP   DEFAULT NOW()
);

-- ────────────────────────────────────────────
-- INDEXES (tăng tốc query)
-- ────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_products_brand    ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_status   ON products(status);
CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_messages_session  ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user     ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_updated  ON chat_sessions(updated_at DESC);

-- ============================================================
-- 법적 컴플라이언스: user_consents + access_logs 테이블
-- Phase 1 + Phase 2 마이그레이션
-- ============================================================

-- 사용자 동의 이력
CREATE TABLE IF NOT EXISTS user_consents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(50) NOT NULL,   -- 'terms', 'privacy', 'audio_processing', 'overseas_transfer'
    version VARCHAR(20) NOT NULL,        -- '2026-03-01'
    agreed BOOLEAN NOT NULL DEFAULT true,
    agreed_at TIMESTAMP DEFAULT NOW(),
    withdrawn_at TIMESTAMP,
    ip_address VARCHAR(50),
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_user_consents_user ON user_consents(user_id);
CREATE INDEX IF NOT EXISTS idx_user_consents_type ON user_consents(user_id, consent_type);

-- 접속기록 (감사 로그)
CREATE TABLE IF NOT EXISTS access_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(50) NOT NULL,         -- 'login', 'upload', 'download', 'view', 'delete', 'consent'
    resource_type VARCHAR(30),           -- 'audio', 'room', 'message', 'user', 'consent'
    resource_id INTEGER,
    ip_address VARCHAR(50),
    user_agent TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_access_logs_user ON access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_created ON access_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_access_logs_action ON access_logs(action);

-- Initialize database schema

CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    version TEXT NOT NULL,
    content TEXT NOT NULL,
    active BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_prompts_tenant ON prompts(tenant_id, active);

CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    value REAL,
    dimensions TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_metrics_tenant ON metrics(tenant_id, metric_name, timestamp);

CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    queue_name TEXT NOT NULL,
    item_id TEXT,
    payload TEXT NOT NULL,
    error TEXT,
    failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP,
    resolved BOOLEAN DEFAULT 0,
    resolved_at TIMESTAMP,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_dlq_tenant ON dead_letter_queue(tenant_id, resolved);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    lead_id TEXT NOT NULL,
    messages TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_conv_tenant ON conversations(tenant_id, lead_id, created_at);

INSERT OR IGNORE INTO prompts (tenant_id, version, content, active, description) VALUES (
    'default',
    'v1.0.0',
    'You are a CRM outreach agent. Generate professional responses.',
    1,
    'Default system prompt'
);

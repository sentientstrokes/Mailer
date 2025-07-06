CREATE TABLE email_events (
    mic TEXT PRIMARY KEY,
    receiver_name TEXT,
    mail_id TEXT NOT NULL,
    mail_type TEXT NOT NULL,
    mode TEXT NOT NULL,
    subject TEXT,
    sent_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    first_opened_at TIMESTAMPTZ DEFAULT NULL,
    open_count INTEGER DEFAULT 0,
    last_clicked_at TIMESTAMPTZ,
    ip_address INET,
    user_agent TEXT
);
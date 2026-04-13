"""Have multiple-line SQL or queries that are used often here. Single-line SQL can go straight into code."""

CREATE_BANS_TABLE = (
    """
    CREATE TABLE IF NOT EXISTS bans
    (
        tg_id INTEGER PRIMARY KEY,
        ban_timestamp INTEGER NOT NULL,
        first_name TEXT,
        last_name TEXT,
        username TEXT
    );
    """
)

MIGRATE_BANS_TABLE = (
    "ALTER TABLE bans ADD COLUMN first_name TEXT;",
    "ALTER TABLE bans ADD COLUMN last_name TEXT;",
    "ALTER TABLE bans ADD COLUMN username TEXT;",
)

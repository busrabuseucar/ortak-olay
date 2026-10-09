"""Additive migration for the local SQLite prototype; existing source data stays intact."""
def migrate(connection):
    connection.execute('BEGIN IMMEDIATE')
    try:
        additions = {
            'reports': {'group_ref': 'TEXT', 'statement_type': "TEXT NOT NULL DEFAULT 'unknown'", 'review_version': 'INTEGER NOT NULL DEFAULT 1'},
            'events': {'group_ref': 'TEXT', 'review_required': 'INTEGER NOT NULL DEFAULT 0'},
        }
        for table, fields in additions.items():
            existing = {row[1] for row in connection.execute(f'PRAGMA table_info({table})')}
            for name, definition in fields.items():
                if name not in existing:
                    connection.execute(f'ALTER TABLE {table} ADD COLUMN {name} {definition}')
        connection.execute("""CREATE TABLE IF NOT EXISTS candidate_decisions (
            report_id TEXT NOT NULL REFERENCES reports(id), event_id TEXT NOT NULL REFERENCES events(id),
            action TEXT NOT NULL, reason TEXT NOT NULL, actor TEXT NOT NULL, timestamp TEXT NOT NULL,
            report_version INTEGER NOT NULL, event_version INTEGER NOT NULL, version INTEGER NOT NULL,
            PRIMARY KEY(report_id,event_id))""")
        connection.commit()
    except Exception:
        connection.rollback()
        raise

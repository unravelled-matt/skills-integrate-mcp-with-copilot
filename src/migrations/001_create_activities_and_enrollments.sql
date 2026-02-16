CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    schedule TEXT NOT NULL,
    max_participants INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    email TEXT NOT NULL,
    FOREIGN KEY(activity_id) REFERENCES activities(id) ON DELETE CASCADE,
    UNIQUE(activity_id, email)
);

CREATE INDEX IF NOT EXISTS idx_enrollments_activity_id ON enrollments(activity_id);

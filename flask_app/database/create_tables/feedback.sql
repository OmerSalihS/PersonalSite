CREATE TABLE IF NOT EXISTS feedback (
    comment_id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    comment TEXT NOT NULL
);

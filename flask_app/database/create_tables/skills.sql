CREATE TABLE IF NOT EXISTS skills (
    skill_id SERIAL PRIMARY KEY,
    experience_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    skill_level INT CHECK (skill_level BETWEEN 1 AND 10),
    FOREIGN KEY (experience_id) REFERENCES experiences(experience_id) ON DELETE CASCADE
);

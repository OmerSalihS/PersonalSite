CREATE TABLE IF NOT EXISTS positions (
    position_id SERIAL PRIMARY KEY,
    inst_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    responsibilities VARCHAR(500) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    FOREIGN KEY (inst_id) REFERENCES institutions(inst_id)
);
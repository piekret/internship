CREATE DATABASE IF NOT EXISTS zad_php;
USE zad_php;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    admin TINYINT(1) NOT NULL DEFAULT 0
);

INSERT INTO users (username, password, admin) VALUES 
    ('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 1), -- admin123
    ('user', '2b25e8aeb75195881382becae8db082a789fca9283225ba84cf8163dafbac838', 0); -- sigmaa

CREATE TABLE IF NOT EXISTS wysiwyg (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    content TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
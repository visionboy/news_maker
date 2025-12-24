-- Create the database if it doesn't exist (handled by Docker usually, but good for ref)
CREATE DATABASE IF NOT EXISTS news_db;

USE news_db;

CREATE TABLE IF NOT EXISTS news_articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    original_url TEXT NOT NULL,
    summary TEXT,
    published_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

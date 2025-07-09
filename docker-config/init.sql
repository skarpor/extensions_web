-- 数据查询系统数据库初始化脚本

-- 创建数据库 (如果不存在)
-- CREATE DATABASE IF NOT EXISTS dataquery;

-- 设置字符集
-- ALTER DATABASE dataquery CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建扩展 (PostgreSQL)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建用户表 (示例，实际表结构由 SQLAlchemy 创建)
-- CREATE TABLE IF NOT EXISTS users (
--     id SERIAL PRIMARY KEY,
--     username VARCHAR(50) UNIQUE NOT NULL,
--     email VARCHAR(100) UNIQUE NOT NULL,
--     hashed_password VARCHAR(255) NOT NULL,
--     nickname VARCHAR(100),
--     is_active BOOLEAN DEFAULT TRUE,
--     is_superuser BOOLEAN DEFAULT FALSE,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- 创建扩展表
-- CREATE TABLE IF NOT EXISTS extensions (
--     id VARCHAR(100) PRIMARY KEY,
--     name VARCHAR(200) NOT NULL,
--     description TEXT,
--     enabled BOOLEAN DEFAULT TRUE,
--     config JSONB,
--     creator_id INTEGER REFERENCES users(id),
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- 创建文件表
-- CREATE TABLE IF NOT EXISTS files (
--     id SERIAL PRIMARY KEY,
--     filename VARCHAR(255) NOT NULL,
--     filepath VARCHAR(500) NOT NULL,
--     filetype VARCHAR(100),
--     filesize BIGINT,
--     hash VARCHAR(64),
--     owner_id INTEGER REFERENCES users(id),
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- 创建聊天表
-- CREATE TABLE IF NOT EXISTS chats (
--     id SERIAL PRIMARY KEY,
--     title VARCHAR(200),
--     chat_type VARCHAR(50) DEFAULT 'private',
--     creator_id INTEGER REFERENCES users(id),
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- 创建消息表
-- CREATE TABLE IF NOT EXISTS messages (
--     id SERIAL PRIMARY KEY,
--     content TEXT NOT NULL,
--     message_type VARCHAR(50) DEFAULT 'text',
--     sender_id INTEGER REFERENCES users(id),
--     chat_id INTEGER REFERENCES chats(id),
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- 创建索引
-- CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
-- CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
-- CREATE INDEX IF NOT EXISTS idx_extensions_enabled ON extensions(enabled);
-- CREATE INDEX IF NOT EXISTS idx_files_owner ON files(owner_id);
-- CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id);
-- CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);

-- 插入默认管理员用户 (密码: admin123)
-- INSERT INTO users (username, email, hashed_password, nickname, is_superuser) 
-- VALUES (
--     'admin', 
--     'admin@example.com', 
--     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJK9fHPyy', 
--     '系统管理员', 
--     TRUE
-- ) ON CONFLICT (username) DO NOTHING;

-- 创建函数：更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表创建触发器
-- CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
--     FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- CREATE TRIGGER update_extensions_updated_at BEFORE UPDATE ON extensions 
--     FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE DATABASE bwp_guild_bot;
USE bwp_guild_bot;

CREATE TABLE IF NOT EXISTS settings (
	guild_id BIGINT PRIMARY KEY,
    verification BIGINT DEFAULT NULL,
    applications BIGINT DEFAULT NULL,
    charts BIGINT DEFAULT NULL,
    gxp_updates BIGINT DEFAULT NULL,
    streak BIGINT DEFAULT NULL,
    counting BIGINT DEFAULT NULL,
    lactate BIGINT DEFAULT NULL,
    guild_role BIGINT DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS verified_users (
    discord_id BIGINT PRIMARY KEY,
    uuid VARCHAR(36) DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS verify_requests (
    message_id BIGINT PRIMARY KEY,
    discord_id BIGINT NOT NULL,
    uuid VARCHAR(36) NOT NULL
)

CREATE TABLE guild_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    player_name VARCHAR(32) NOT NULL,
    log_type ENUM('join', 'leave') NOT NULL,
    created_at BIGINT NOT NULL
);

-- Guild tracking part

CREATE TABLE tracked_guilds (
    guild_id BIGINT PRIMARY KEY,
    logs_channel BIGINT DEFAULT NULL
);

CREATE TABLE tracked_players (
    uuid VARCHAR(36) PRIMARY KEY,
    guild_id BIGINT DEFAULT NULL,

    INDEX idx_guild_id (guild_id)
);

CREATE TABLE tracked_player_snapshots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL,
    guild_id BIGINT NOT NULL,
    level INT NOT NULL,
    xp INT NOT NULL,
    date DATE NOT NULL,

    UNIQUE KEY uq_uuid_date (uuid, date),

    INDEX idx_uuid (uuid),
    INDEX idx_guild_id (guild_id),
    INDEX idx_date (date),

    FOREIGN KEY (uuid) REFERENCES tracked_players(uuid)
);

CREATE TABLE tracked_guild_snapshots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    gxp BIGINT NOT NULL,
    date DATE NOT NULL,

    UNIQUE KEY uq_guild_date (guild_id, date),

    INDEX idx_guild_id (guild_id),
    INDEX idx_date (date),

    FOREIGN KEY (guild_id) REFERENCES tracked_guilds(guild_id)
);

-- Chart

CREATE TABLE last_week_updates (
    id INT PRIMARY KEY,
    xp_chart INT NOT NULL,
    gxp_chart INT NOT NULL
);

INSERT IGNORE INTO last_week_updates (
    id,
    xp_chart,
    gxp_chart
) VALUES (
    1,
    0,
    0
);


-- web login tables
CREATE TABLE web_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    discord_id BIGINT NOT NULL UNIQUE,
    uuid VARCHAR(32) NOT NULL,
    role TINYINT NOT NULL DEFAULT 0
);

CREATE TABLE web_sessions (
    user_id INT PRIMARY KEY,
    access_token CHAR(64) NOT NULL,
    expires_at DATETIME NOT NULL,

    CONSTRAINT fk_user
        FOREIGN KEY (user_id)
        REFERENCES web_users(id)
        ON DELETE CASCADE
);

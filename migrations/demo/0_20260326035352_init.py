from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `endpoint` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    `endpoint` VARCHAR(255) NOT NULL COMMENT 'Endpoint path',
    `method` VARCHAR(10) NOT NULL COMMENT 'HTTP method',
    `update_time` DATETIME(6) NOT NULL COMMENT 'Updated at' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `create_time` DATETIME(6) NOT NULL COMMENT 'Created at' DEFAULT CURRENT_TIMESTAMP(6),
    UNIQUE KEY `uid_endpoint_endpoin_5e5599` (`endpoint`, `method`),
    KEY `idx_endpoint_endpoin_1a2d74` (`endpoint`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `permission` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    `permission_title` VARCHAR(100) NOT NULL UNIQUE COMMENT 'Permission title',
    `update_time` DATETIME(6) NOT NULL COMMENT 'Updated at' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `create_time` DATETIME(6) NOT NULL COMMENT 'Created at' DEFAULT CURRENT_TIMESTAMP(6),
    KEY `idx_permission_permiss_576344` (`permission_title`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `role` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    `role_name` VARCHAR(100) NOT NULL UNIQUE COMMENT 'Role name',
    `update_time` DATETIME(6) NOT NULL COMMENT 'Updated at' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `create_time` DATETIME(6) NOT NULL COMMENT 'Created at' DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `user` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    `account` VARCHAR(50) NOT NULL UNIQUE COMMENT 'User account',
    `password` VARCHAR(255) NOT NULL COMMENT 'Password hash',
    `open_id` VARCHAR(32) NOT NULL UNIQUE COMMENT 'OpenID',
    `status` SMALLINT NOT NULL COMMENT 'User status' DEFAULT 0,
    `update_time` DATETIME(6) NOT NULL COMMENT 'Updated at' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `create_time` DATETIME(6) NOT NULL COMMENT 'Created at' DEFAULT CURRENT_TIMESTAMP(6),
    KEY `idx_user_account_80d388` (`account`),
    KEY `idx_user_open_id_cc2303` (`open_id`),
    KEY `idx_user_status_ec9fb9` (`status`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `log` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    `api` VARCHAR(512) NOT NULL COMMENT 'API URI',
    `action` VARCHAR(512) NOT NULL COMMENT 'Action summary',
    `ip` VARCHAR(64) NOT NULL COMMENT 'Source IP',
    `ua` VARCHAR(255) NOT NULL COMMENT 'User agent',
    `level` SMALLINT NOT NULL COMMENT 'Severity level',
    `update_time` DATETIME(6) NOT NULL COMMENT 'Updated at' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `create_time` DATETIME(6) NOT NULL COMMENT 'Created at' DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_log_user_5dd73170` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
    KEY `idx_log_api_0e66b2` (`api`),
    KEY `idx_log_action_e8ddd4` (`action`),
    KEY `idx_log_ip_25527b` (`ip`),
    KEY `idx_log_ua_8435a3` (`ua`),
    KEY `idx_log_level_b6bd62` (`level`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `endpoint_permission` (
    `endpoint_id` INT NOT NULL,
    `permission_id` INT NOT NULL,
    FOREIGN KEY (`endpoint_id`) REFERENCES `endpoint` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`permission_id`) REFERENCES `permission` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_endpoint_pe_endpoin_1a7ca7` (`endpoint_id`, `permission_id`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `role_permission` (
    `role_id` INT NOT NULL,
    `permission_id` INT NOT NULL,
    FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`permission_id`) REFERENCES `permission` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_role_permis_role_id_7454bb` (`role_id`, `permission_id`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `user_role` (
    `user_id` BIGINT NOT NULL,
    `role_id` INT NOT NULL,
    FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_user_role_user_id_d0bad3` (`user_id`, `role_id`)
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "hx"
)

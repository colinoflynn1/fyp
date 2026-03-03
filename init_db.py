import os
import mysql.connector

conn = mysql.connector.connect(
    host=os.environ.get('DB_HOST'),
    port=int(os.environ.get('DB_PORT', 3306)),
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASS'),
    database=os.environ.get('DB_NAME'),
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS `users` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `full_name` varchar(255) NOT NULL,
  `role` enum('user','admin') NOT NULL DEFAULT 'user',
  `password_hash` varchar(255) DEFAULT NULL,
  `password` varchar(45) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `email_notifications` tinyint(1) DEFAULT '1',
  `dashboard_notifications` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_email_unique` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS `savings_goals` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int unsigned NOT NULL,
  `goal_name` varchar(120) NOT NULL,
  `target_amount` decimal(12,2) NOT NULL,
  `target_date` date NOT NULL,
  `frequency` enum('weekly','bi-weekly','monthly') NOT NULL,
  `saved_amount` decimal(12,2) NOT NULL DEFAULT '0.00',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `next_due_date` date DEFAULT NULL,
  `completed_at` timestamp NULL DEFAULT NULL,
  `periods_skipped` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_goal_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS `savings_goal_deposits` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `goal_id` int unsigned NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `note` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `contribution_type` varchar(20) NOT NULL DEFAULT 'lump_sum',
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_deposit_goal` FOREIGN KEY (`goal_id`) REFERENCES `savings_goals` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS `user_notifications` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int unsigned NOT NULL,
  `notification_type` varchar(50) NOT NULL,
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `goal_id` int unsigned DEFAULT NULL,
  `is_read` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_notification_goal` FOREIGN KEY (`goal_id`) REFERENCES `savings_goals` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_notification_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""")

conn.commit()
cursor.close()
conn.close()
print("Tables created successfully!")

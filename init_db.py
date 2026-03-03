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

cursor.execute("SET FOREIGN_KEY_CHECKS=0;")

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
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4;
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
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4;
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
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4;
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
  KEY `fk_notification_goal` (`goal_id`),
  KEY `idx_user_read` (`user_id`,`is_read`),
  KEY `idx_user_created` (`user_id`,`created_at` DESC),
  CONSTRAINT `fk_notification_goal` FOREIGN KEY (`goal_id`) REFERENCES `savings_goals` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_notification_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=67 DEFAULT CHARSET=utf8mb4;
""")

# Insert users (only if table is empty)
cursor.execute("SELECT COUNT(*) FROM users")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
    INSERT INTO `users` VALUES
    (1,'john@gmail.com','John','user','scrypt:32768:8:1$gYwLd1WmYy9x7gm9$3db79a34771b3d5532e6c705eb1b331740721daaad3cf4769b89b74895c6141a76cf61cac342a5c55a4fe5022dc2f02d43e79cc71553ea768a30371721c9ccee','password1','2025-11-05 13:07:12','2025-11-05 23:16:25',1,1),
    (2,'colinoflynn20@gmail.com','Colin','admin','scrypt:32768:8:1$LhA7T3oWdYRB6DVf$cbf5fd06900186f8d62bf788df63d44ab300093d400f01cbaaf5a57c812d1e476f8403e8a78646624d07279bf191eda5000e10979b176cdceaffe0fb1feaa4db','password','2025-11-05 13:07:12','2026-02-20 14:50:33',1,1),
    (4,'arranbearman@gmail.com','Arran bearman','user','scrypt:32768:8:1$Or9xqvC2HEdBCTQj$dddcfa1a63aa7a9322ca4a64fd8429f8963b1789582d59374df1c4a26c9d3c71ce1a8d62e3f5e21730588f563b0a87cb1cc76ae5547706f8709c7ab370e926f8',NULL,'2025-11-05 17:14:16','2026-03-02 13:04:03',1,1),
    (5,'conor@gmail.com','Conor U','user','scrypt:32768:8:1$CDNHsMHfcHXRFshE$52c0eb1fecdbe499e0efdd2e9db8f641086c82dd755db508b7dd0aef325e07d9491d896061359b19726005a419dc0a9762ffa302a444c6b7adffdca8df60eb12',NULL,'2025-11-05 23:08:25','2025-11-05 23:08:25',1,1),
    (6,'usti@gmail.com','usti','user','scrypt:32768:8:1$U4pixTqfuq30D7SB$b2bf7136ab7bfd1c7e81dae71b30d192e3fddd47e0856fe9bf6c697cd48355e293bd32e1b2bf3f8a91164460d37ea679758200b7fc88c3359437d16a07f50da5',NULL,'2025-11-07 23:03:41','2025-11-07 23:03:41',1,1),
    (8,'user@gmail.com','user','user','scrypt:32768:8:1$Kqqd48hJHQ06Vedv$51d2f189902c6a0a869b8f32d7e61b02f35dcb0facd935cd97ff6ff341204b4ff39624c7e50f32beec628bae77f7e4845c6da16619ae25f9910a22d75d632c5b',NULL,'2026-02-09 23:09:37','2026-02-09 23:09:37',1,1)
    """)

# Insert savings_goals (only if table is empty)
cursor.execute("SELECT COUNT(*) FROM savings_goals")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
    INSERT INTO `savings_goals` VALUES
    (1,4,'Holidays',3000.00,'2026-05-26','bi-weekly',744.44,'2025-11-20 13:37:49','2026-02-18 14:15:25','2026-03-04',NULL,1),
    (2,4,'Christmas',500.00,'2025-12-24','weekly',500.00,'2025-11-20 13:41:24','2026-02-03 17:20:11','2026-02-05','2026-01-29 11:53:58',0),
    (3,2,'J1',5000.00,'2026-05-24','monthly',2500.00,'2025-11-20 15:17:51','2026-02-20 14:55:04','2026-03-22',NULL,0),
    (5,5,'beer money',2000.00,'2026-02-05','weekly',2000.00,'2025-11-21 15:20:38','2026-02-18 15:11:13','2026-02-25','2026-02-18 15:11:13',0),
    (7,2,'Car Insurance',1000.00,'2026-02-02','weekly',1000.00,'2026-01-20 17:11:54','2026-02-05 08:56:11','2026-02-12','2026-02-05 08:56:11',0),
    (8,2,'Car Tax',270.00,'2026-01-29','weekly',320.00,'2026-01-22 18:29:35','2026-02-03 17:20:11','2026-02-05','2026-01-29 11:45:16',0),
    (9,4,'Family Dinner',300.00,'2026-01-30','weekly',300.00,'2026-01-23 13:04:39','2026-02-03 17:18:39','2026-02-10','2026-02-03 17:18:39',0),
    (10,5,'Holidays',500.00,'2026-02-19','weekly',500.00,'2026-01-29 11:52:13','2026-02-18 15:11:32','2026-02-25','2026-02-18 15:11:32',0),
    (12,2,'Accommodation',2000.00,'2026-03-05','weekly',0.00,'2026-02-03 16:35:04','2026-02-25 14:51:51','2026-03-04',NULL,1),
    (13,5,'Boston J1 Trip',2000.00,'2026-05-20','monthly',100.00,'2026-02-06 16:53:02','2026-02-24 11:34:43','2026-03-26',NULL,0),
    (16,8,'March 7th Goal',700.00,'2026-03-07','weekly',700.00,'2026-02-09 23:58:55','2026-02-10 11:20:29','2026-02-17','2026-02-10 11:20:29',0),
    (17,8,'August 10th Goal',3000.00,'2026-08-10','monthly',0.00,'2026-02-10 11:19:19','2026-02-10 11:19:19','2026-03-12',NULL,0),
    (18,2,'Rent',500.00,'2026-07-31','monthly',0.00,'2026-02-20 15:06:46','2026-02-20 15:06:46','2026-03-22',NULL,0),
    (19,4,'Masters',10000.00,'2026-09-09','weekly',0.00,'2026-03-02 12:11:08','2026-03-02 12:11:08','2026-03-09',NULL,0),
    (20,5,'Car',15000.00,'2027-03-02','weekly',500.00,'2026-03-02 12:14:12','2026-03-02 12:14:12','2026-03-09',NULL,0),
    (21,1,'House Insurance',2500.00,'2027-03-02','bi-weekly',100.00,'2026-03-02 13:21:56','2026-03-02 13:22:26','2026-03-16',NULL,0)
    """)

# Insert savings_goal_deposits (only if table is empty)
cursor.execute("SELECT COUNT(*) FROM savings_goal_deposits")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
    INSERT INTO `savings_goal_deposits` VALUES
    (1,1,100.00,'Initial lump sum','2025-11-20 13:37:49','lump_sum'),
    (2,2,50.00,'Overtime','2025-11-20 15:05:02','lump_sum'),
    (4,3,120.00,'Lump sum deposit','2025-11-21 23:28:38','lump_sum'),
    (6,1,322.22,'Scheduled bi-weekly contribution','2026-01-20 17:05:56','on_time'),
    (7,2,450.00,'Scheduled weekly contribution','2026-01-20 17:06:16','on_time'),
    (8,5,100.00,'Scheduled weekly contribution','2026-01-20 17:07:02','on_time'),
    (9,3,150.00,'tax back','2026-01-20 17:07:48','lump_sum'),
    (10,7,250.00,'lump sum','2026-01-20 17:12:15','lump_sum'),
    (11,8,70.00,'Initial lump sum','2026-01-22 18:29:35','lump_sum'),
    (12,7,250.00,'overtime','2026-01-23 12:32:22','lump_sum'),
    (13,3,120.00,'Lump sum deposit','2026-01-23 12:33:43','lump_sum'),
    (14,9,150.00,'Initial lump sum','2026-01-23 13:04:39','lump_sum'),
    (15,8,250.00,'Overtime','2026-01-29 11:45:16','lump_sum'),
    (16,7,100.00,'Overtime','2026-01-29 11:46:27','lump_sum'),
    (17,9,150.00,'Scheduled weekly contribution','2026-02-03 17:18:39','on_time'),
    (18,1,322.22,'Scheduled bi-weekly contribution','2026-02-03 17:18:55','on_time'),
    (19,5,600.00,'Lump sum deposit','2026-02-03 17:30:16','lump_sum'),
    (20,7,400.00,'Scheduled weekly contribution','2026-02-05 08:56:11','on_time'),
    (21,16,700.00,'Lump sum deposit','2026-02-10 11:20:29','lump_sum'),
    (22,5,1300.00,'Scheduled weekly contribution','2026-02-18 15:11:13','on_time'),
    (23,10,500.00,'Scheduled weekly contribution','2026-02-18 15:11:32','on_time'),
    (24,3,2110.00,'test','2026-02-20 14:55:04','lump_sum'),
    (25,13,100.00,'Overtime','2026-02-24 11:34:43','lump_sum'),
    (26,20,500.00,'Initial lump sum','2026-03-02 12:14:12','lump_sum'),
    (27,21,100.00,'Overtime','2026-03-02 13:22:26','lump_sum')
    """)

cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
conn.commit()
cursor.close()
conn.close()
print("Database initialised successfully!")
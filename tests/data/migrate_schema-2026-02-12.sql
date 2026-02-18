-- Migration: arxiv.sql -> arxiv_db_schema.sql
-- ntai: 2025-02-12

-- ***************************************
-- DO NOT EVER RUN THIS AGAINST PRODUCTION
-- ***************************************

SET FOREIGN_KEY_CHECKS=0;

-- CREATE new tables that exist in target but not in production

CREATE TABLE `flagged_user_comment` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action` varchar(32) DEFAULT NULL,
  `comment` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `flagged_user_detail` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `active` tinyint(1) DEFAULT '1',
  `creator_user_id` int unsigned NOT NULL,
  `flagged_user_id` int unsigned NOT NULL,
  `all_categories` tinyint(1) DEFAULT '1',
  `flagged_user_comment_id` int DEFAULT NULL,
  `action` varchar(32) DEFAULT NULL,
  `comment` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `creator_user_id` (`creator_user_id`),
  KEY `flagged_user_id` (`flagged_user_id`),
  CONSTRAINT `flagged_user_detail_ibfk_1` FOREIGN KEY (`creator_user_id`) REFERENCES `tapir_users` (`user_id`),
  CONSTRAINT `flagged_user_detail_ibfk_2` FOREIGN KEY (`flagged_user_id`) REFERENCES `tapir_users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `flagged_user_detail_category_relation` (
  `flagged_user_detail_id` int NOT NULL,
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `category` varchar(32) NOT NULL,
  PRIMARY KEY (`flagged_user_detail_id`,`category`),
  CONSTRAINT `flagged_user_detail_category_relation_ibfk_1` FOREIGN KEY (`flagged_user_detail_id`) REFERENCES `flagged_user_detail` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ALTER existing tables to match target schema

-- --- arXiv_admin_log ---
-- Remove ON UPDATE CURRENT_TIMESTAMP from `created`,
-- add `old_created` and `updated` columns.
ALTER TABLE `arXiv_admin_log`
  MODIFY COLUMN `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ADD COLUMN `old_created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER `notify`,
  ADD COLUMN `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER `old_created`;

-- --- arXiv_check_results ---
-- Widen `message` from varchar(40) to varchar(200),
-- change `data` from varchar(2000) to text.
ALTER TABLE `arXiv_check_results`
  MODIFY COLUMN `message` varchar(200) DEFAULT NULL,
  MODIFY COLUMN `data` text;

-- --- arXiv_submission_flag ---
-- Add three new flag columns.
ALTER TABLE `arXiv_submission_flag`
  ADD COLUMN `flag_done` smallint NOT NULL DEFAULT '0' AFTER `flag_pdf_opened`,
  ADD COLUMN `flag_done_cleared` smallint NOT NULL DEFAULT '0' AFTER `flag_done`,
  ADD COLUMN `flag_viewed` smallint NOT NULL DEFAULT '0' AFTER `flag_done_cleared`;

-- --- arXiv_submissions ---
-- Add `preflight` column.
ALTER TABLE `arXiv_submissions`
  ADD COLUMN `preflight` tinyint(1) NOT NULL DEFAULT '0' AFTER `metadata_queued_time`;

-- Done

SET FOREIGN_KEY_CHECKS=1;

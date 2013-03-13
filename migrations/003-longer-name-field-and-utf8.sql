--
-- Increase length of name field to 255 chars; ensure all tables are UTF8
--
ALTER TABLE `homesnippets_snippet` MODIFY COLUMN name varchar(255);

ALTER TABLE `auth_group` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `auth_group_permissions` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `auth_message` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `auth_permission` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `auth_user` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `auth_user_groups` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `auth_user_user_permissions` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `django_admin_log` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `django_content_type` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `django_session` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `django_site` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `homesnippets_clientmatchrule` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `homesnippets_snippet` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `homesnippets_snippet_client_match_rules` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;


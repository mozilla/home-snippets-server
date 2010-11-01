DROP TABLE IF EXISTS `auth_group`;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `auth_group_permissions`;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`permission_id`),
  KEY `auth_group_permissions_bda51c3c` (`group_id`),
  KEY `auth_group_permissions_1e014c8f` (`permission_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `auth_message`;
CREATE TABLE `auth_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `message` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auth_message_fbfc09f1` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `auth_permission`;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  KEY `auth_permission_e4470c6e` (`content_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=31 DEFAULT CHARSET=utf8;

INSERT INTO `auth_permission` VALUES 
    (1,'Can add permission',1,'add_permission'),
    (2,'Can change permission',1,'change_permission'),
    (3,'Can delete permission',1,'delete_permission'),
    (4,'Can add group',2,'add_group'),
    (5,'Can change group',2,'change_group'),
    (6,'Can delete group',2,'delete_group'),
    (7,'Can add user',3,'add_user'),
    (8,'Can change user',3,'change_user'),
    (9,'Can delete user',3,'delete_user'),
    (10,'Can add message',4,'add_message'),
    (11,'Can change message',4,'change_message'),
    (12,'Can delete message',4,'delete_message'),
    (13,'Can add content type',5,'add_contenttype'),
    (14,'Can change content type',5,'change_contenttype'),
    (15,'Can delete content type',5,'delete_contenttype'),
    (16,'Can add session',6,'add_session'),
    (17,'Can change session',6,'change_session'),
    (18,'Can delete session',6,'delete_session'),
    (19,'Can add site',7,'add_site'),
    (20,'Can change site',7,'change_site'),
    (21,'Can delete site',7,'delete_site'),
    (22,'Can add log entry',8,'add_logentry'),
    (23,'Can change log entry',8,'change_logentry'),
    (24,'Can delete log entry',8,'delete_logentry'),
    (25,'Can add client match rule',9,'add_clientmatchrule'),
    (26,'Can change client match rule',9,'change_clientmatchrule'),
    (27,'Can delete client match rule',9,'delete_clientmatchrule'),
    (28,'Can add snippet',10,'add_snippet'),
    (29,'Can change snippet',10,'change_snippet'),
    (30,'Can delete snippet',10,'delete_snippet');

DROP TABLE IF EXISTS `auth_user`;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(30) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(75) NOT NULL,
  `password` varchar(128) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
-- password is "admin"
INSERT INTO `auth_user` VALUES (1,'admin','','','lorchard@mozilla.com','sha1$e02fa$ffe4cd90dd27bb62a2a37db06840d757ba32abce',1,1,1,'2010-10-18 20:12:08','2010-10-18 20:12:08');

DROP TABLE IF EXISTS `auth_user_groups`;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`group_id`),
  KEY `auth_user_groups_fbfc09f1` (`user_id`),
  KEY `auth_user_groups_bda51c3c` (`group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `auth_user_user_permissions`;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`permission_id`),
  KEY `auth_user_user_permissions_fbfc09f1` (`user_id`),
  KEY `auth_user_user_permissions_1e014c8f` (`permission_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `django_admin_log`;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime NOT NULL,
  `user_id` int(11) NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_fbfc09f1` (`user_id`),
  KEY `django_admin_log_e4470c6e` (`content_type_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `django_content_type`;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `app_label` (`app_label`,`model`)
) ENGINE=MyISAM AUTO_INCREMENT=11 DEFAULT CHARSET=utf8;

INSERT INTO `django_content_type` VALUES 
    (1,'permission','auth','permission'),
    (2,'group','auth','group'),
    (3,'user','auth','user'),
    (4,'message','auth','message'),
    (5,'content type','contenttypes','contenttype'),
    (6,'session','sessions','session'),
    (7,'site','sites','site'),
    (8,'log entry','admin','logentry'),
    (9,'client match rule','homesnippets','clientmatchrule'),
    (10,'snippet','homesnippets','snippet');

DROP TABLE IF EXISTS `django_session`;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY (`session_key`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `django_site`;
CREATE TABLE `django_site` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `domain` varchar(100) NOT NULL,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
-- you *might* want to change this.
INSERT INTO `django_site` VALUES (1,'snippets.mozilla.com','snippets.mozilla.com');

DROP TABLE IF EXISTS `homesnippets_clientmatchrule`;
CREATE TABLE `homesnippets_clientmatchrule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `description` varchar(200) NOT NULL,
  `exclude` tinyint(1) NOT NULL,
  `startpage_version` varchar(64) DEFAULT NULL,
  `name` varchar(64) DEFAULT NULL,
  `version` varchar(64) DEFAULT NULL,
  `appbuildid` varchar(64) DEFAULT NULL,
  `build_target` varchar(64) DEFAULT NULL,
  `locale` varchar(64) DEFAULT NULL,
  `channel` varchar(64) DEFAULT NULL,
  `os_version` varchar(64) DEFAULT NULL,
  `distribution` varchar(64) DEFAULT NULL,
  `distribution_version` varchar(64) DEFAULT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `homesnippets_snippet`;
CREATE TABLE `homesnippets_snippet` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  `body` longtext NOT NULL,
  `priority` int(11) DEFAULT NULL,
  `disabled` tinyint(1) NOT NULL,
  `preview` tinyint(1) NOT NULL,
  `pub_start` datetime DEFAULT NULL,
  `pub_end` datetime DEFAULT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `homesnippets_snippet_client_match_rules`;
CREATE TABLE `homesnippets_snippet_client_match_rules` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `snippet_id` int(11) NOT NULL,
  `clientmatchrule_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `snippet_id` (`snippet_id`,`clientmatchrule_id`),
  KEY `homesnippets_snippet_client_match_rules_37e31bc4` (`snippet_id`),
  KEY `homesnippets_snippet_client_match_rules_c405ee63` (`clientmatchrule_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

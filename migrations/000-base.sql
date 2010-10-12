BEGIN;CREATE TABLE "auth_permission" (
    "id" integer NOT NULL PRIMARY KEY,
    "name" varchar(50) NOT NULL,
    "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id"),
    "codename" varchar(100) NOT NULL,
    UNIQUE ("content_type_id", "codename")
)
;
CREATE TABLE "auth_group_permissions" (
    "id" integer NOT NULL PRIMARY KEY,
    "group_id" integer NOT NULL,
    "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id"),
    UNIQUE ("group_id", "permission_id")
)
;
CREATE TABLE "auth_group" (
    "id" integer NOT NULL PRIMARY KEY,
    "name" varchar(80) NOT NULL UNIQUE
)
;
CREATE TABLE "auth_user_user_permissions" (
    "id" integer NOT NULL PRIMARY KEY,
    "user_id" integer NOT NULL,
    "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id"),
    UNIQUE ("user_id", "permission_id")
)
;
CREATE TABLE "auth_user_groups" (
    "id" integer NOT NULL PRIMARY KEY,
    "user_id" integer NOT NULL,
    "group_id" integer NOT NULL REFERENCES "auth_group" ("id"),
    UNIQUE ("user_id", "group_id")
)
;
CREATE TABLE "auth_user" (
    "id" integer NOT NULL PRIMARY KEY,
    "username" varchar(30) NOT NULL UNIQUE,
    "first_name" varchar(30) NOT NULL,
    "last_name" varchar(30) NOT NULL,
    "email" varchar(75) NOT NULL,
    "password" varchar(128) NOT NULL,
    "is_staff" bool NOT NULL,
    "is_active" bool NOT NULL,
    "is_superuser" bool NOT NULL,
    "last_login" datetime NOT NULL,
    "date_joined" datetime NOT NULL
)
;
CREATE TABLE "auth_message" (
    "id" integer NOT NULL PRIMARY KEY,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    "message" text NOT NULL
)
;
CREATE TABLE "django_content_type" (
    "id" integer NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL,
    "app_label" varchar(100) NOT NULL,
    "model" varchar(100) NOT NULL,
    UNIQUE ("app_label", "model")
)
;
CREATE TABLE "django_session" (
    "session_key" varchar(40) NOT NULL PRIMARY KEY,
    "session_data" text NOT NULL,
    "expire_date" datetime NOT NULL
)
;
CREATE TABLE "django_site" (
    "id" integer NOT NULL PRIMARY KEY,
    "domain" varchar(100) NOT NULL,
    "name" varchar(50) NOT NULL
)
;
CREATE TABLE "django_admin_log" (
    "id" integer NOT NULL PRIMARY KEY,
    "action_time" datetime NOT NULL,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    "content_type_id" integer REFERENCES "django_content_type" ("id"),
    "object_id" text,
    "object_repr" varchar(200) NOT NULL,
    "action_flag" smallint unsigned NOT NULL,
    "change_message" text NOT NULL
)
;
CREATE TABLE "homesnippets_snippet" (
    "id" integer NOT NULL PRIMARY KEY,
    "name" varchar(80) NOT NULL,
    "body" text NOT NULL,
    "created" datetime NOT NULL,
    "modified" datetime NOT NULL
)
;COMMIT;

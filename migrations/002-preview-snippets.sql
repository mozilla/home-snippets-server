-- Add column for preview-only snippets
alter table homesnippets_snippet add column `preview` tinyint(1) NOT NULL default 0;

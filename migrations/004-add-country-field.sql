-- Add column for country-based geolocation
ALTER TABLE `homesnippets_snippet` ADD COLUMN `country` varchar(16) NOT NULL DEFAULT '';

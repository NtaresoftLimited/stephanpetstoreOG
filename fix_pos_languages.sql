-- Fix POS Language Configuration
-- This SQL will set English as the default language for the POS

-- First, find the English language ID
SELECT id, name, code 
FROM res_lang 
WHERE code = 'en_US' AND active = true;

-- Find the POS config ID
SELECT id, name, default_language_id 
FROM pos_config 
WHERE name = 'Stephan''s Pet Store';

-- Update POS config to use English (replace X with the English language ID from first query)
-- UPDATE pos_config 
-- SET default_language_id = X  -- Replace X with English ID (usually 1)
-- WHERE name = 'Stephan''s Pet Store';

-- Clear the many2many relationship table
-- DELETE FROM pos_config_res_lang_rel 
-- WHERE pos_config_id = (SELECT id FROM pos_config WHERE name = 'Stephan''s Pet Store');

-- Add English to the languages list (replace X with English ID, Y with POS config ID)
-- INSERT INTO pos_config_res_lang_rel (pos_config_id, res_lang_id)
-- VALUES (Y, X);  -- Replace Y with POS ID, X with English ID

--=== SAFE ONE-STEP FIX ===--
-- Run this single query (uncomment to use):

UPDATE pos_config 
SET default_language_id = (SELECT id FROM res_lang WHERE code = 'en_US' AND active = true LIMIT 1)
WHERE name = 'Stephan''s Pet Store';

-- Then clear and reset the languages relation:
DELETE FROM pos_config_res_lang_rel 
WHERE pos_config_id = (SELECT id FROM pos_config WHERE name = 'Stephan''s Pet Store');

INSERT INTO pos_config_res_lang_rel (pos_config_id, res_lang_id)
SELECT 
    (SELECT id FROM pos_config WHERE name = 'Stephan''s Pet Store'),
    (SELECT id FROM res_lang WHERE code = 'en_US' AND active = true LIMIT 1);

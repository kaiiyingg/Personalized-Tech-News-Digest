-- This file defines a PostgreSQL trigger function named update_updated_at_column.
-- The function is intended to be attached to a table as a BEFORE UPDATE trigger.
-- Whenever a row in the table is updated, this function sets the 'updated_at'
-- column to the current timestamp (NOW()), ensuring the column always reflects
-- the last modification time of the row.
--
-- Usage:
--   1. Create this function in your database.
--   2. Attach it to a table using a trigger, for example:
--        CREATE TRIGGER set_updated_at
--        BEFORE UPDATE ON your_table
--        FOR EACH ROW
--        EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
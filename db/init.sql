CREATE ROLE repl_user WITH REPLICATION LOGIN ENCRYPTED PASSWORD 'Qq12345';
SELECT pg_create_physical_replication_slot('replication_slot');

CREATE TABLE hba ( lines text ); 
COPY hba FROM '/var/lib/postgresql/data/pg_hba.conf'; 
INSERT INTO hba (lines) VALUES ('host replication all 0.0.0.0/0 md5'); 
COPY hba TO '/var/lib/postgresql/data/pg_hba.conf'; 
SELECT pg_reload_conf();

CREATE TABLE IF NOT EXISTS emails(id SERIAL PRIMARY KEY, email VARCHAR(70) NOT NULL);
CREATE TABLE IF NOT EXISTS phones(id SERIAL PRIMARY KEY, phnumber VARCHAR(70) NOT NULL);
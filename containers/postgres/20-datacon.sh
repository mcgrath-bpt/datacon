#!/bin/sh
set -eu
developer_password=$(cat /run/secrets/developer_password)
psql -X --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set=ON_ERROR_STOP=1 --set=developer_password="$developer_password" <<'SQL'
CREATE EXTENSION IF NOT EXISTS pg_duckdb;
CREATE ROLE developer LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD :'developer_password';
GRANT datacon_duckdb TO developer;
GRANT CONNECT ON DATABASE datacon TO developer;
CREATE SCHEMA workspace AUTHORIZATION developer;
ALTER ROLE developer IN DATABASE datacon SET search_path = workspace, public;
SQL

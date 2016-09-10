#!/bin/bash
set -e

db_user=${DB_USER:-comses}
db_name=${POSTGRES_DB:-comses_db}
datasets_db=${MIRACLE_DATASETS_DB_NAME:-miracle_datasets}

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER $db_user;
    CREATE DATABASE $db_name IF NOT EXISTS;
    CREATE DATABASE $datasets_db IF NOT EXISTS;
    GRANT ALL PRIVILEGES ON DATABASE $db_name TO $db_user;
    GRANT ALL PRIVILEGES on DATABASE $datasets_db to $db_user;
EOSQL

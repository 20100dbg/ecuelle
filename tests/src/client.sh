#!/bin/sh

if [ ${DB_TYPE} = "mysql" ]; then
    mysql -h ${DB_HOST} -P ${DB_PORT} -u ${DB_USER} -p${DB_PASSWORD} < queries.sql

elif [ ${DB_TYPE} = "postgres" ]; then
    PGPASSWORD=${DB_PASSWORD} psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} < queries.sql
        
elif [ ${DB_TYPE} = "mssql" ]; then
    sqlcmd -S ${DB_HOST},${DB_PORT} -U ${DB_USER} -P ${DB_PASSWORD} < queries.sql

fi


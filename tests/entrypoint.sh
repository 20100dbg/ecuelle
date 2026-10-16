#!/bin/sh

#Make sure to use up-to-date $PATH
. ~/.bashrc

if [ -n "$SQL_SCRIPTS_DIR" ] && [ -d "$SQL_SCRIPTS_DIR" ]; then

    if [ ${DB_TYPE} = "mssql" ] && [ -n ${DB_NAME} ]; then
        sqlcmd -N o -S ${DB_HOST},${PROXY_PORT} -U sa -P ${DB_PASSWORD} -Q "create database ${DB_NAME}"
    fi

    for sql_file in "$SQL_SCRIPTS_DIR"/*.sql; do
        [ -f "$sql_file" ] || continue
        echo "Executing $sql_file"

        if [ ${DB_TYPE} = "mysql" ]; then
            mysql -h ${DB_HOST} -P ${PROXY_PORT} -u ${DB_USER} -p"${DB_PASSWORD}" -D ${DB_NAME} < "$sql_file"

        elif [ ${DB_TYPE} = "postgres" ]; then
            PGPASSWORD=${DB_PASSWORD} psql -h ${DB_HOST} -p ${PROXY_PORT} -U ${DB_USER} -d ${DB_NAME} < "$sql_file"
                
        elif [ ${DB_TYPE} = "mssql" ]; then
            sqlcmd -N o -S ${DB_HOST},${PROXY_PORT} -U sa -P ${DB_PASSWORD} -d ${DB_NAME} -Q "$(cat $sql_file)"

        fi

    done
fi

cd /app
. .venv/bin/activate
python3 client.py

#php client.php

#sh client.sh
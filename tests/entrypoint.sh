#!/bin/sh

#Make sure to use up-to-date $PATH
. ~/.bashrc

if [ -n "$1" ] && [ "$1" = "-h" ]; then
    echo "Usage :"
    echo "docker compose run --name ecuelle-test --rm test [query types] [script]"
    echo "docker compose run --name ecuelle-test --rm test basic,invalid,edge_cases,parameterized sh|php|pdo|python"
    exit 0;
fi

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

case "$2" in
    sh)
        echo '--- Bash script start'
        bash client.sh
        echo '--- Bash script done'
        ;;
    php)
        echo '--- PHP script start'
        php client.php $1
        echo '--- PHP script done'
        ;;
    pdo)
        echo '--- PDO script start'
        php client_pdo.php $1
        echo '--- PDO script done'
        ;;
    python)
        echo '--- Python script start'
        python3 client.py $1
        echo '--- Python script done'
        ;;
    "")
        echo '--- PHP script start'
        php client.php $1
        echo '--- PHP script done'

        echo '--- PDO script start'
        php client_pdo.php $1
        echo '--- PDO script done'

        echo '--- Python script start'
        python3 client.py $1
        echo '--- Python script done'
        ;;
    *)
        echo "Usage: $0 [sh|php|pdo|python]"
        exit 1
        ;;
esac

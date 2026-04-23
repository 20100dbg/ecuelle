#!/bin/bash

DB_HOST="127.0.0.1"
DB_PORT=3306
DB_USER="root"
DB_PASSWORD="my-secret-password123"
DB_NAME="sample"

if [ -z $1 ];
    echo Usage: $0 <mysql,postgres,mssql>
    echo $0 mysql
    exit 1
fi

echo Running test against $1

source .venv/bin/activate
python client.py --dbms $1 --test

php client.php --dbms $1 --test


if [ "$1" == "mysql" ]; then
    echo "SELECT 123" | mysql -u $DB_USER -h $DB_HOST -P $DB_PORT -p$DB_PASSWORD -D $DB_NAME
fi
## Ecuelle

Ecuelle is a MySQL/PostgreSQL proxy.






docker network create -d bridge ecuelle-network

docker build -t ecuelle .

./start_db.sh


docker run -it --name ecuelle --rm --mount type=bind,src=./src,dst=/app/src --network=ecuelle-network -e PROXY_PORT=3306 -e DB_TYPE=mysql -e SERVER_HOST=mysql_db -e SERVER_PORT=3306 -p8080:80 -p3306:3306 ecuelle:latest








## Test environment

-s : IP/hostname of database server
-p : port the database server is listening on


DB_TYPE : DBMS we want to use : mysql, postgres, mssql
PROXY_PORT : the port we want the app to connect to. Default is : mysql=3306, postgres=5432, mssql=1433

DB_TYPE=mysql PROXY_PORT=3306 docker compose --profile mysql run --remove-orphans --service-ports app -s mysql -p 3306

DB_TYPE=postgres PROXY_PORT=5432 docker compose --profile postgres run --remove-orphans --service-ports app -s postgres -p 5432

DB_TYPE=mssql PROXY_PORT=1433 docker compose --profile mssql run --remove-orphans --service-ports app -s mssql -p 1433



## Setup client

//sudo apt install python3-dev default-libmysqlclient-dev build-essential pkg-config unixodbc

sudo apt install libodbc2 unixodbc


python -m venv .venv
source .venv/bin/activate
pip install psycopg mysqlclient pyodbc

python client.py --dbms mysql --host 127.0.0.1 --port 3306 --user root --password my-secret-password --database sample

python client.py --dbms postgres --host 127.0.0.1 --port 5432 --user postgres --password my-secret-password --database postgres


## Populate database

`mysql -u root -h 127.0.0.1 -p < sample.sql`

`psql -h 127.0.0.1 -p 5432 -U postgres < sample_postgres.sql`

`tsql -h 127.0.0.1 -p 5432 -U postgres < sample_postgres.sql`


## Clean
docker stop mysql_db postgres_db mssql_db
docker rm mysql_db postgres_db mssql_db
docker volume rm ecuelleXXXXXXX


_____________________________


docker pull postgres:16.13-alpine
docker pull postgres:15.17-alpine
docker pull postgres:14.22-alpine


## Ecuelle

Ecuelle is a MySQL/PostgreSQL/MSSQL proxy.
It logs and display in a Web UI intercepted queries and results.

Please note this is a work-in-progress project, there is still a lot to do !

### How to use

The easiest is to use provided `start.sh` script.
It will run ecuelle with default or custom settings, and can start a database server if needed.

```
Usage: start.sh --dbms <mysql,postgres,mssql> [--host IP/HOST] [--port PORT] [--listen PORT] [--docker-db]
Options:
  --dbms DBMS       Which DBMS to use: mysql, postgres or mssql
  --host IP/HOST    Database IP/hostname to connect to (only if --docker-db is not set)
  --port PORT       Database port to connect to (only if --docker-db is not set)
  --listen PORT     Listening port for Ecuelle
  --docker-db       Start a database server inside a docker
  --password        Set database password for default admin user

```

Example: start Ecuelle as Mysql proxy and start Mysql server, with default settings
```
./start.sh --dbms mysql --docker-db
```

### Setup client

Install dependencies
```
sudo apt install python3-dev default-libmysqlclient-dev pkg-config
```

Install python packages
```
python -m venv .venv
source .venv/bin/activate
pip install psycopg mysqlclient mssql-python
```

Start client
```
python client.py --dbms mysql --host 127.0.0.1 --port 3306 --user root --password my-secret-password123 --database sample
```

Another example
```
python client.py --dbms postgres --host 127.0.0.1 --port 5432 --user postgres --password my-secret-password123 --database postgres
```

### Populate database

`mysql -u root -h 127.0.0.1 -p < samples/mysql.sql`

`psql -h 127.0.0.1 -p 5432 -U postgres < samples/postgres.sql`

```
docker exec -it mssql_db /opt/mssql-tools/bin/sqlcmd -U sa -H 127.0.0.1 -Q "create database sample"
docker exec -it mssql_db /opt/mssql-tools/bin/sqlcmd -U sa -H 127.0.0.1 -d sample -Q "$(cat samples/mssql.sql)"
```
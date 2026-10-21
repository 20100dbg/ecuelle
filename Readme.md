<p align="center">
  <img src="https://github.com/20100dbg/ecuelle/blob/master/ecuelle.png?raw=true" alt="Logo" width="120" />
</p>

<h1 align="center">Ecuelle</h1>


Ecuelle is a MySQL/PostgreSQL/MSSQL proxy.
It logs and display in a Web UI intercepted queries and results.

Please note this is a work-in-progress project, there is still a lot to do !


### How to use
Features:
- Supports MySQL, PostgreSQL, MS SQL
- Shows queries, results, and errors


### How to use

Clone this project
```
git clone https://github.com/20100dbg/ecuelle
```

Copy .env.dist to .env and edit .env for your needs
```
cp .env.dist .env
nano .env
```

Once inside the project's folder, run:
```
docker compose --profile <DBMS> up --build
```

You can bypass .env file parameters with env vars:
```
DB_VERSION=8.4 DB_PORT=3306 docker compose --profile <DBMS> up --build
```

You can also start Ecuelle alone, no database
```
docker compose up --build
```

### Shut it down

Don't forget to specify the used profile:
```
docker compose --profile <DBMS> down -v
```

### Test

Don't forget to first run with `docker compose --profile <DBMS> up --build`
First build the test client
```
docker compose build test
```

You can run an automated test client to run a few SQL queries
```
docker compose run --name ecuelle-test --rm test
```

Run fixtures before testing SQL queries
```
SQL_SCRIPTS_DIR=./tests/fixtures/<DBMS> docker compose run --name ecuelle-test --rm test
```

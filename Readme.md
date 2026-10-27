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

You can run Ecuelle as-is, but I heavily recommend running it inside [Docker](https://docs.docker.com/engine/install/)

Once inside the project's folder, run:
```
docker compose --profile <DBMS> up --build
```

You can bypass .env file parameters with env vars:
```
DB_VERSION=8.4 DB_PORT=3306 docker compose --profile <DBMS> up --build
```

You can also start Ecuelle alone, without starting a database
```
docker compose up --build
```

### Shut it down

Don't forget to specify the used profile:
```
docker compose --profile <DBMS> down
```

Use `-v` to remove the database volume. This erase your database data !
```
docker compose --profile <DBMS> down -v
```

### Test

Don't forget to first run with `docker compose --profile <DBMS> up --build`

Build the test client
```
docker compose build test
```

You can run an automated test client that will execute a few SQL queries
```
docker compose run --name ecuelle-test --rm test
```

Run fixtures before testing SQL queries
```
SQL_SCRIPTS_DIR=./tests/fixtures/<DBMS> docker compose run --name ecuelle-test --rm test
```

Start a shell into test environment. This gives access to every DBMS clients, test scripts and fixtures.
```
docker compose run bash --name ecuelle-test --rm test bash
```

### Dependancies

[sql-highlight](https://github.com/scriptcoded/sql-highlight)

[Bulma CSS](https://bulma.io/)

[Vue3](https://vuejs.org/)

Build sql-highlight
```
#needs npm
sudo apt install npm
git clone https://github.com/scriptcoded/sql-highlight
cd sql-highlight/
npm init -y
npm install sql-highlight esbuild
echo -e 'const { highlight, getSegments } = require("sql-highlight");\nwindow.highlight = highlight;\nwindow.getSegments = getSegments;' > entry.js
npx esbuild entry.js --bundle --minify --platform=browser --format=iife --target=es2018 --outfile=sql-highlight.browser.js
```


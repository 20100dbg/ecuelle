## Ecuelle

Ecuelle is a MySQL/PostgreSQL proxy.



## Test environment

Check start_postgres.sh and start_mysql.sh
You can set root password, listening port and more.


## Populate database

`mysql -u root -h 127.0.0.1 -p < sample.sql`

`psql -h 127.0.0.1 -p 5432 -U postgres < sample_postgres.sql`


## Start proxy

`python proxy --dbms mysql -l 3306 -p 3307`


_____________________________


docker pull postgres:16.13-alpine
docker pull postgres:15.17-alpine
docker pull postgres:14.22-alpine


docker exec -it -u postgres postgres-container bash

createdb sample

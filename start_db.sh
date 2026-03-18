#!/bin/sh

PASSWORD=my-secret-password

docker pull mysql:5.7
docker run --rm --name mysql_db --network=ecuelle-network -v ./conf:/etc/mysql/conf.d --volume mysql_data:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=$PASSWORD mysql:5.7

#!/bin/bash

ROOT_PASSWORD=my-secret-password
LISTENING_PORT=3307

docker pull mysql:latest

mkdir -p ./mysql

docker run -d \
  --name mysql_container \
  -e MYSQL_ROOT_PASSWORD=$ROOT_PASSWORD \
  --mount type=bind,src=./mysql,dst=/var/lib/mysql \
  -p $LISTENING_PORT:3306 \
  mysql:latest

echo;
echo;
echo Listening on $LISTENING_PORT
echo Root password is $ROOT_PASSWORD

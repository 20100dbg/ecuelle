#!/bin/bash

ROOT_PASSWORD=my-secret-password
LISTENING_PORT=5432
VERSION=14.22-alpine

docker pull postgres:$VERSION
mkdir -p ./postgres


docker run -d \
  --name postgres-container \
  --mount type=bind,src=./postgres,dst=/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=$ROOT_PASSWORD \
  -p $LISTENING_PORT:5432 \
  postgres:$VERSION

echo;
echo;
echo Listening on $LISTENING_PORT
echo Root password is $ROOT_PASSWORD

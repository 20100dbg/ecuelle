#!/bin/bash

source .env

docker compose --profile $DB_TYPE up -d

echo;
echo Ecuelle Web UI is at: http://127.0.0.1:8080
echo Forwarding $DB_TYPE from 127.0.0.1:$PROXY_PORT to $DB_HOST:$DB_PORT
echo;

#!/bin/sh

for i in "$@"; do
  case $i in
    -h|--help)
      echo "Usage: start.sh --dbms <mysql,postgres,mssql> [--host IP/HOST] [--port PORT] [--listen PORT] [--docker-db]"
      echo "Options:"
      echo "  --dbms DBMS\t\tWhich DBMS to use: mysql, postgres or mssql"
      echo "  --host IP/HOST\tDatabase IP/hostname to connect to (only if --docker-db is not set)"
      echo "  --port PORT\t\tDatabase port to connect to (only if --docker-db is not set)"
      echo "  --listen PORT\t\tListening port for Ecuelle"
      echo "  --docker-db\t\tStart a database server inside a docker"
      echo "  --password\t\tSet database password for default admin user"
      shift # past argument
      exit 0
      ;;
    --dbms)
      DBMS="$2"
      shift # past argument
      shift # past value
      ;;
    --host)
      SERVER_HOST="$2"
      shift # past argument
      shift # past value
      ;;
    --port)
      SERVER_PORT="$2"
      shift # past argument
      shift # past value
      ;;
    --listen)
      PROXY_PORT="$2"
      shift # past argument
      shift # past value
      ;;
    --docker-db)
      DOCKER_DB=1
      shift # past argument
      ;;
    --password)
      PASSWORD="$2"
      shift # past argument
      shift # past value
      ;;
    -*|--*)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

if [ -z $DBMS ]; then
    echo Please set --dbms option
    exit 1
fi

if [ -z $SERVER_PORT ]; then
    case $DBMS in
      mysql) SERVER_PORT=3306 ;;
      postgres) SERVER_PORT=5432 ;;
      mssql) SERVER_PORT=1433 ;;
    esac
fi

if [ -z $PROXY_PORT ]; then PROXY_PORT=$SERVER_PORT; fi

if [ $DOCKER_DB ]; then
    SERVER_HOST="${DBMS}_db"
    if [ -z $PASSWORD ]; then PASSWORD=my-secret-password123; fi
else
    if [ -z $SERVER_HOST ]; then echo "Without --docker-db, please set --host option"; exit 1; fi
fi

echo Creating network
#docker network create -d bridge ecuelle-network

echo Building Ecuelle
docker build -t ecuelle .



if [ $DOCKER_DB ]; then

    echo Starting $DBMS database docker

    docker stop mysql_db postgres_db mssql_db 2>/dev/null 1>/dev/null

    if [ $DBMS = "mysql" ]; then
        TAG=5.7
        USER=root
        docker pull mysql:$TAG >/dev/null
        docker run -d --rm --name mysql_db --network=ecuelle-network -v ./conf:/etc/mysql/conf.d --volume mysql_data:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=$PASSWORD mysql:$TAG

    elif [ $DBMS = "postgres" ]; then
        TAG=14.22-alpine
        USER=postgres
        docker pull postgres:$TAG >/dev/null
        docker run -d --rm --name postgres_db --network=ecuelle-network --volume postgres_data:/var/lib/postgresql/data -e POSTGRES_USER=$USER -e POSTGRES_PASSWORD=$PASSWORD postgres:$TAG
        
    elif [ $DBMS = "mssql" ]; then
        TAG=2017-latest
        USER=sa
        docker pull mcr.microsoft.com/mssql/server:$TAG >/dev/null
        docker run -d --rm --name mssql_db --network=ecuelle-network --volume mssql_data:/var/opt/mssql/data -e ACCEPT_EULA=Y -e MSSQL_SA_PASSWORD=$PASSWORD mcr.microsoft.com/mssql/server:$TAG
    fi

    echo;
    echo Creds : $USER / $PASSWORD
    echo DBMS : $DBMS:$TAG
fi

echo;
echo Ecuelle Web UI is at: http://127.0.0.1:8080
echo Forwarding $DBMS from 127.0.0.1:$PROXY_PORT to $SERVER_HOST:$SERVER_PORT
echo;

docker run -it --name ecuelle --rm \
--mount type=bind,src=./src,dst=/app/src --network=ecuelle-network \
-e PROXY_PORT=$PROXY_PORT -e DB_TYPE=$DBMS \
-e SERVER_HOST=$SERVER_HOST -e SERVER_PORT=$SERVER_PORT \
-p8080:80 -p$PROXY_PORT:$PROXY_PORT ecuelle:latest


## Docker

Set root password
Edit start.sh and change ROOT_PASSWORD variable


## Populate database

mysql -u root -h 127.0.0.1 -p < sample.sql


## Connect and use

mysql -u root -h 127.0.0.1 -p


## Reset database

docker stop mysql_container
docker rm mysql_container
sudo rm -rf ./mysql
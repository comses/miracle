#!/usr/bin/env bash

sudo docker-compose start files
sudo docker-compose start db
sudo docker-compose start radiant
sudo docker-compose start deployr
echo Waiting for Postgres to Fire up
sleep 20
sudo docker-compose start django

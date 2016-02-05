#!/usr/bin/env bash

apt-get update
apt-get install -y curl python-pip

curl -sSL https://get.docker.com/ | sh

pip install -U docker-compose

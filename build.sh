#! /usr/bin/env bash

MIRACLE_UID=${MIRACLE_UID:-2000}

# generate custom dhparam.pem for logjam https://blog.cloudflare.com/logjam-the-latest-tls-vulnerability-explained/
if [ -f nginx/dhparam.pem ]; then
    echo "Using existing nginx/dhparam.pem";
else 
    openssl dhparam -out nginx/dhparam.pem 4096;
fi
# make sure you copy server key and server crt to nginx/ directory
echo "For production, copy the SSL key and cert to nginx/ as server.crt and server.key before deployment (may consider switch to lets encrypt at some point)"
if [ -f nginx/server.crt ]; then
    echo "Using existing nginx/server.crt"
else
    echo "For production, copy the appropriate SSL key and cert to nginx/ as server.crt and server.key before deployment (consider switch to lets encrypt)";
    cd nginx;
    sh make-cert.sh;
    cd ..;
fi
cd docker;
echo "Creating base Docker images with MIRACLE_UID=$MIRACLE_UID"
docker build --build-arg MIRACLE_UID=$MIRACLE_UID -t miracle/min -f min.Dockerfile .
for dn in base r;
    do docker build -t miracle/$dn -f $dn.Dockerfile .;
done
cd ..;
docker-compose build
chmod a+x django/entrypoint.sh

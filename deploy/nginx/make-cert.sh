#!/usr/bin/env bash

echo "Creates self-signed cert and key for local testing purposes."
echo "Invoke via % $0 <hostname> - if hostname is blank, defaults to localhost."

hostname="${1:-localhost}"

if [ -f server.crt ]; then
    echo "server.crt already exists, aborting.";
else
    echo "Creating server.key and server.crt for $hostname";
    openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -days 3650 -nodes -subj "/C=US/ST=Arizona/L=Tempe/O=ASU/CN=$hostname" -extensions v3_ca
fi


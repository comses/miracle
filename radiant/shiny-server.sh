#!/bin/sh

# Make sure the directory for individual app logs exists
exec shiny-server >> /var/log/shiny-server.log 2>&1

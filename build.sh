#! /usr/bin/env bash

# uid=

# # Get file name and line number
# while test $# -gt 0
# do
# 	if [[ "$1" == "-uid" ]]; then
# 		shift
# 		uid="$1"
# 		shift
# 	fi
# done

# # Ensure that the line number is valid
# re='^[0-9]+$'
# if ! [[ $uid =~ $re ]]; then
#    echo "Error: invalid uid number" >&2; exit 1
# fi

# baseimages/min, base, r

#cd docker && docker build -t miracle/min --build-arg uid=$uid .
cd docker && docker build -t miracle/min -f min.Dockerfile . && \
    docker build -t miracle/base -f base.Dockerfile . && \
    docker build -t miracle/r -f r.Dockerfile . && \
    cd .. && docker-compose build && docker-compose up
# in Dockerfile
# ARG uid
# adduser -u $uid


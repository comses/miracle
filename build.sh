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
cd docker;
for dn in min base r;
do docker build -t miracle/$dn -f $dn.Dockerfile .;
done
cd ..;
docker-compose build
# in Dockerfile
# ARG uid
# adduser -u $uid


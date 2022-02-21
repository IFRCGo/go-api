#!/bin/bash -e
cmd="$@"

export DOCKER_HOST_IP=$(/sbin/ip route|awk '/default/ { print $3 }')

wait-for-it ${DJANGO_DB_HOST:-db}:${DJANGO_DB_PORT-5432}
>&2 echo "Postgres is up - continuing..."
exec $cmd

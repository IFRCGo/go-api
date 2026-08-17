#!/bin/bash -e

export DOCKER_HOST_IP=$(/sbin/ip route|awk '/default/ { print $3 }')

wait-for-it ${DJANGO_DB_HOST:-db}:${DJANGO_DB_PORT:-5432}
>&2 echo "Postgres is up - continuing..."
# NOTE: exec "$@" (not an unquoted variable) so arguments survive verbatim.
# Re-splitting them drops the quoting, which turns `bash -c 'a b c'` into
# `bash -c a b c` — the command silently becomes just `a`.
exec "$@"

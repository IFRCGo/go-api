#!/bin/bash -e

export DOCKER_HOST_IP=$(/sbin/ip route|awk '/default/ { print $3 }')

# NOTE: exec "$@" (not an unquoted variable) so arguments survive verbatim.
# Re-splitting them drops the quoting, which turns `bash -c 'a b c'` into
# `bash -c a b c` — the command silently becomes just `a`.
exec "$@"

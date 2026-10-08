#!/bin/bash

# Web entrypoint for local development (docker compose `serve`).
#
# DOCKER_HOST_IP is the container's default gateway, i.e. the docker host. It is
# added to INTERNAL_IPS so django-debug-toolbar shows for requests from the host.

set -euo pipefail

DOCKER_HOST_IP=$(ip route | awk '/default/ { print $3 }')
export DOCKER_HOST_IP

exec python manage.py runserver 0.0.0.0:8000

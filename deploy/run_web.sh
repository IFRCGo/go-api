#!/bin/bash

# Web entrypoint for the containerised deployment: gunicorn serves the app
# directly on :80 (no nginx / unix socket). Static/media are served by the
# configured object-storage backend; db-migrate + collectstatic run as
# separate pre-deploy hooks, not here.
#
# --preload imports the app in the master before forking, so an import error
# (missing env, bad settings) fails the process immediately instead of workers
# silently crash-looping.
#
# The access log format carries the X-Forwarded-For chain: %(h)s is the peer
# address, which behind an ingress is the controller pod, not the client.

set -euo pipefail

exec gunicorn main.wsgi:application \
    --name go-api \
    --preload \
    --bind 0.0.0.0:80 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --log-level=info \
    --access-logfile=- \
    --error-logfile=- \
    --access-logformat '%(h)s %(l)s %(u)s %(t)s [%({x-forwarded-for}i)s] "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

#!/bin/bash -e

./manage.py wait_for_resources --db --celery-broker

# Prod uses HeartbeatDatabaseScheduler so banjo-celery-probe can check liveness
# (see deploy/helm/values.yaml); locally the plain DatabaseScheduler is enough.
exec celery -A main beat -l INFO

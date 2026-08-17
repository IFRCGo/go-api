#!/bin/bash -e
# Wait for the celery broker. main/entrypoint.sh waits for the db, not the broker.
#
# TODO: Replace with wait_for_resources once banjo-stack is implemented

BROKER_HOST_PORT=$(python -c "
import os
from urllib.parse import urlparse

url = urlparse(os.environ['CELERY_REDIS_URL'])
print(f'{url.hostname}:{url.port or 6379}')
")

echo "Waiting for celery broker at ${BROKER_HOST_PORT}..."
wait-for-it "${BROKER_HOST_PORT}"
>&2 echo "Celery broker is up - continuing..."

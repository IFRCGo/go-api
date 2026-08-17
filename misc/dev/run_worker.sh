#!/bin/bash -e
# Uses the management command for Django's autoreloader.

# TODO(susilnem): Use wait_for_resources once banjo-stack is implemented
./misc/wait-for-broker.sh

exec ./manage.py run_celery_dev

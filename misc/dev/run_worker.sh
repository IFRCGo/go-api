#!/bin/bash -e
# Uses the management command for Django's autoreloader.

./manage.py wait_for_resources --db --celery-broker

exec ./manage.py run_celery_dev

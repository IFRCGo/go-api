#!/bin/bash -e

./misc/wait-for-broker.sh

exec celery -A main beat -l INFO

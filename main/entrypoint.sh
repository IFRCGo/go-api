#!/bin/bash
set -e
cmd="$@"

export DATABASE_URL=postgres://$DJANGO_DB_USER:$DJANGO_DB_PASS@$DJANGO_DB_HOST:5432/$DJANGO_DB_USER

function postgres_ready(){
python << END
import sys
import psycopg2
try:
    conn = psycopg2.connect(dbname="$DJANGO_DB_NAME", user="$DJANGO_DB_USER", password="$DJANGO_DB_PASS", host="$DJANGO_DB_HOST")
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

until postgres_ready; do
  >&2 echo "Postgres is unavailable - trying again..."
  sleep 1
done

>&2 echo "Postgres is up - continuing..."
exec $cmd
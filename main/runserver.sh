#!/bin/bash
mkdir -p $HOME/logs $HOME/static

# load fixture data, apply migrations, collect static files
python manage.py loaddata Countries DisasterTypes
python manage.py migrate
python manage.py collectstatic --noinput --clear
python manage.py collectstatic --noinput -l

# Prepare log files and start outputting logs to stdout
touch $HOME/logs/gunicorn.log
touch $HOME/logs/access.log

tail -n 0 -f $HOME/logs/*.log &

echo Starting nginx 

# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn main.wsgi:application \
    --name main \
    --bind unix:django_app.sock \
    --workers 3 \
    --log-level=info \
    --log-file=$HOME/logs/gunicorn.log \
    --access-logfile=$HOME/logs/access.log & 

exec service nginx start
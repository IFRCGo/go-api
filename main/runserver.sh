#!/bin/bash
mkdir -p $HOME/logs $HOME/static

# apply migrations, load fixture data, collect static files
python manage.py migrate
python manage.py loaddata Countries DisasterTypes
python manage.py collectstatic --noinput --clear
python manage.py collectstatic --noinput -l

# Prepare log files and start outputting logs to stdout
touch $HOME/logs/gunicorn.log
touch $HOME/logs/access.log
touch $HOME/logs/ingest_mdb.log

# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn main.wsgi:application \
    --name main \
    --bind unix:django_app.sock \
    --workers 3 \
    --log-level=info \
    --log-file=$HOME/logs/gunicorn.log \
    --access-logfile=$HOME/logs/access.log &

# set up cron
echo export IFRC_FTPHOST=$IFRC_FTPHOST >> $HOME/.env
echo export IFRC_FTPUSER=$IFRC_FTPUSER >> $HOME/.env
echo export IFRC_FTPPASS=$IFRC_FTPPASS >> $HOME/.env
echo export PATH=$PATH:/usr/local/bin >> $HOME/.env
(echo '0 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py ingest_mdb >> /home/ifrc/logs/ingest_mdb.log 2>&1') | crontab -
service cron start

tail -n 0 -f $HOME/logs/*.log &

echo Starting nginx
exec service nginx start

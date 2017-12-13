#!/bin/bash
mkdir -p $HOME/logs $HOME/static

# apply migrations, load fixture data, collect static files
python manage.py migrate
python manage.py loaddata Regions Countries DisasterTypes Actions
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
    --bind unix:/home/ifrc/django_app.sock \
    --workers 3 \
    --timeout 120 \
    --log-level=info \
    --log-file=$HOME/logs/gunicorn.log \
    --access-logfile=$HOME/logs/access.log &

# set up cron
rm $HOME/.env
echo "export GO_FTPHOST=\"$GO_FTPHOST\"" >> $HOME/.env
echo "export GO_FTPUSER=\"$GO_FTPUSER\"" >> $HOME/.env
echo "export GO_FTPPASS=\"$GO_FTPPASS\"" >> $HOME/.env
echo "export GO_DBPASS=\"$GO_DBPASS\"" >> $HOME/.env
echo "export PATH=\"$PATH:/usr/local/bin\"" >> $HOME/.env
echo "export DJANGO_SECRET_KEY=\"$DJANGO_SECRET_KEY\"" >> $HOME/.env
echo "export DJANGO_DB_NAME=\"$DJANGO_DB_NAME\"" >> $HOME/.env
echo "export DJANGO_DB_USER=\"$DJANGO_DB_USER\"" >> $HOME/.env
echo "export DJANGO_DB_PASS=\"$DJANGO_DB_PASS\"" >> $HOME/.env
echo "export DJANGO_DB_HOST=\"$DJANGO_DB_HOST\"" >> $HOME/.env
echo "export DJANGO_DB_PORT=\"$DJANGO_DB_PORT\"" >> $HOME/.env
echo "export APPEALS_USER=\"$APPEALS_USER\"" >> $HOME/.env
echo "export APPEALS_USER=\"$APPEALS_USER\"" >> $HOME/.env
echo "export ES_HOST=\"$ES_HOST\"" >> $HOME/.env
(echo '30 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py ingest_mdb >> /home/ifrc/logs/ingest_mdb.log 2>&1') | crontab -
(echo '45 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py ingest_appeals >> /home/ifrc/logs/ingest_appeals.log 2>&1') | crontab -
(echo '15 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py ingest_gdacs >> /home/ifrc/logs/ingest_gdacs.log 2>&1') | crontab -
service cron start

tail -n 0 -f $HOME/logs/*.log &

echo Starting nginx
exec service nginx start

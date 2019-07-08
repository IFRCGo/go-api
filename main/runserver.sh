#!/bin/bash
mkdir -p $HOME/logs $HOME/static

# apply migrations, load fixture data, collect static files
python manage.py migrate
#python manage.py loaddata Regions Countries Districts DisasterTypes Actions #Needed only in case of empty database – otherwise it can cause conflicts
python manage.py collectstatic --noinput --clear
python manage.py collectstatic --noinput -l
python manage.py make_permissions

# Add server name(s) to django settings and nginx - later maybe only nginx would be enough, and ALLOWED_HOSTS could be "*"
if [ "$API_FQDN"x = prddsgocdnapi.azureedge.netx ]; then
    sed -i 's/\$NGINX_SERVER_NAME/'$API_FQDN' api.go.ifrc.org/g' /etc/nginx/sites-available/nginx.conf
    sed -i "s/ALLOWED_HOSTS.append(production_url)/ALLOWED_HOSTS.append(production_url)\n    ALLOWED_HOSTS.append('api.go.ifrc.org')/" $HOME/go-api/main/settings.py
else
    sed -i 's/\$NGINX_SERVER_NAME/'$API_FQDN'/g' /etc/nginx/sites-available/nginx.conf
fi

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
echo "export APPEALS_PASS=\"$APPEALS_PASS\"" >> $HOME/.env
echo "export ES_HOST=\"$ES_HOST\"" >> $HOME/.env
echo "export EMAIL_HOST=\"$EMAIL_HOST\"" >> $HOME/.env
echo "export EMAIL_PORT=\"$EMAIL_PORT\"" >> $HOME/.env
echo "export EMAIL_USER=\"$EMAIL_USER\"" >> $HOME/.env
echo "export EMAIL_PASS=\"$EMAIL_PASS\"" >> $HOME/.env
echo "export AZURE_STORAGE_ACCOUNT=\"$AZURE_STORAGE_ACCOUNT\"" >> $HOME/.env
echo "export AZURE_STORAGE_KEY=\"$AZURE_STORAGE_KEY\"" >> $HOME/.env
echo "export API_FQDN=\"$API_FQDN\"" >> $HOME/.env
echo "export FRONTEND_URL=\"$FRONTEND_URL\"" >> $HOME/.env
echo "export PRODUCTION=\"$PRODUCTION\"" >> $HOME/.env
echo "export TEST_EMAILS=\"$TEST_EMAILS\"" >> $HOME/.env

(crontab -l 2>/dev/null; echo 'SHELL=/bin/bash') | crontab -
(crontab -l 2>/dev/null; echo '15 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py ingest_appeal_docs >> /home/ifrc/logs/ingest_appeal_docs.log 2>&1') | crontab -
#(crontab -l 2>/dev/null; echo '30 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py ingest_mdb >> /home/ifrc/logs/ingest_mdb.log 2>&1') | crontab -
(crontab -l 2>/dev/null; echo '45 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py ingest_appeals >> /home/ifrc/logs/ingest_appeals.log 2>&1') | crontab -
(crontab -l 2>/dev/null; echo '51 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py revoke_staff_status >> /home/ifrc/logs/revoke_staff_status.log 2>&1') | crontab -
(crontab -l 2>/dev/null; echo '*/20 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py ingest_gdacs >> /home/ifrc/logs/ingest_gdacs.log 2>&1') | crontab -
#(crontab -l 2>/dev/null; echo '0 2 * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py ingest_who >> /home/ifrc/logs/ingest_who.log 2>&1') | crontab -
(crontab -l 2>/dev/null; echo '*/5 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py index_and_notify >> /home/ifrc/logs/index_and_notify.log 2>&1') | crontab -
service cron start

tail -n 0 -f $HOME/logs/*.log &

echo Starting nginx
exec nginx -g 'daemon off;'

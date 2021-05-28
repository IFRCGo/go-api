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
    sed -i 's/\$NGINX_SERVER_NAME/'$API_FQDN' api.go.ifrc.org goadmin.ifrc.org/g' /etc/nginx/sites-available/nginx.conf
    sed -i "s/ALLOWED_HOSTS.append(PRODUCTION_URL)/ALLOWED_HOSTS.append(PRODUCTION_URL)\n    ALLOWED_HOSTS.append('api.go.ifrc.org')\n    ALLOWED_HOSTS.append('goadmin.ifrc.org')/" $HOME/go-api/main/settings.py
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
# Exporting env vars, like: echo "export PRODUCTION=\"$PRODUCTION\"" >> $HOME/.env
printenv | sed 's/^\([a-zA-Z0-9_]*\)=\(.*\)$/export \1="\2"/g' > $HOME/.env

(crontab -l 2>/dev/null; echo 'SHELL=/bin/bash') | crontab -
(crontab -l 2>/dev/null; echo '15 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py ingest_appeal_docs >> /home/ifrc/logs/ingest_appeal_docs.log 2>&1') | crontab -
#(crontab -l 2>/dev/null; echo '30 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py ingest_mdb >> /home/ifrc/logs/ingest_mdb.log 2>&1') | crontab -
(crontab -l 2>/dev/null; echo '45 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py ingest_appeals >> /home/ifrc/logs/ingest_appeals.log 2>&1') | crontab -
(crontab -l 2>/dev/null; echo '51 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py revoke_staff_status >> /home/ifrc/logs/revoke_staff_status.log 2>&1') | crontab -
(crontab -l 2>/dev/null; echo '*/20 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py ingest_gdacs >> /home/ifrc/logs/ingest_gdacs.log 2>&1') | crontab -
#(crontab -l 2>/dev/null; echo '0 2 * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py ingest_who >> /home/ifrc/logs/ingest_who.log 2>&1') | crontab -
(crontab -l 2>/dev/null; echo '*/5 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py index_and_notify >> /home/ifrc/logs/index_and_notify.log 2>&1') | crontab -
(crontab -l 2>/dev/null; echo '10 2 * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py scrape_pdfs >> /home/ifrc/logs/scrape_pdfs.log 2>&1') | crontab -
(crontab -l 2>/dev/null; echo '30 1 * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py ingest_databank >> /home/ifrc/logs/ingest_databank.log 2>&1') | crontab -
if [ "$API_FQDN"x = dsgocdnapi.azureedge.netx ]; then  # only staging
    (crontab -l 2>/dev/null; echo '*/5 * * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py sync_molnix >> /home/ifrc/logs/sync_molnix.log 2>&1') | crontab -
fi
(crontab -l 2>/dev/null; echo '* */6 * * * . /home/ifrc/.env; python /home/ifrc/go-api/manage.py update_project_status >> /home/ifrc/logs/update_project_status.log 2>&1') | crontab -
service cron start

tail -n 0 -f $HOME/logs/*.log &

echo Starting nginx
exec nginx -g 'daemon off;'

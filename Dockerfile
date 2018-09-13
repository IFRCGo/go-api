FROM python:3.6.3-jessie

EXPOSE 80
EXPOSE 443

RUN \
	apt-get update; \
	apt-get install -y nginx postgresql-client mdbtools vim; \
	apt-get install -y cron --no-install-recommends

ENV HOME=/home/ifrc
WORKDIR $HOME

COPY requirements.txt $HOME/requirements.txt
RUN \
	pip install gunicorn; \
	pip install -r requirements.txt

COPY main/nginx.conf /etc/nginx/sites-available/
RUN \
	ln -s /etc/nginx/sites-available/nginx.conf /etc/nginx/sites-enabled; \
	>> /etc/nginx/nginx.conf

COPY main/runserver.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/runserver.sh

COPY ./ $HOME/go-api/
WORKDIR $HOME/go-api/

RUN \
      cd /usr/local/lib/python*/site-packages/django/contrib/admin/ ; \
      patch < /home/ifrc/go-api/main/sites_patch

ENTRYPOINT ["./main/entrypoint.sh"]

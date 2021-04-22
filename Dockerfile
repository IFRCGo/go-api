FROM python:3.6.11-buster

EXPOSE 80
EXPOSE 443

RUN \
	apt-get update && \
	apt-get install -y nginx postgresql-client mdbtools vim tidy less gettext && \
	apt-get install -y cron --no-install-recommends && \
	apt-get install -y binutils libproj-dev gdal-bin

ENV HOME=/home/ifrc
WORKDIR $HOME

COPY requirements.txt $HOME/requirements.txt
RUN \
	pip install gunicorn; \
	pip install -r requirements.txt; \
	pip install mapbox-tilesets

COPY main/nginx.conf /etc/nginx/sites-available/
RUN \
	ln -s /etc/nginx/sites-available/nginx.conf /etc/nginx/sites-enabled; \
	>> /etc/nginx/nginx.conf

COPY main/runserver.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/runserver.sh

COPY ./ $HOME/go-api/
WORKDIR $HOME/go-api/

ENTRYPOINT ["./main/entrypoint.sh"]

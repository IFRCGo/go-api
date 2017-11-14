FROM python:3.6.3-jessie

RUN \
	apt-get update; \
	apt-get install -y nginx postgresql-client mdbtools


ENV HOME=/home/ifrc

WORKDIR $HOME

COPY requirements.txt $HOME/requirements.txt
RUN \
	pip install gunicorn; \
	pip install -r requirements.txt

COPY main/nginx.conf /etc/nginx/sites-available/
RUN \
	ln -s /etc/nginx/sites-available/nginx.conf /etc/nginx/sites-enabled; \
	echo "daemon off;" >> /etc/nginx/nginx.conf

COPY main/runserver.sh /usr/local/bin/

COPY \
	./ $HOME/go-api/

WORKDIR $HOME/go-api/

EXPOSE 80
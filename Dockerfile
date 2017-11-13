FROM python:3.6.3-jessie

ENV HOME=/home/ifrc

WORKDIR $HOME

COPY \
	requirements.txt $HOME/requirements.txt

RUN \
	pip install -r requirements.txt

COPY \
	./ $HOME/go-api/

WORKDIR $HOME/go-api/

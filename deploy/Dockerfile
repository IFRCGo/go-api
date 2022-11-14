FROM hashicorp/terraform:latest

RUN apk update
RUN apk add wget unzip curl \
    py3-pip \
    build-base python3-dev \
    linux-headers \
    bash

# Upgrade pip
RUN pip3 install -U pip

# Install azure client
RUN pip3 install azure-cli

WORKDIR /opt/src
ENTRYPOINT []
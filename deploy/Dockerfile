FROM hashicorp/terraform:1.6.5

RUN apk update
RUN apk add wget unzip curl \
    py3-pip \
    build-base python3-dev \
    linux-headers \
    bash \
    helm

# Upgrade pip
RUN pip3 install -U pip

# Install azure client
RUN pip3 install azure-cli
RUN echo 'burst docker cache'

WORKDIR /opt/src
ENTRYPOINT []

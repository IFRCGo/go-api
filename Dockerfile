FROM python:3.11-bullseye
COPY --from=ghcr.io/astral-sh/uv:0.6.2 /uv /uvx /bin/

LABEL maintainer="GO Dev <go-dev@ifrc.org>"
LABEL org.opencontainers.image.source="https://github.com/IFRCGo/go-api"

ENV PYTHONUNBUFFERED=1

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
ENV UV_CACHE_DIR="/root/.cache/uv"

EXPOSE 80
EXPOSE 443

# Microsoft repo for Debian 11 (bullseye) + ODBC Driver 18
RUN set -eux; \
    apt-get update -y; \
    apt-get install -y --no-install-recommends \
      curl ca-certificates gnupg apt-transport-https; \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
      | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg; \
    ARCH="$(dpkg --print-architecture)"; \
    echo "deb [arch=${ARCH} signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" \
      > /etc/apt/sources.list.d/microsoft-prod.list; \
    apt-get update -y; \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
      nginx mdbtools vim tidy less gettext \
        cron \
        wait-for-it \
      openjdk-17-jre-headless \
        binutils libproj-dev gdal-bin poppler-utils \
        unixodbc unixodbc-dev msodbcsql18 \
      openjdk-11-jre-headless \
        libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libxcb-dri3-0 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxinerama1 libxrandr2 libxrender1 libxss1 libxtst6 libgbm1 libasound2 libxslt1.1; \
    apt-get autoremove -y; \
    rm -rf /var/lib/apt/lists/*

  ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

ENV HOME=/home/ifrc
WORKDIR $HOME

# Upgrade pip and install python packages for code
RUN --mount=type=cache,target=$UV_CACHE_DIR \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --all-groups

# pyspark is installed via pyproject.toml during `uv sync`

# Refresh apt metadata and preinstall the package that previously failed in CI.
RUN apt-get update -o Acquire::Retries=3 \
  && apt-get install -y --fix-missing libopenmpt0


# To avoid some SyntaxWarnings ("is" with a literal), still needed on 20241024:
ENV AZUREROOT=/usr/local/lib/python3.11/site-packages/azure/storage/
RUN perl -pi -e 's/ is 0 / == 0 /'      ${AZUREROOT}blob/_upload_chunking.py
RUN perl -pi -e 's/ is not -1 / != 1 /' ${AZUREROOT}blob/baseblobservice.py
RUN perl -pi -e "s/ is '' / == '' /"    ${AZUREROOT}common/_connection.py
RUN perl -pi -e "s/ is '' / == '' /"    ${AZUREROOT}_connection.py

# Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# To avoid dump of "Queue is full. Dropping telemetry." messages in log, 20241111:
ENV OPENCENSUSINIT=/usr/local/lib/python3.11/site-packages/opencensus/common/schedule/__init__.py
RUN perl -pi -e "s/logger.warning.*/pass/" ${OPENCENSUSINIT} 2>/dev/null

# To avoid 'NoneType' object has no attribute 'get' in clickjacking.py, 20250305:
ENV CLICKJACKING=/usr/local/lib/python3.11/site-packages/django/middleware/clickjacking.py
RUN perl -pi -e "s/if response.get/if response is None:\n            return\n\n        if response.get/" ${CLICKJACKING} 2>/dev/null

COPY main/nginx.conf /etc/nginx/sites-available/
RUN \
  ln -s /etc/nginx/sites-available/nginx.conf /etc/nginx/sites-enabled; \
  >> /etc/nginx/nginx.conf

COPY main/runserver.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/runserver.sh

COPY ./ $HOME/go-api/
WORKDIR $HOME/go-api/

ENTRYPOINT ["./main/entrypoint.sh"]

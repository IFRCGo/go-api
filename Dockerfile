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

# Microsoft repo for Debian 11 (bullseye) + ODBC Driver 18 + Azure CLI
RUN set -eux; \
    apt-get update -y; \
    apt-get install -y --no-install-recommends \
      curl ca-certificates gnupg apt-transport-https; \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
      | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg; \
    ARCH="$(dpkg --print-architecture)"; \
    echo "deb [arch=${ARCH} signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" \
      > /etc/apt/sources.list.d/microsoft-prod.list; \
    echo "deb [arch=${ARCH} signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/repos/azure-cli/ bullseye main" \
      > /etc/apt/sources.list.d/azure-cli.list; \
    apt-get update -y; \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
      nginx mdbtools vim tidy less gettext \
        cron \
        wait-for-it \
      openjdk-11-jre-headless \
        libpostgresql-jdbc-java \
        binutils libproj-dev gdal-bin poppler-utils \
        unixodbc unixodbc-dev msodbcsql18 \
        libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libxcb-dri3-0 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxinerama1 libxrandr2 libxrender1 libxss1 libxtst6 libgbm1 libasound2 libxslt1.1 \
        libopenmpt0 \
        azure-cli; \
    rm -rf /var/lib/apt/lists/*

# Ensure JAVA_HOME is available regardless of architecture variant.
# Some Debian/Ubuntu packages install architecture-specific JVM directories
RUN set -eux; \
    if [ -d /usr/lib/jvm ]; then \
      JAVA_DIR=$(ls -1 /usr/lib/jvm | grep -E 'java-11-openjdk|openjdk-11' | head -n1 || true); \
      if [ -n "${JAVA_DIR}" ]; then \
        if [ ! -e /usr/lib/jvm/java-11-openjdk-amd64 ]; then \
          ln -s "/usr/lib/jvm/${JAVA_DIR}" /usr/lib/jvm/java-11-openjdk-amd64 || true; \
        fi; \
      fi; \
    fi

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV HOME=/home/ifrc
WORKDIR $HOME

# pyspark is installed via pyproject.toml during `uv sync`
RUN --mount=type=cache,target=$UV_CACHE_DIR \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --all-groups

# Patch installed packages to fix known issues
RUN set -eux; \
    AZUREROOT=/usr/local/lib/python3.11/site-packages/azure/storage/; \
    perl -pi -e 's/ is 0 / == 0 /'      ${AZUREROOT}blob/_upload_chunking.py; \
    perl -pi -e 's/ is not -1 / != 1 /' ${AZUREROOT}blob/baseblobservice.py; \
    perl -pi -e "s/ is '' / == '' /"    ${AZUREROOT}common/_connection.py; \
    perl -pi -e "s/ is '' / == '' /"    ${AZUREROOT}_connection.py; \
    OPENCENSUSINIT=/usr/local/lib/python3.11/site-packages/opencensus/common/schedule/__init__.py; \
    perl -pi -e "s/logger.warning.*/pass/" ${OPENCENSUSINIT} 2>/dev/null; \
    CLICKJACKING=/usr/local/lib/python3.11/site-packages/django/middleware/clickjacking.py; \
    perl -pi -e "s/if response.get/if response is None:\n            return\n\n        if response.get/" ${CLICKJACKING} 2>/dev/null

COPY main/nginx.conf /etc/nginx/sites-available/
RUN ln -s /etc/nginx/sites-available/nginx.conf /etc/nginx/sites-enabled

COPY main/runserver.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/runserver.sh

COPY ./ $HOME/go-api/
WORKDIR $HOME/go-api/

ENTRYPOINT ["./main/entrypoint.sh"]

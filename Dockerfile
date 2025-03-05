FROM python:3.11-bullseye

LABEL org.opencontainers.image.source="https://github.com/IFRCGo/go-api"

ENV PYTHONUNBUFFERED=1
EXPOSE 80
EXPOSE 443

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        # FIXME: Make sure all packages are used/required
        nginx mdbtools vim tidy less gettext \
        cron \
        wait-for-it \
        binutils libproj-dev gdal-bin poppler-utils && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

ENV HOME=/home/ifrc
WORKDIR $HOME

COPY pyproject.toml poetry.lock $HOME/

# Upgrade pip and install python packages for code
RUN pip install --upgrade --no-cache-dir pip "poetry>=2.1,<2.2" \
    && poetry --version \
    # Configure to use system instead of virtualenvs
    && poetry config virtualenvs.create false \
    && poetry install --no-root \
    && poetry add playwright \
    # Clean-up
    && pip uninstall -y poetry virtualenv-clone virtualenv

RUN playwright install \
    && playwright install-deps

# To avoid some SyntaxWarnings ("is" with a literal), still needed on 20241024:
ENV AZUREROOT=/usr/local/lib/python3.11/site-packages/azure/storage/
RUN perl -pi -e 's/ is 0 / == 0 /'      ${AZUREROOT}blob/_upload_chunking.py
RUN perl -pi -e 's/ is not -1 / != 1 /' ${AZUREROOT}blob/baseblobservice.py
RUN perl -pi -e "s/ is '' / == '' /"    ${AZUREROOT}common/_connection.py
RUN perl -pi -e "s/ is '' / == '' /"    ${AZUREROOT}_connection.py

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

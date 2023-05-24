FROM python:3.8.12-buster

ENV PYTHONUNBUFFERED 1
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
RUN pip install --upgrade --no-cache-dir pip poetry \
    && poetry --version \
    # Configure to use system instead of virtualenvs
    && poetry config virtualenvs.create false \
    && poetry install --no-root \
    # Clean-up
    && pip uninstall -y poetry virtualenv-clone virtualenv

# TODO: Refactor the whole Azure storage part. (Upgrade is not enough, was tested.)
# Until then avoid some SyntaxWarnings ("is" with a literal):
ENV AZUREROOT=/usr/local/lib/python3.8/site-packages/azure/storage/
RUN perl -pi -e 's/ is 0 / == 0 /'      ${AZUREROOT}blob/_upload_chunking.py
RUN perl -pi -e 's/ is not -1 / != 1 /' ${AZUREROOT}blob/baseblobservice.py
RUN perl -pi -e "s/ is '' / == '' /"    ${AZUREROOT}common/_connection.py
RUN perl -pi -e "s/ is '' / == '' /"    ${AZUREROOT}_connection.py

COPY main/nginx.conf /etc/nginx/sites-available/
RUN \
	ln -s /etc/nginx/sites-available/nginx.conf /etc/nginx/sites-enabled; \
	>> /etc/nginx/nginx.conf

COPY main/k8s_runserver.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/runserver.sh

COPY ./ $HOME/go-api/
WORKDIR $HOME/go-api/

ENTRYPOINT ["./main/entrypoint.sh"]

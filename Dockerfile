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

COPY main/nginx.conf /etc/nginx/sites-available/
RUN \
	ln -s /etc/nginx/sites-available/nginx.conf /etc/nginx/sites-enabled; \
	>> /etc/nginx/nginx.conf

COPY main/k8s_runserver.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/k8s_runserver.sh

COPY ./ $HOME/go-api/
WORKDIR $HOME/go-api/

ENTRYPOINT ["./main/entrypoint.sh"]

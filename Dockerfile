FROM python:3.11-bullseye

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
RUN pip install --upgrade --no-cache-dir pip poetry \
    && poetry --version \
    # Configure to use system instead of virtualenvs
    && poetry config virtualenvs.create false \
    && poetry install --no-root \
    && poetry add playwright \
    # Clean-up
    && pip uninstall -y poetry virtualenv-clone virtualenv

RUN playwright install \
    && playwright install-deps

COPY main/nginx.conf /etc/nginx/sites-available/
RUN \
	ln -s /etc/nginx/sites-available/nginx.conf /etc/nginx/sites-enabled; \
	>> /etc/nginx/nginx.conf

COPY main/runserver.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/runserver.sh

COPY ./ $HOME/go-api/
WORKDIR $HOME/go-api/

ENTRYPOINT ["./main/entrypoint.sh"]

[![Waffle.io - Columns and their card count](https://badge.waffle.io/IFRCGo/go-infrastructure.svg?columns=all)](https://waffle.io/IFRCGo/go-infrastructure)

[![CircleCI](https://circleci.com/gh/IFRCGo/go-api.svg?style=svg&circle-token=4337c3da24907bbcb5d6aa06f0d60c5f27845435)](https://circleci.com/gh/IFRCGo/go-api)

# IFRC GO API

## Staff email domains

A list of staff email domains, which the API will treat as single-validation, email-verification only, is to be found [here](https://github.com/IFRCGo/go-api/blob/develop/registrations/views.py#L24).

## Requirements

- [Pyenv](https://github.com/pyenv/pyenv)
- Python 3.6.3 `pyenv install 3.6.3`
- [mdb tools](https://github.com/brianb/mdbtools) `brew install mdbtools`

## Running the Docker image locally

Check [Docker Hub](https://hub.docker.com/r/ifrcgo/go-api/tags/) for the latest tag.

```(bash)
docker run -p 80:80 --env-file .env -d -t ifrc/go-api:{TAG_NUMBER}
```

To specify a command on a running image:

```(bash)
docker ps
# CONTAINER ID        IMAGE               COMMAND                   CREATED             STATUS              PORTS                NAMES
# d0e64afa84b5        ifrc/go-api:16      "/bin/sh -c \"/usr/lo…"   22 minutes ago      Up 22 minutes       0.0.0.0:80->80/tcp   focused_allen
docker exec -it d0e64afa84b5 python manage.py ingest_appeals
```

## Setup

Start the environment and install the dependencies

```(bash)
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Developing against a local sqlite db

```(bash)
# Add FTP credentials to environment
source .env
# echo $GO_FTPPASS

# Tells django to use a local sqlite db
export LOCAL_TEST=true

python manage.py makemigrations
python manage.py migrate
python manage.py loaddata Actions Countries DisasterTypes
python manage.py collectstatic

# Disables automated elasticsearch indexing
export BULK_IMPORT = 1
python manage.py ingest_mdb
python manage.py ingest_appeals
python manage.py create_events

# Re-enable indexing to elasticsearch
export BULK_IMPORT = 0
python manage.py runserver
```

# Testing

## Run tests

```(bash)
python manage.py test
```

## Generate coverage report

```(bash)
coverage run --source='.' manage.py test
coverage report
```

# Continuous Integration

[Circle-ci handles continuous integration](https://circleci.com/gh/IFRCGo/go-api).

Pushes to `develop` will run the test suite against a test db.

Pushes to `master` will create a new git tag, using the `version` value in `main/__init__.py`, and build and deploy a new Docker image to the IFRC Docker Hub account. The build will fail if the version already has a tag, so you must increment the version number in `main/__init__.py` before merging to `master`.

# Deployment

`main/runserver.sh` is the entrypoint for deploying this API to a new environment. It is also the default command specified in `Dockerfile`. `main/runserver.sh` requires that environment variables corresponding to database connection strings, FTP settings, and email settings, among others, be set. Check the script for the specific variables in your environment.

## Deployment command

```(bash)
docker run -p 80:80 --env-file .env -d -t ifrc/go-api:{TAG_NUMBER}
```

[![Waffle.io - Columns and their card count](https://badge.waffle.io/IFRCGo/go-infrastructure.svg?columns=all)](https://waffle.io/IFRCGo/go-infrastructure)

[![CircleCI](https://circleci.com/gh/IFRCGo/go-api.svg?style=svg&circle-token=4337c3da24907bbcb5d6aa06f0d60c5f27845435)](https://circleci.com/gh/IFRCGo/go-api)

# IFRC GO API

## Requirements

- [Pyenv](https://github.com/pyenv/pyenv)
- Python 3.6.3 `pyenv install 3.6.3`

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
python manage.py loaddata Countries DisasterTypes
python manage.py collectstatic
python manage.py ingest_mdb
python manage.py runserver
```

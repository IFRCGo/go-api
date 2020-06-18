[![Waffle.io - Columns and their card count](https://badge.waffle.io/IFRCGo/go-infrastructure.svg?columns=all)](https://waffle.io/IFRCGo/go-infrastructure)

[![CircleCI](https://circleci.com/gh/IFRCGo/go-api.svg?style=svg&circle-token=4337c3da24907bbcb5d6aa06f0d60c5f27845435)](https://circleci.com/gh/IFRCGo/go-api)

# IFRC GO API

## Staff email domains

A list of staff email domains, which the API will treat as single-validation, email-verification only, is to be found [here](https://github.com/IFRCGo/go-api/blob/master/registrations/views.py#L25).

## Requirements

- docker and docker-compose

## Local Development

### Setup

     $ docker-compose build
     $ docker-compose run --rm migrate
     $ docker-compose run --rm loaddata 

### Running tests

     $ docker-compose run --rm test

### Making new migrations

     $ docker-compose run --rm makemigrations

### If there are conflicting migrations (only works if the migrations don't modify the same models)

     $ docker-compose run --rm makemigrations_merge

### Applying the last migration files to database

     $ docker-compose run --rm migrate

### Accessing python shell 

     $ docker-compose run --rm shell 

### Adding super user

     $ docker-compose run --rm createsuperuser

### Running server

     $ docker-compose run --rm --service-ports serve
    
Access the site at http://localhost:8000

### Install new dependencies

     $ docker-compose build


## Adding/Updating translations (Django)
```bash
# Creation and upkeep language po files (for eg: fr)
python3 manage.py makemessages -l fr
# Creation and upkeep language po files (for eg: multiple languages)
python3 manage.py makemessages -l en -l es -l ar -l fr
# Updating currnet language po files
python3 manage.py makemessages -a
# Translate empty string of po files using AWS Translate (Requires valid AWS_TRANSLATE_* env variables)
python3 manage.py translate_po
# Compile po files
python3 manage.py compilemessages
```

## Note for Django Model translations
```
# Use this to copy the data from original field to it's default lanauage.
# For eg: if the field `name` is registred for translation then
# this command will copy value from `name` to `name_en` if en is the default language.
python manage.py update_translation_fields

# Auto translate values from default lang to other language
python manage.py translate_model
```

## Generate coverage report

     $ docker-compose run --rm coverage

# Continuous Integration

[Circle-ci](https://circleci.com/gh/IFRCGo/go-api) handles continuous integration.

## Release to Docker Hub

To release a new version to docker hub do the following:

- Update `version` value in `main/__init__.py`
- Create a new git tag with the same version
- Commit and make a PR against master
- The tagged version of the code is used to build a new docker image and is pushed to docker hub

# Deployment

`main/runserver.sh` is the entrypoint for deploying this API to a new environment. It is also the default command specified in `Dockerfile`. `main/runserver.sh` requires that environment variables corresponding to database connection strings, FTP settings, and email settings, among others, be set. Check the script for the specific variables in your environment.

## Deployment command

```(bash)
docker run -p 80:80 --env-file .env -d -t ifrcgo/go-api:{TAG_NUMBER}
```

## Comment for loading data

In `main/runserver.sh` the line containing the `loaddata` command is only necessary when creating a new database. In other cases it might be causing the conflict, so it is commented.

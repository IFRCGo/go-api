[![Waffle.io - Columns and their card count](https://badge.waffle.io/IFRCGo/go-infrastructure.svg?columns=all)](https://waffle.io/IFRCGo/go-infrastructure)

[![CircleCI](https://circleci.com/gh/IFRCGo/go-api.svg?style=svg&circle-token=4337c3da24907bbcb5d6aa06f0d60c5f27845435)](https://circleci.com/gh/IFRCGo/go-api)

# IFRC GO API

## Staff email domains

A list of staff email domains, which the API will treat as single-validation, email-verification only, is to be found [here](https://github.com/IFRCGo/go-api/blob/develop/registrations/views.py#L24).

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

     $ docker-compose run --rm migrate

### Making new migrations

     $ docker-compose run --rm makemigrations
    

### Accessing python shell 

     $ docker-compose run --rm shell 

### Adding super user

     $ docker-compose run --rm createsuperuser

### Running server

     $ docker-compose run --rm --service-ports serve
    
Access the site at http://localhost:8000

### Install new dependencies

     $ docker-compose build


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

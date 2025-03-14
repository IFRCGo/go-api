[![Waffle.io - Columns and their card count](https://badge.waffle.io/IFRCGo/go-infrastructure.svg?columns=all)](https://waffle.io/IFRCGo/go-infrastructure)

[![CircleCI](https://circleci.com/gh/IFRCGo/go-api.svg?style=svg&circle-token=4337c3da24907bbcb5d6aa06f0d60c5f27845435)](https://circleci.com/gh/IFRCGo/go-api)

# IFRC GO API

## Staff email domains

A list of staff email domains, which the API will treat as single-validation,
email-verification only, is to be found
[here](https://github.com/IFRCGo/go-api/blob/master/registrations/views.py#L25).

## Requirements

-   docker and docker-compose

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

     $ docker-compose up serve celery
     $ (To attach to a container with stdin, e.g. for debugging: docker attach <container_name>)
     $ (Or, without celery, the old pdb-friendly way: docker-compose run --rm --service-ports serve)

Access the site at http://localhost:8000

### Install new dependencies

     $ docker-compose build

### Using [uv](https://docs.astral.sh/uv/) (python package manager)
- Install uv using this documentation https://docs.astral.sh/uv/getting-started/installation/
- Sync packages using uv
    ```bash
    uv sync
    ```
- Add new package in pyproject.toml and generate lock
    ```bash
    uv lock
    ```

## Adding/Updating translations (Django static)

```bash
# Creation and upkeep language po files (for eg: fr)
python3 manage.py makemessages -l fr
# Creation and upkeep language po files (for eg: multiple languages)
python3 manage.py makemessages -l en -l es -l ar -l fr
# Updating current language po files
python3 manage.py makemessages -a
# Translate empty string of po files using AWS Translate (Requires valid AWS_TRANSLATE_* env variables)
python3 manage.py translate_po
# Compile po files
python3 manage.py compilemessages

# Import/Export django static translation
python3 manage.py static-translation-export path-to-export.csv
# For specific languages or only new(empty) strings.
python3 manage.py static-translation-export path-to-export.csv --only-new --languages en es
python3 manage.py static-translation-import path-to-import.csv
```

## Note for Django Model translations

```
# Use this to copy the data from original field to it's default language.
# For eg: if the field `name` is registred for translation then
# this command will copy value from `name` to `name_en` if en is the default language.
python manage.py update_translation_fields

# Auto translate values from default lang to other language – to be used in the future (AWS Translate)
python manage.py translate_model
```

## Generate coverage report

     $ docker-compose run --rm coverage

## Testing

Please read [TESTING.md](./TESTING.md) for guidance on writing and executing tests.

## Documentation

Identify the function/class to modify from [main/urls.py](main/urls.py).

### Add function descriptions

Use [docstrings](https://www.python.org/dev/peps/pep-0257/) to add action
specific descriptions,

```
class CustomViewset(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Description for list action of Custom.

    read:
    Description for read action of Custom.
    """
```

### Add field descriptions

Look for the **field** definition in the `CustomViewset` class or its attributes
like `CustomFilter`.

Add `help_text` attribute to the field definition.

```
variable_name = filters.NumberFilter(field_name='variable name', lookup_expr='exact', help_text='Description string for variable name.')
```

Django automatically generates description strings for **standard** fields like
`id` or `ordering`.

# Continuous Integration

[Circle-ci](https://circleci.com/gh/IFRCGo/go-api) handles continuous
integration.

## Release to Docker Hub

To release a new version to docker hub do the following:

-   Update `version` value in `main/__init__.py`
-   Create a new git tag with the same version
-   Commit and make a PR against master
-   The tagged version of the code is used to build a new docker image and is
    pushed to docker hub

# Deployment

`main/runserver.sh` is the entrypoint for deploying this API to a new
environment. It is also the default command specified in `Dockerfile`.
`main/runserver.sh` requires that environment variables corresponding to
database connection strings, FTP settings, and email settings, among others, be
set. Check the script for the specific variables in your environment.

## Deployment command

```(bash)
docker-compose up serve celery
```
or (just the base serve command):
```(bash)
docker-compose run --rm --service-ports serve
```
## Comment for loading data

In `main/runserver.sh` the line containing the `loaddata` command is only necessary when creating a new database. In other cases it might be causing the conflict, so it is commented. 

## Initializing ElasticSearch

For the initial creation of an index
```(bash)
docker-compose exec serve bash python manage.py rebuild_index
```
For updating the index
```(bash)
docker-compose exec serve bash python manage.py update_index
```
## Sentry

For updating the cron monitored tasks
```(bash)
docker-compose exec serve bash ./manage.py cron_job_monitor
```

## See logs from Kubernetes
There are a few different ways to see logs in the new Kubernetes based stack. Both of the options require `kubectl`, access to the cluster. Once the cluster is added to your local kubernetes context, follow the steps below:

### 1. Using Grafana
Grafana is an open source log analytics software. We use [Grafana along with Loki](https://grafana.com/docs/loki/latest/installation/helm/) to interactively fetch logs, run custom queries and analysis. To access the Grafana dashboard and view logs:
1. Proxy the Grafana server to you localhost: `kubectl port-forward --namespace loki-stack service/loki-stack-grafana 3000:80`
2. Now visit http://localhost:3000 to see the login page
3. Get the password using `kubectl get secret --namespace loki-stack loki-stack-grafana -o jsonpath="{.data.admin-password}" | base64 -d ; echo`. The username is `admin`
4. Now go to the Dashboard > Logs. Currently we have added API and Elastic Search logs ![image](https://github.com/developmentseed/ds-business/assets/371666/b8cd96a9-dd97-4cad-8574-c03697c8b5d5)
5. If you want to run custom queries, use the Explore tab.

### 2. Using kubectl
Using `kubectl` is a more direct way to looking at logs. Once you find the pod name (using `kubectl get pods`), run `kubectl logs podname`.

# Management commands to update and import admin0 and admin1 data

There are two Django management commands that helps to work with ICRC admin0 and admin1 shapefiles. These commands should be used only when you want to update geometries, or import new ones from a shapefile. The structure of the shapefile is not very flexible, but can be adjusted easily in the scripts. 

## import-admin0-data
This management command is used for updating and importing admin0 shapefile. To run:
* `python manage.py import-admin0-data <filename.shp>`

The above command will generate a list of missing countries in the database based on the iso2 code to a file called `missing-countries.txt`. In case the script comes across any countries with duplicate iso code, these will be stored in `duplicate-countries.txt`

### Options available for the command
* `--update-geom` -- updates the geometry for all countries matched in the shapefile using the iso2 code.
* `--update-bbox` -- updates the bbox for all countries matched in the shapefile using the iso2 code.
* `--update-centroid` -- updates the centroid for all countries from a CSV. The CSV should have iso code, latitude and longitude. If a country is missing in the CSV, the geometric centroid will be used.
* `--import-missing missing-countries.txt` -- this will import countries for the iso2 mentioned in `missing-countries.txt` to the database. The file is the same format as generated by the default command.
* `--update-iso3 iso3.csv` -- this will import iso3 codes for all countries from a csv file. The file should have `iso2, iso3` columns.
* `--update-independent` -- updates the independence status for the country from the shapefile.

## import-admin1-data
This management command is used for updating and importing admin1 shapefile. To run:
* `python manage.py import-admin1-data <filename.shp>`

The above command will generate a list of missing districts in the database based on the district code and name (in case there are more than one district with the same code) to a file called `missing-district.txt`

### Options available for the command
* `--update-geom` -- updates the geometry for all districts matched in the shapefile using the iso2 code.
* `--update-bbox` -- updates the bbox for all districts matched in the shapefile using the iso2 code.
* `--update-centroid` -- updates the centroid for all districts matched in the shapefile using the iso2 code.
* `--import-missing missing-districts.txt` -- this will import districts for the iso2 mentioned in `missing-districts.txt` to the database. The file is the same format as generated by the default command.
* `--import-all` -- this option is used to import all districts in the shapefile, if they don't have a code we can match against in the database.

## import-admin2-data
This management command is used for updating and importing admin2 shapefile. To run:
* `python manage.py import-admin2-data <filename.shp>`

The shapefile should have the following mandatory fields:
* name or shapeName
* code or pcode
* admin1_id (this is the ID of the GO district this admin2 belongs to)

See [this ticket](https://github.com/IFRCGo/go-api/issues/1492#issuecomment-1284120696) for a full workflow of preparing the admin2 shapefiles.
The above command will generate a list of missing admin2-s in the database based on the code (we use pcodes) to a file called `missing-admin2.txt`

### Options available for the command
* `--update-geom` -- updates the geometry for all admin2 matched in the shapefile.
* `--import-missing missing-admin2.txt` -- this will import admin2 listed in `missing-admin2.txt` to the database. The file is the same format as generated by the default command.
* `--import-all` -- this option is used to import all admin2 in the shapefile.


## Update bbox for regions
Run `python manage.py update-region-bbox` to update the bbox for each region in the database.

## Import FDRS codes
Run `python manage.py import-fdrs iso-fdrs.csv` to update the countries table with FDRS codes. The csv should have `iso, fdrs` structure

## Update sovereign state and disputed status
Run ` python manage.py update-sovereign-and-disputed new_fields.csv` to update the countries table with sovereign states and disputed status. The CSV should have the `id,iso,name,sovereign_state,disputed` columns. The matching is based on iso and name. If iso is null, we fall back to name.

## Update Mapbox Tilesets
To update GO countries and districts Mapbox tilesets, run the management command `python manage.py update-mapbox-tilesets`. This will export all country and district geometries to a GeoJSON file, and then upload them to Mapbox. The tilesets will take a while to process. The updated status can be viewed on the Mapbox Studio under tilesets. To run this management command, MAPBOX_ACCESS_TOKEN should be set in the environment. The referred files are in ./mapbox/..., so you should **not** run this command from an arbitrary point of the vm's filesystem (e.g. from the location of shapefiles), but from Django root.

### Options available for the command
* `--production` — update production tilesets. If this flag is not set, by default the script will only update staging tiles
* `--update-countries` — update tileset for countries, including labels
* `--update-districts` — update tileset for districts, including labels
* `--update-all` — update all countries and districts tilesets
* `--create-and-update-admin2 <ISO3>` — if a new admin2 tileset should be created, use this argument. It will create a new source on Mapbox and then register a tileset. Ensure that recipes are create in `mapbox/admin2/` directory. For example, see `mapbox/admin2/COL.json` and `mapbox/admin2/COL-centroids.json`. A recipe for polygons and centroids are required. For centroids, we don't need to create a staging recipe.  To run `python manage.py update-mapbox-tilesets --create-and-update-admin2 COL`
* `--update-admin2 <ISO3>` — use this to update an existing admin2 tileset. For example, `python manage.py update-mapbox-tilesets --update-admin2 COL`

## Import GEC codes
To import GEC codes along with country ids, run `python manage.py import-gec-code appeal_ingest_match.csv`. The CSV should have the columns `'GST_code', 'GST_name', 'GO ID', 'ISO'`

## SSO setup

For more info checkout [GO-SSO](./docs/go-sso.md)

## Playwright exports

For more info checkout [Playwright exports](./docs/playwright-exports.md)

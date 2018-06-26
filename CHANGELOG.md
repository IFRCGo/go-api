# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- Logging to Azure Queue storage.
- A cron job to detet changes to field reports, events, and appeals, and index them to elasticsearch/notify subscribers.
- Add a CSV renderer so data can be exported as CSV for any model.
- Include filtering class for situation report and appeal documents.
- Include report date, updated at timestamp in field report response.
- Include search fields for all relevant admin forms.
- Include alert sorting and ordering.

### Changed

- Changed elasticsearch indexes to use one table.
- Upgraded elasticsearch query to match terms, rather than prefix.
- Made the district deployed to in partner deployments a many-to-many field.

### Removed

- Post-save triggers for indexing models to elasticsearch and notifying subscribers.

## 1.0.1

### Added

- Adds a partner society deployment type table
- Attaches event representation to field reports
- Attaches mini field report representation to events
- Fixes event admin search field
- Improvements to the emergency admin page.
- Field report DMIS ingest automatically creates new emergency objects.
- Key figures, contacts, links, and embed models to country and region pages.
- Create endpoints for key figures and embeds that respond to private/public setting.
- Appeals and field report admins can create new emergency objects that automatically get attached as relations.
- Newly ingested appeals will now try to guess at an emergency that it might belong to.
- If a newly ingested appeal is attached, a needs_confirmation flag will ensure it does not show up in API responses.
- Creates routes and relations for a district, essentially sub-country admin level.
- Creates a new type of deployment, a national partner deployment.

### Changed

- Uses autocomplete fields for events, countries in admin.
- Altered the emergency key figure model to use a text type, ie "15%."
- Appeals now order by start date, not end date.
- Events now have a column for where they were auto-generated from.

### Removed

- Removed event editable fields from appeal, field report list admin views.

## 1.0.0

### Added

- `api/v2` routes, powered by Django Rest Framework.
- Field report contact inline element to field report admin form.
- Updates core Django dependencies to recent versions, notably Django 1.11.8 > 2.0.5

### Changed

- Changed how docker-compose and docker is used for development and testing.

### Removed

- All Tastypie `api/v1` routes no longer function. The remaining `api/v1` routes for aggregates and elasticsearch queries will continue to function, but will soon be removed as well.

## 0.1.20

[Unreleased]: https://github.com/IFRCGo/go-api/compare/1.0.1...HEAD
[1.0.1]: https://github.com/IFRCGo/go-api/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/IFRCGo/go-api/compare/0.1.20...1.0.0
[0.1.20]: https://github.com/IFRCGo/go-api/compare/0.1.0...0.1.20

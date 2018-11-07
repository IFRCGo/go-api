# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

## 1.1.16

### Added
- Change default setting to non-'Public' when adding Situation Report (frontend#503)

### Added

## 1.1.15

### Added
- Autocomplete feature of events for Situation Reports (frontend#502)

### Added

## 1.1.14

### Added
- Autocomplete feature of personal deployments (frontend#492)
- Temporary stop of multiple Appeal email sending (#323)

### Added

## 1.1.13

### Fixed
- Bug where situation reports would only display public reports

## 1.1.12

### Added
- Possibility to hide attached field reports

## 1.1.11

### Added
- Type fixing in ingest_mdb and ingest_gdacs

## 1.1.7

### Added
- Richer CSV output, allowing case insensitive username for login/pwdChange

## 1.1.4

### Added
- Hiding inline add, edit and delete icons even from superusers (on admin)

## 1.1.2

### Added

- Increasing data-upload-max-memory-size
- Fixing frontend-url
- Making region optional (in countries admin form)

### Added

## 1.1.1

### Added

- Redirect http to https at Nginx level.
- Force https for new registration links.
- Add IFRC and ERU HR as new personnel types.
- Added the visibility class to situation reports.
- Fields for country overview, key priorities, and inform scores.

## 1.1.0

### Added

- Fields for country overview, key priorities, and inform scores.
- Change default Django admin site headers.
- Change deployments admin title to better reflect 3Ws.
- Hide emergencies key priorities field from admin pages.
- Deprecate separate deployment tables for HEOP, FACT, and RDRT in favor of single Personnel table.
- Include serializers, routes, and filters for Personnel, ERU tables.

### Changed

- Modified logging interval to 90 minutes.

## 1.0.2

### Added

- Log to blob storage every three hours.
- Modify send_notification script to omit email addressers from header.
- Add class to check for whether requesting user has IFRC role, attach it to relevant endpoints.
- New field reports, when created at the `api/v2/create_field_report` endpoint, will create an attached emergency if none is attached already.
- Add views to create, edit field reports.
- Create a separate API route for emergency snippets.
- Add an API path for viewing elasticsearch cluster health.
- Add a keyword field for appeal codes in ES that is heavily weighted.
- Add countries and regions to elasticsearch indexes.
- Add elasticsearch analyzer for autocomplete, apply it to body of generic page index.
- Default country and regional user group and permissions.
- A regionally restricted admin class to filter querysets depending on a user's permissions.
- Logging to Azure Queue storage.
- A cron job to detet changes to field reports, events, and appeals, and index them to elasticsearch/notify subscribers.
- Add a CSV renderer so data can be exported as CSV for any model.
- Include filtering class for situation report and appeal documents.
- Include report date, updated at timestamp in field report response.
- Include search fields for all relevant admin forms.
- Include API docs.
- Include alert sorting and ordering.

### Changed

- Changed region, country filter to list filters on field reports, events.
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

[Unreleased]: https://github.com/IFRCGo/go-api/compare/1.1.16...HEAD
[1.1.16]: https://github.com/IFRCGo/go-api/compare/1.1.15...1.1.16
[1.1.15]: https://github.com/IFRCGo/go-api/compare/1.1.14...1.1.15
[1.1.14]: https://github.com/IFRCGo/go-api/compare/1.1.13...1.1.14
[1.1.13]: https://github.com/IFRCGo/go-api/compare/1.1.12...1.1.13
[1.1.12]: https://github.com/IFRCGo/go-api/compare/1.1.11...1.1.12
[1.1.11]: https://github.com/IFRCGo/go-api/compare/1.1.10...1.1.11
[1.1.7]: https://github.com/IFRCGo/go-api/compare/1.1.6...1.1.7
[1.1.4]: https://github.com/IFRCGo/go-api/compare/1.1.3...1.1.4
[1.1.3]: https://github.com/IFRCGo/go-api/compare/1.1.2...1.1.3
[1.1.2]: https://github.com/IFRCGo/go-api/compare/1.1.1...1.1.2
[1.1.1]: https://github.com/IFRCGo/go-api/compare/1.1.0...1.1.1
[1.1.0]: https://github.com/IFRCGo/go-api/compare/1.0.2...1.1.0
[1.0.2]: https://github.com/IFRCGo/go-api/compare/1.0.1...1.0.2
[1.0.1]: https://github.com/IFRCGo/go-api/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/IFRCGo/go-api/compare/0.1.20...1.0.0
[0.1.20]: https://github.com/IFRCGo/go-api/compare/0.1.0...0.1.20

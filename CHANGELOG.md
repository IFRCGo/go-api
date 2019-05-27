# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Unreleased

## 1.1.80
## 1.1.79

### Added
 - Appealbilaterals API integration

## 1.1.78
## 1.1.77
## 1.1.76
## 1.1.75
## 1.1.74
## 1.1.73

### Added
 - New ingest_appeal_docs, including fullscan/3-months options

## 1.1.72
## 1.1.71
## 1.1.70
## 1.1.69

### Added
 - Country list for PER views
 - Permissions for PER views v1, v2
 - Filter formdata for country and region
 - NS data into form sending
 - Authentication to PER forms
 - PER permissions
 - New notification system – also events are listened to

## 1.1.68

### Added
 - gov_ numbers to provide in field reports

## 1.1.67

### Added
 - Tanzania to trusted domains

## 1.1.66
## 1.1.65

### Added
 - Event fields to be migrated from fieldreports

## 1.1.64
## 1.1.63

### Added
 - Multiple file upload – only for sit.rep admin page

## 1.1.62

### Added
 - Modules upgrading (mainly Azure storage)

## 1.1.61

### Added
 - Vulnerability upgrade

## 1.1.60
## 1.1.59
## 1.1.58
## 1.1.57
## 1.1.56

### Added
 - Multiple file upload

## 1.1.55
## 1.1.54
## 1.1.53
## 1.1.52
## 1.1.51
## 1.1.50

### Added
 - Unique_id not needed to PER form (just from KoBo form)
 - PER form data (and header) insertion via JSON POST
 - api.go.ifrc.org alias (prod)
 - Registration fix (admin_1/admin_2 for non-IFRC users)
 - Jinja upgrade

## 1.1.49
## 1.1.48

### Added
 - Wysiwyg HTML editing by tinyMCE4-lite

## 1.1.47
## 1.1.46

### Added
 - We need to expose updated_at for events - also in detailed

## 1.1.45

### Added
 - Some ERU figures should be shown on the home page

### Added

## 1.1.44
- ERU: accept more events

## 1.1.43
- Country name into field_report notification email
- Adding Austrian subdomains (e.g. s.roteskreuz.at) to domain list

## 1.1.42
- Featured event deployments count

## 1.1.41
- More explicit Delete button

## 1.1.40
- Adding cruzvermelha.org.pt to the trusted domain list. Verbose countries and regions.

## 1.1.39
- Adding Zambia (redcross.org.zm) to the trusted domain list.

## 1.1.38
## 1.1.37
## 1.1.36
## 1.1.35
## 1.1.34
## 1.1.33
## 1.1.32
## 1.1.31
## 1.1.30
## 1.1.29
## 1.1.28
## 1.1.27
## 1.1.26
## 1.1.25
## 1.1.24

### Added
- Adding positions to snippets, using for ordering on API side
- Upgrading Django due to a vulnerability
- Small version correction
- Bulk update of group memberships
- Database restoration and some exceptions to appeals ingest
- Showing real region_name and temporarily disabling field report notifications
- Field reports search issue fixed
- Increasing Django version to 2.0.10 due to security vulnerability
- Adding more Belgian domain names
- Converting country names for mdb ingestion

## 1.1.23
## 1.1.22

### Added
- A Read-only group for IFRC and Membership users and a script removing them from is_staff
- Adding rwandaredcross to valid domain list
- Upgrading urrllib3 with one version number

### Added

## 1.1.21

### Added
- Sending (only) username reminder

### Added

## 1.1.20
## 1.1.19

### Added
- Changing admin banner style
- Not allowing space into registered username

## 1.1.18
## 1.1.17
## 1.1.16

### Added
- Fixing email links to field reports
- Pointing with regions GEC_code to representing country, e.g. Africa regional office: Kenya
- Change default setting to Membership when adding Situation Report

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

[Unreleased]: https://github.com/IFRCGo/go-api/compare/1.1.80...HEAD
[1.1.80]: https://github.com/IFRCGo/go-api/compare/1.1.79...1.1.80
[1.1.79]: https://github.com/IFRCGo/go-api/compare/1.1.78...1.1.79
[1.1.78]: https://github.com/IFRCGo/go-api/compare/1.1.77...1.1.78
[1.1.77]: https://github.com/IFRCGo/go-api/compare/1.1.76...1.1.77
[1.1.76]: https://github.com/IFRCGo/go-api/compare/1.1.75...1.1.76
[1.1.75]: https://github.com/IFRCGo/go-api/compare/1.1.74...1.1.75
[1.1.74]: https://github.com/IFRCGo/go-api/compare/1.1.73...1.1.74
[1.1.73]: https://github.com/IFRCGo/go-api/compare/1.1.72...1.1.73
[1.1.72]: https://github.com/IFRCGo/go-api/compare/1.1.71...1.1.72
[1.1.71]: https://github.com/IFRCGo/go-api/compare/1.1.70...1.1.71
[1.1.70]: https://github.com/IFRCGo/go-api/compare/1.1.69...1.1.70
[1.1.69]: https://github.com/IFRCGo/go-api/compare/1.1.68...1.1.69
[1.1.68]: https://github.com/IFRCGo/go-api/compare/1.1.67...1.1.68
[1.1.67]: https://github.com/IFRCGo/go-api/compare/1.1.66...1.1.67
[1.1.66]: https://github.com/IFRCGo/go-api/compare/1.1.65...1.1.66
[1.1.65]: https://github.com/IFRCGo/go-api/compare/1.1.64...1.1.65
[1.1.64]: https://github.com/IFRCGo/go-api/compare/1.1.63...1.1.64
[1.1.63]: https://github.com/IFRCGo/go-api/compare/1.1.62...1.1.63
[1.1.62]: https://github.com/IFRCGo/go-api/compare/1.1.61...1.1.62
[1.1.61]: https://github.com/IFRCGo/go-api/compare/1.1.60...1.1.61
[1.1.60]: https://github.com/IFRCGo/go-api/compare/1.1.59...1.1.60
[1.1.59]: https://github.com/IFRCGo/go-api/compare/1.1.58...1.1.59
[1.1.58]: https://github.com/IFRCGo/go-api/compare/1.1.57...1.1.58
[1.1.57]: https://github.com/IFRCGo/go-api/compare/1.1.56...1.1.57
[1.1.56]: https://github.com/IFRCGo/go-api/compare/1.1.55...1.1.56
[1.1.55]: https://github.com/IFRCGo/go-api/compare/1.1.54...1.1.55
[1.1.54]: https://github.com/IFRCGo/go-api/compare/1.1.53...1.1.54
[1.1.53]: https://github.com/IFRCGo/go-api/compare/1.1.52...1.1.53
[1.1.52]: https://github.com/IFRCGo/go-api/compare/1.1.51...1.1.52
[1.1.51]: https://github.com/IFRCGo/go-api/compare/1.1.50...1.1.51
[1.1.50]: https://github.com/IFRCGo/go-api/compare/1.1.49...1.1.50
[1.1.49]: https://github.com/IFRCGo/go-api/compare/1.1.48...1.1.49
[1.1.48]: https://github.com/IFRCGo/go-api/compare/1.1.47...1.1.48
[1.1.47]: https://github.com/IFRCGo/go-api/compare/1.1.46...1.1.47
[1.1.46]: https://github.com/IFRCGo/go-api/compare/1.1.45...1.1.46
[1.1.45]: https://github.com/IFRCGo/go-api/compare/1.1.44...1.1.45
[1.1.44]: https://github.com/IFRCGo/go-api/compare/1.1.43...1.1.44
[1.1.43]: https://github.com/IFRCGo/go-api/compare/1.1.42...1.1.43
[1.1.42]: https://github.com/IFRCGo/go-api/compare/1.1.41...1.1.42
[1.1.41]: https://github.com/IFRCGo/go-api/compare/1.1.40...1.1.41
[1.1.40]: https://github.com/IFRCGo/go-api/compare/1.1.39...1.1.40
[1.1.39]: https://github.com/IFRCGo/go-api/compare/1.1.38...1.1.39
[1.1.38]: https://github.com/IFRCGo/go-api/compare/1.1.37...1.1.38
[1.1.37]: https://github.com/IFRCGo/go-api/compare/1.1.36...1.1.37
[1.1.36]: https://github.com/IFRCGo/go-api/compare/1.1.35...1.1.36
[1.1.35]: https://github.com/IFRCGo/go-api/compare/1.1.34...1.1.35
[1.1.34]: https://github.com/IFRCGo/go-api/compare/1.1.33...1.1.34
[1.1.33]: https://github.com/IFRCGo/go-api/compare/1.1.32...1.1.33
[1.1.32]: https://github.com/IFRCGo/go-api/compare/1.1.31...1.1.32
[1.1.31]: https://github.com/IFRCGo/go-api/compare/1.1.30...1.1.31
[1.1.30]: https://github.com/IFRCGo/go-api/compare/1.1.29...1.1.30
[1.1.29]: https://github.com/IFRCGo/go-api/compare/1.1.28...1.1.29
[1.1.28]: https://github.com/IFRCGo/go-api/compare/1.1.27...1.1.28
[1.1.27]: https://github.com/IFRCGo/go-api/compare/1.1.26...1.1.27
[1.1.26]: https://github.com/IFRCGo/go-api/compare/1.1.25...1.1.26
[1.1.25]: https://github.com/IFRCGo/go-api/compare/1.1.24...1.1.25
[1.1.24]: https://github.com/IFRCGo/go-api/compare/1.1.23...1.1.24
[1.1.23]: https://github.com/IFRCGo/go-api/compare/1.1.22...1.1.23
[1.1.22]: https://github.com/IFRCGo/go-api/compare/1.1.21...1.1.22
[1.1.21]: https://github.com/IFRCGo/go-api/compare/1.1.20...1.1.21
[1.1.20]: https://github.com/IFRCGo/go-api/compare/1.1.19...1.1.20
[1.1.19]: https://github.com/IFRCGo/go-api/compare/1.1.18...1.1.19
[1.1.18]: https://github.com/IFRCGo/go-api/compare/1.1.17...1.1.18
[1.1.17]: https://github.com/IFRCGo/go-api/compare/1.1.16...1.1.17
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

# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Unreleased

## 1.1.278

### Added
 - Readd Sector

## 1.1.277

### Added
 - Release v4.3.4

## 1.1.276

### Added
 - RCCE tag

## 1.1.275

### Added
 - Domain whitelist

## 1.1.274

### Added
 - Release 2.3.1

## 1.1.273

### Added
 - Release 4.3.0

## 1.2.0

### Added
 - Fetch FTS HPC Data using google sheet.
 - Add visibility support for project. (Public, Login required, IFRC Only)
 - New Programme Type `Domestic`
 - Add Bulk Project Import in Admin Panel.
 - Enable history for Project changes.
 - Add Sector/SectorTag `Health (private)` and `COVID-19`.
 - Add API for Project for region.
 - Add Multiselect filters for Project API enumfields.

### Changed
 - Change Sector/SectorTag `Health` to `Health (public)`.

## 1.1.272

### Added
 - PER form search fix

## 1.1.271

### Added
 - Release 4.2.3

## 1.1.269

### Added
 - Error handlings

## 1.1.268

### Added
 - Max length of object_name set to 2000

## 1.1.267

### Added
 - 4.2.0 release

## 1.1.266

### Added
 - Vanity URLs, ingestion fixes, Email API to production

## 1.1.265

### Added
 - Vanity URLs for Emergencies

## 1.1.264

### Added
 - Updated runserver.sh with ENV var

## 1.1.263

### Added
 - Email API instead of smtplib

## 1.1.262

### Added
 - Appeal Documents ingestion URL fix

## 1.1.261

### Added
 - Added phone to FRContact serializer

## 1.1.260

### Added
 - Bhutan and Marshall Isl. to whitelist

## 1.1.259

### Added
 - Fallback Country queryset

## 1.1.258

### Added
 - Fixed Nonetype error for Followed Event notifs

## 1.1.257

### Added
 - Added logging to each Followed Event mail sent

## 1.1.256

### Added
 - Fix for Followed Events notif.

## 1.1.255

### Added
 - Separated Followed Event notifs

## 1.1.254

### Added
 - Limited threads for notif. emails and fixes

## 1.1.253
## 1.1.252
## 1.1.251
## 1.1.250
## 1.1.249
## 1.1.248
## 1.1.247

### Added
 - Fix backend/frontend pointing issue
 - Nicing *success.html and it's email_context
 - Changing base_url to frontend_url in recover_password
 - Changing hardcoded dsgo... URL-s in notifications (except logo)

## 1.1.246

### Added
 - Purging an obscure and unnecessary PER part of per_ns_phase

## 1.1.245
## 1.1.244
## 1.1.243
## 1.1.242
## 1.1.241

### Added
 - Changing email addressee to IM
 - Putting "!" alert into comment on top banner. Maybe used later
 - Timing of notification alerts on service break
 - Notification sending in case of erroneous ingestion

## 1.1.240
## 1.1.239

### Added
 - Making cleaner logging for FTS_HPC (databank ingest source)
 - Put a warning sign in case of ingest issue to the admin interface

## 1.1.238
## 1.1.237
## 1.1.236
## 1.1.235
## 1.1.234

### Added
 - New fields to CronJob log, showing result numbers also in title
 - Admin inter-face-lift, filters
 - Updating logging feature of different recurring jobs in api/manag... and databank/manag...
 - CronJobs result logging, admin page, log-rotate

## 1.1.233

### Added
 - Setting regions also in ingested WHO emergencies

## 1.1.232

### Added
 - Ingest WHO with double URL-s

## 1.1.231
## 1.1.230

### Added
 - Rapid Response to surge alerts
 - Rapid Response to personnel deployments

## 1.1.229
## 1.1.228
## 1.1.227
## 1.1.226
## 1.1.225

### Added
 - https://stackoverflow.com/questions/51850985/django-filter-typeerror-at-goods-init-got-an-unexpected-keyword-argumen
 - django-filters, field_name instead of name (also in view_filters.py, ListFilter)
 - PartnerDeploymentFilterset also to be field_name-ing
 - Some fixes in deployments/test_views.py, None is not allowed to be sent via POST
 - Empty value to split
 - Small migration of a warned default

## 1.1.224

### Added
 - Bump Django up to 2.2.9 - and some dependencies also

## 1.1.223

### Added
 - Washing the scraped raw appeal id from surplus spaces

## 1.1.222

### Added
 - Fix scrapers substring error

## 1.1.221

### Added
 - Changed scrapers save to loop from bulk_create

## 1.1.220

### Added
 - Fixing git tag again...

## 1.1.219

### Added
 - pdfminer.six package version upgrade

## 1.1.218

### Added
 - Fix tag to 218

## 1.1.217

### Added
 - Workaround for thousand seps. for notif mails

## 1.1.216

### Added
 - Removed line used for testing PDF scrapers

## 1.1.215

### Added
 - PDF scrapers implementation (EPoA, OU, EA, FR)

## 1.1.214

### Added
 - User permission for 3W

## 1.1.213

### Added
 - Integers to float for thousand sep. in notifs

## 1.1.212

### Added
 - Notification email changes

## 1.1.211

### Added
 - handover FDRS credential

## 1.1.210

### Added
 - Databank

## 1.1.209

### Added
 - Last (or latest) notification e-mail fixes

## 1.1.208

### Added
 - Change back test data

## 1.1.207

### Added
 - index_and_notify.py not updating

## 1.1.206

### Added
 - Add new fields to MiniFieldReportSerializer needed for emergency page

## 1.1.205

### Added
 - New Op. notif. Field Reports list fix

## 1.1.204

### Added
 - Created date instead of modified for Weekly Digest notif.

## 1.1.203

### Added
 - Further notif. fixes

## 1.1.202

### Added
 - Notification fixes

## 1.1.201

### Added
 - New Operation notif. fix

## 1.1.200

### Added
 - Remove dtype validation for Project

## 1.1.199

### Added
 - Add the style tag to most elements to show up  correctly in the desktop Outlook client

## 1.1.198

### Added
 - Minor fixes of Weekly Digest notification fields

## 1.1.197

### Added
 - Added Actions for FR notif and fixed by Munus reqs

## 1.1.196

### Added
 - Fixes field names for potentially_affected fields.

## 1.1.195

### Added
 - Allow Actions to belong to both Event and Early Warning types

## 1.1.194

### Added
 - Add a boolean for Event to be featured on the region page

## 1.1.193

### Added
 - Notification rework

## 1.1.192

### Added
 - Adds organizations and field_report_types fields to the Action model
 - Adds an API endpoint to fetch all actions

## 1.1.191

### Added
 - Last step before merging 3W-project-api

## 1.1.190

### Added
 - Upgrading Pillow due to a vulnerability and some IS_STAGING code refactoring

## 1.1.189

### Added
 - PRODUCTION_URL check

## 1.1.188

### Added
 - Adding context_processors.py

## 1.1.187

### Added
 - Staging admin with grey background and sending status with related appeals

## 1.1.186

### Added
 - Implemented PER Draft deletion

## 1.1.185

### Added
 - redcrossghana.org into domain list

## 1.1.184

### Added
 - Do not repeat (in-future date) surge alert notifications

## 1.1.183

### Added
 - Adding croixrouge-mali.org

## 1.1.182

### Added
 - Added phone field to FieldReportContact

## 1.1.181
## 1.1.180

### Added
 - pck.pl and mda.org.il to domain names

## 1.1.179

### Added
 - Fix PER 3 numbering

## 1.1.178

### Added
 - PER Overview form list has to be tailored to users real PER permissions

## 1.1.177

### Added
 - Added CSV export of Field Reports for superusers

## 1.1.176
## 1.1.175
## 1.1.174
## 1.1.173

### Added
 - User CSV export without password hashes, with group membership list

## 1.1.172
## 1.1.171
## 1.1.170

### Added
 - Notification nicing (unsubs under text, cleaner subject with sense)

## 1.1.169

### Added
 - Nice admin URL

## 1.1.168

### Added
 - Nicer frontend URL

## 1.1.167

### Added
 - GO admin URL

## 1.1.166

### Added
 - Notifications: appeal -> operation

## 1.1.165

### Added
 - Point to event instead of field report in notifications

## 1.1.164

### Added
 - Email link to account notification settings

## 1.1.163

### Added
 - PER changes (form retexts)

## 1.1.162

### Added
 - Count engaged countries only (not form instances)

## 1.1.161

### Added
 - Fixing NS PER Engagement count

## 1.1.160

### Added
 - Daily followup

## 1.1.159

### Added
 - Daily email about second changes, phone_nr to field reports

## 1.1.158

### Added
 - Field Report changes, other_ fields

## 1.1.157
## 1.1.156

### Added
 - Surge Alerts to notifications

## 1.1.155

### Added
 - Deployment Messages

## 1.1.154
## 1.1.153
## 1.1.152

### Added
 - Multiple followed events for digest email

## 1.1.151

### Added
 - Email mockups finalized

## 1.1.150
## 1.1.149

### Added
 - Digest mode

## 1.1.148
## 1.1.147
## 1.1.146

### Added
 - Change notification tests
 - New notification features (timing, layout)

## 1.1.145

### Added
 - Baseline into ProcessPhases

## 1.1.144
## 1.1.143

### Added
 - Changing misleading variable name

## 1.1.142

### Added
 - Country Expanded

## 1.1.141

### Added
 - Create Draft.country via sendperdraft

## 1.1.140

### Added
 - Overview table addons

## 1.1.139

### Added
 - Draft, country filtering

## 1.1.138

### Added
 - Weekly digest and opening some PER views to public

## 1.1.137

### Added
 - Better PER Doc serializer

## 1.1.136

### Added
 - List PER Documents, filtered by countries

## 1.1.135

### Added
 - PER Document upload as file

## 1.1.134

### Added
 - Authorization is required when PER data is sent/deleted

## 1.1.133

### Added
 - Mini userserializer to PER

## 1.1.131
## 1.1.130

### Added
 - PER Overview (get, add)

## 1.1.129

### Added
 - PER Work Plans

## 1.1.128
## 1.1.127

### Added
 - Country settings and PER endpoints for Responsible Users

## 1.1.126
## 1.1.125

### Added
 - Country is unique in PER NS Phase.
 - Some new fields to deployment tables (to be able to ingest from Google Sprdsh)

## 1.1.124
## 1.1.123
## 1.1.122

### Added
 - Two new surge types to subscribe

## 1.1.121
## 1.1.120

### Added
 - PER visualization and phase administration, default value for starter NS-es

## 1.1.119

### Added
 - 2 more PER visulization endpoints

## 1.1.118
## 1.1.117

### Added
 - PER Form submitted since last deadline

## 1.1.116

### Added
 - Who, What, Where – Projects

## 1.1.115

### Added
 - Logo upload file extension filtering. Notification enhancements

## 1.1.114

### Added
 - Slight changes in notification dispatching

## 1.1.113
## 1.1.112

### Added
 - Fix EMAIL_HOST variable in .env file

## 1.1.111
## 1.1.110
## 1.1.109
## 1.1.108

### Added
 - Upload NS logo to logos/country_iso/filename

## 1.1.107

### Added
 - Fix a condition for 1

## 1.1.106
## 1.1.105

### Added
 - Fix ENV variables

## 1.1.104
## 1.1.103
## 1.1.102

### Added
 - Consolidate event notifications and test email addresses

## 1.1.101

### Added
 - Fix event notification bug

## 1.1.100

### Added
 - PER_DUE_DATE subscription and deletion

## 1.1.99

### Added
 - Some new PER form texts

## 1.1.98

### Added
 - Notification bugfixes

## 1.1.97

### Added
 - Inactive users should not get notifications

## 1.1.96

### Added
 - Edit perform by ID. Notification cutover for followed events

## 1.1.95

### Added
 - Filtering red WHO alerts. PER edit via /editperform

## 1.1.94

### Added
 - Deleting PER drafts before uploading the new one

## 1.1.93

### Added
 - Filter WHO ingests. PER Draft saving

## 1.1.92

### Added
 - No IP address to PER form header

## 1.1.91

### Added
 - Delete subscription of one event

## 1.1.90

### Added
 - Minor fix on ingest_who

## 1.1.89
## 1.1.88

### Added
 - Add one emergency to follow (and keep the others)

## 1.1.87
## 1.1.86

### Added
 - Search users from regions and some PER statistics

## 1.1.85

### Added
 - PER permission endpoint (to show PER tab or not)

## 1.1.84

### Added
 - Events following one-by-one

## 1.1.83

### Added
 - User details for PER forms

## 1.1.82

### Added
 - FormData filtering

## 1.1.81

### Added
 - Region into PER response list

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

[Unreleased]: https://github.com/IFRCGo/go-api/compare/1.2.278...HEAD
[1.2.278]: https://github.com/IFRCGo/go-api/compare/1.2.277...1.1.278
[1.2.277]: https://github.com/IFRCGo/go-api/compare/1.2.275...1.1.277
[1.2.276]: https://github.com/IFRCGo/go-api/compare/1.2.275...1.1.276
[1.2.275]: https://github.com/IFRCGo/go-api/compare/1.2.274...1.1.275
[1.2.274]: https://github.com/IFRCGo/go-api/compare/1.2.274...1.1.274
[1.2.274]: https://github.com/IFRCGo/go-api/compare/1.2.273...1.1.274
[1.2.273]: https://github.com/IFRCGo/go-api/compare/1.2.272...1.1.273
[1.1.272]: https://github.com/IFRCGo/go-api/compare/1.1.271...1.1.272
[1.1.271]: https://github.com/IFRCGo/go-api/compare/1.1.269...1.1.271
[1.1.269]: https://github.com/IFRCGo/go-api/compare/1.1.268...1.1.269
[1.1.268]: https://github.com/IFRCGo/go-api/compare/1.1.267...1.1.268
[1.1.267]: https://github.com/IFRCGo/go-api/compare/1.1.266...1.1.267
[1.1.266]: https://github.com/IFRCGo/go-api/compare/1.1.265...1.1.266
[1.1.265]: https://github.com/IFRCGo/go-api/compare/1.1.264...1.1.265
[1.1.264]: https://github.com/IFRCGo/go-api/compare/1.1.263...1.1.264
[1.1.263]: https://github.com/IFRCGo/go-api/compare/1.1.262...1.1.263
[1.1.262]: https://github.com/IFRCGo/go-api/compare/1.1.261...1.1.262
[1.1.261]: https://github.com/IFRCGo/go-api/compare/1.1.260...1.1.261
[1.1.260]: https://github.com/IFRCGo/go-api/compare/1.1.259...1.1.260
[1.1.259]: https://github.com/IFRCGo/go-api/compare/1.1.258...1.1.259
[1.1.258]: https://github.com/IFRCGo/go-api/compare/1.1.257...1.1.258
[1.1.257]: https://github.com/IFRCGo/go-api/compare/1.1.256...1.1.257
[1.1.256]: https://github.com/IFRCGo/go-api/compare/1.1.255...1.1.256
[1.1.255]: https://github.com/IFRCGo/go-api/compare/1.1.254...1.1.255
[1.1.254]: https://github.com/IFRCGo/go-api/compare/1.1.253...1.1.254
[1.1.253]: https://github.com/IFRCGo/go-api/compare/1.1.252...1.1.253
[1.1.252]: https://github.com/IFRCGo/go-api/compare/1.1.251...1.1.252
[1.1.251]: https://github.com/IFRCGo/go-api/compare/1.1.250...1.1.251
[1.1.250]: https://github.com/IFRCGo/go-api/compare/1.1.249...1.1.250
[1.1.249]: https://github.com/IFRCGo/go-api/compare/1.1.248...1.1.249
[1.1.248]: https://github.com/IFRCGo/go-api/compare/1.1.247...1.1.248
[1.1.247]: https://github.com/IFRCGo/go-api/compare/1.1.246...1.1.247
[1.1.246]: https://github.com/IFRCGo/go-api/compare/1.1.245...1.1.246
[1.1.245]: https://github.com/IFRCGo/go-api/compare/1.1.244...1.1.245
[1.1.244]: https://github.com/IFRCGo/go-api/compare/1.1.243...1.1.244
[1.1.243]: https://github.com/IFRCGo/go-api/compare/1.1.242...1.1.243
[1.1.242]: https://github.com/IFRCGo/go-api/compare/1.1.241...1.1.242
[1.1.241]: https://github.com/IFRCGo/go-api/compare/1.1.240...1.1.241
[1.1.240]: https://github.com/IFRCGo/go-api/compare/1.1.239...1.1.240
[1.1.239]: https://github.com/IFRCGo/go-api/compare/1.1.238...1.1.239
[1.1.238]: https://github.com/IFRCGo/go-api/compare/1.1.237...1.1.238
[1.1.237]: https://github.com/IFRCGo/go-api/compare/1.1.236...1.1.237
[1.1.236]: https://github.com/IFRCGo/go-api/compare/1.1.235...1.1.236
[1.1.235]: https://github.com/IFRCGo/go-api/compare/1.1.234...1.1.235
[1.1.234]: https://github.com/IFRCGo/go-api/compare/1.1.233...1.1.234
[1.1.233]: https://github.com/IFRCGo/go-api/compare/1.1.232...1.1.233
[1.1.232]: https://github.com/IFRCGo/go-api/compare/1.1.231...1.1.232
[1.1.231]: https://github.com/IFRCGo/go-api/compare/1.1.230...1.1.231
[1.1.230]: https://github.com/IFRCGo/go-api/compare/1.1.229...1.1.230
[1.1.229]: https://github.com/IFRCGo/go-api/compare/1.1.228...1.1.229
[1.1.228]: https://github.com/IFRCGo/go-api/compare/1.1.227...1.1.228
[1.1.227]: https://github.com/IFRCGo/go-api/compare/1.1.226...1.1.227
[1.1.226]: https://github.com/IFRCGo/go-api/compare/1.1.225...1.1.226
[1.1.225]: https://github.com/IFRCGo/go-api/compare/1.1.224...1.1.225
[1.1.224]: https://github.com/IFRCGo/go-api/compare/1.1.223...1.1.224
[1.1.223]: https://github.com/IFRCGo/go-api/compare/1.1.222...1.1.223
[1.1.222]: https://github.com/IFRCGo/go-api/compare/1.1.221...1.1.222
[1.1.221]: https://github.com/IFRCGo/go-api/compare/1.1.220...1.1.221
[1.1.220]: https://github.com/IFRCGo/go-api/compare/1.1.219...1.1.220
[1.1.219]: https://github.com/IFRCGo/go-api/compare/1.1.218...1.1.219
[1.1.218]: https://github.com/IFRCGo/go-api/compare/1.1.217...1.1.218
[1.1.217]: https://github.com/IFRCGo/go-api/compare/1.1.216...1.1.217
[1.1.216]: https://github.com/IFRCGo/go-api/compare/1.1.215...1.1.216
[1.1.215]: https://github.com/IFRCGo/go-api/compare/1.1.214...1.1.215
[1.1.214]: https://github.com/IFRCGo/go-api/compare/1.1.213...1.1.214
[1.1.213]: https://github.com/IFRCGo/go-api/compare/1.1.212...1.1.213
[1.1.212]: https://github.com/IFRCGo/go-api/compare/1.1.211...1.1.212
[1.1.211]: https://github.com/IFRCGo/go-api/compare/1.1.210...1.1.211
[1.1.210]: https://github.com/IFRCGo/go-api/compare/1.1.209...1.1.210
[1.1.209]: https://github.com/IFRCGo/go-api/compare/1.1.208...1.1.209
[1.1.208]: https://github.com/IFRCGo/go-api/compare/1.1.207...1.1.208
[1.1.207]: https://github.com/IFRCGo/go-api/compare/1.1.206...1.1.207
[1.1.206]: https://github.com/IFRCGo/go-api/compare/1.1.205...1.1.206
[1.1.205]: https://github.com/IFRCGo/go-api/compare/1.1.204...1.1.205
[1.1.204]: https://github.com/IFRCGo/go-api/compare/1.1.203...1.1.204
[1.1.203]: https://github.com/IFRCGo/go-api/compare/1.1.202...1.1.203
[1.1.202]: https://github.com/IFRCGo/go-api/compare/1.1.201...1.1.202
[1.1.201]: https://github.com/IFRCGo/go-api/compare/1.1.200...1.1.201
[1.1.200]: https://github.com/IFRCGo/go-api/compare/1.1.199...1.1.200
[1.1.199]: https://github.com/IFRCGo/go-api/compare/1.1.198...1.1.199
[1.1.198]: https://github.com/IFRCGo/go-api/compare/1.1.197...1.1.198
[1.1.197]: https://github.com/IFRCGo/go-api/compare/1.1.196...1.1.197
[1.1.196]: https://github.com/IFRCGo/go-api/compare/1.1.195...1.1.196
[1.1.195]: https://github.com/IFRCGo/go-api/compare/1.1.194...1.1.195
[1.1.194]: https://github.com/IFRCGo/go-api/compare/1.1.193...1.1.194
[1.1.193]: https://github.com/IFRCGo/go-api/compare/1.1.192...1.1.193
[1.1.192]: https://github.com/IFRCGo/go-api/compare/1.1.191...1.1.192
[1.1.191]: https://github.com/IFRCGo/go-api/compare/1.1.190...1.1.191
[1.1.190]: https://github.com/IFRCGo/go-api/compare/1.1.189...1.1.190
[1.1.189]: https://github.com/IFRCGo/go-api/compare/1.1.188...1.1.189
[1.1.188]: https://github.com/IFRCGo/go-api/compare/1.1.187...1.1.188
[1.1.187]: https://github.com/IFRCGo/go-api/compare/1.1.186...1.1.187
[1.1.186]: https://github.com/IFRCGo/go-api/compare/1.1.185...1.1.186
[1.1.185]: https://github.com/IFRCGo/go-api/compare/1.1.184...1.1.185
[1.1.184]: https://github.com/IFRCGo/go-api/compare/1.1.183...1.1.184
[1.1.183]: https://github.com/IFRCGo/go-api/compare/1.1.182...1.1.183
[1.1.182]: https://github.com/IFRCGo/go-api/compare/1.1.181...1.1.182
[1.1.181]: https://github.com/IFRCGo/go-api/compare/1.1.180...1.1.181
[1.1.180]: https://github.com/IFRCGo/go-api/compare/1.1.179...1.1.180
[1.1.179]: https://github.com/IFRCGo/go-api/compare/1.1.178...1.1.179
[1.1.178]: https://github.com/IFRCGo/go-api/compare/1.1.177...1.1.178
[1.1.177]: https://github.com/IFRCGo/go-api/compare/1.1.176...1.1.177
[1.1.176]: https://github.com/IFRCGo/go-api/compare/1.1.175...1.1.176
[1.1.175]: https://github.com/IFRCGo/go-api/compare/1.1.174...1.1.175
[1.1.174]: https://github.com/IFRCGo/go-api/compare/1.1.173...1.1.174
[1.1.173]: https://github.com/IFRCGo/go-api/compare/1.1.172...1.1.173
[1.1.172]: https://github.com/IFRCGo/go-api/compare/1.1.171...1.1.172
[1.1.171]: https://github.com/IFRCGo/go-api/compare/1.1.170...1.1.171
[1.1.170]: https://github.com/IFRCGo/go-api/compare/1.1.169...1.1.170
[1.1.169]: https://github.com/IFRCGo/go-api/compare/1.1.168...1.1.169
[1.1.168]: https://github.com/IFRCGo/go-api/compare/1.1.167...1.1.168
[1.1.167]: https://github.com/IFRCGo/go-api/compare/1.1.166...1.1.167
[1.1.166]: https://github.com/IFRCGo/go-api/compare/1.1.165...1.1.166
[1.1.165]: https://github.com/IFRCGo/go-api/compare/1.1.164...1.1.165
[1.1.164]: https://github.com/IFRCGo/go-api/compare/1.1.163...1.1.164
[1.1.163]: https://github.com/IFRCGo/go-api/compare/1.1.162...1.1.163
[1.1.162]: https://github.com/IFRCGo/go-api/compare/1.1.161...1.1.162
[1.1.161]: https://github.com/IFRCGo/go-api/compare/1.1.160...1.1.161
[1.1.160]: https://github.com/IFRCGo/go-api/compare/1.1.159...1.1.160
[1.1.159]: https://github.com/IFRCGo/go-api/compare/1.1.158...1.1.159
[1.1.158]: https://github.com/IFRCGo/go-api/compare/1.1.157...1.1.158
[1.1.157]: https://github.com/IFRCGo/go-api/compare/1.1.156...1.1.157
[1.1.156]: https://github.com/IFRCGo/go-api/compare/1.1.155...1.1.156
[1.1.155]: https://github.com/IFRCGo/go-api/compare/1.1.154...1.1.155
[1.1.154]: https://github.com/IFRCGo/go-api/compare/1.1.153...1.1.154
[1.1.153]: https://github.com/IFRCGo/go-api/compare/1.1.152...1.1.153
[1.1.152]: https://github.com/IFRCGo/go-api/compare/1.1.151...1.1.152
[1.1.151]: https://github.com/IFRCGo/go-api/compare/1.1.150...1.1.151
[1.1.150]: https://github.com/IFRCGo/go-api/compare/1.1.149...1.1.150
[1.1.149]: https://github.com/IFRCGo/go-api/compare/1.1.148...1.1.149
[1.1.148]: https://github.com/IFRCGo/go-api/compare/1.1.147...1.1.148
[1.1.147]: https://github.com/IFRCGo/go-api/compare/1.1.146...1.1.147
[1.1.146]: https://github.com/IFRCGo/go-api/compare/1.1.145...1.1.146
[1.1.145]: https://github.com/IFRCGo/go-api/compare/1.1.144...1.1.145
[1.1.144]: https://github.com/IFRCGo/go-api/compare/1.1.143...1.1.144
[1.1.143]: https://github.com/IFRCGo/go-api/compare/1.1.142...1.1.143
[1.1.142]: https://github.com/IFRCGo/go-api/compare/1.1.141...1.1.142
[1.1.141]: https://github.com/IFRCGo/go-api/compare/1.1.140...1.1.141
[1.1.140]: https://github.com/IFRCGo/go-api/compare/1.1.139...1.1.140
[1.1.139]: https://github.com/IFRCGo/go-api/compare/1.1.138...1.1.139
[1.1.138]: https://github.com/IFRCGo/go-api/compare/1.1.137...1.1.138
[1.1.137]: https://github.com/IFRCGo/go-api/compare/1.1.136...1.1.137
[1.1.136]: https://github.com/IFRCGo/go-api/compare/1.1.135...1.1.136
[1.1.135]: https://github.com/IFRCGo/go-api/compare/1.1.134...1.1.135
[1.1.134]: https://github.com/IFRCGo/go-api/compare/1.1.133...1.1.134
[1.1.133]: https://github.com/IFRCGo/go-api/compare/1.1.132...1.1.133
[1.1.132]: https://github.com/IFRCGo/go-api/compare/1.1.131...1.1.132
[1.1.131]: https://github.com/IFRCGo/go-api/compare/1.1.130...1.1.131
[1.1.130]: https://github.com/IFRCGo/go-api/compare/1.1.129...1.1.130
[1.1.129]: https://github.com/IFRCGo/go-api/compare/1.1.128...1.1.129
[1.1.128]: https://github.com/IFRCGo/go-api/compare/1.1.127...1.1.128
[1.1.127]: https://github.com/IFRCGo/go-api/compare/1.1.126...1.1.127
[1.1.126]: https://github.com/IFRCGo/go-api/compare/1.1.125...1.1.126
[1.1.125]: https://github.com/IFRCGo/go-api/compare/1.1.124...1.1.125
[1.1.124]: https://github.com/IFRCGo/go-api/compare/1.1.123...1.1.124
[1.1.123]: https://github.com/IFRCGo/go-api/compare/1.1.122...1.1.123
[1.1.122]: https://github.com/IFRCGo/go-api/compare/1.1.121...1.1.122
[1.1.121]: https://github.com/IFRCGo/go-api/compare/1.1.120...1.1.121
[1.1.120]: https://github.com/IFRCGo/go-api/compare/1.1.119...1.1.120
[1.1.119]: https://github.com/IFRCGo/go-api/compare/1.1.118...1.1.119
[1.1.118]: https://github.com/IFRCGo/go-api/compare/1.1.117...1.1.118
[1.1.117]: https://github.com/IFRCGo/go-api/compare/1.1.116...1.1.117
[1.1.116]: https://github.com/IFRCGo/go-api/compare/1.1.115...1.1.116
[1.1.115]: https://github.com/IFRCGo/go-api/compare/1.1.114...1.1.115
[1.1.114]: https://github.com/IFRCGo/go-api/compare/1.1.113...1.1.114
[1.1.113]: https://github.com/IFRCGo/go-api/compare/1.1.112...1.1.113
[1.1.112]: https://github.com/IFRCGo/go-api/compare/1.1.111...1.1.112
[1.1.111]: https://github.com/IFRCGo/go-api/compare/1.1.110...1.1.111
[1.1.110]: https://github.com/IFRCGo/go-api/compare/1.1.109...1.1.110
[1.1.109]: https://github.com/IFRCGo/go-api/compare/1.1.108...1.1.109
[1.1.108]: https://github.com/IFRCGo/go-api/compare/1.1.107...1.1.108
[1.1.107]: https://github.com/IFRCGo/go-api/compare/1.1.106...1.1.107
[1.1.106]: https://github.com/IFRCGo/go-api/compare/1.1.105...1.1.106
[1.1.105]: https://github.com/IFRCGo/go-api/compare/1.1.104...1.1.105
[1.1.104]: https://github.com/IFRCGo/go-api/compare/1.1.103...1.1.104
[1.1.103]: https://github.com/IFRCGo/go-api/compare/1.1.102...1.1.103
[1.1.102]: https://github.com/IFRCGo/go-api/compare/1.1.101...1.1.102
[1.1.101]: https://github.com/IFRCGo/go-api/compare/1.1.100...1.1.101
[1.1.100]: https://github.com/IFRCGo/go-api/compare/1.1.99...1.1.100
[1.1.99]: https://github.com/IFRCGo/go-api/compare/1.1.98...1.1.99
[1.1.98]: https://github.com/IFRCGo/go-api/compare/1.1.97...1.1.98
[1.1.97]: https://github.com/IFRCGo/go-api/compare/1.1.96...1.1.97
[1.1.96]: https://github.com/IFRCGo/go-api/compare/1.1.95...1.1.96
[1.1.95]: https://github.com/IFRCGo/go-api/compare/1.1.94...1.1.95
[1.1.94]: https://github.com/IFRCGo/go-api/compare/1.1.93...1.1.94
[1.1.93]: https://github.com/IFRCGo/go-api/compare/1.1.92...1.1.93
[1.1.92]: https://github.com/IFRCGo/go-api/compare/1.1.91...1.1.92
[1.1.91]: https://github.com/IFRCGo/go-api/compare/1.1.90...1.1.91
[1.1.90]: https://github.com/IFRCGo/go-api/compare/1.1.89...1.1.90
[1.1.89]: https://github.com/IFRCGo/go-api/compare/1.1.88...1.1.89
[1.1.88]: https://github.com/IFRCGo/go-api/compare/1.1.87...1.1.88
[1.1.87]: https://github.com/IFRCGo/go-api/compare/1.1.86...1.1.87
[1.1.86]: https://github.com/IFRCGo/go-api/compare/1.1.85...1.1.86
[1.1.85]: https://github.com/IFRCGo/go-api/compare/1.1.84...1.1.85
[1.1.84]: https://github.com/IFRCGo/go-api/compare/1.1.83...1.1.84
[1.1.83]: https://github.com/IFRCGo/go-api/compare/1.1.82...1.1.83
[1.1.82]: https://github.com/IFRCGo/go-api/compare/1.1.81...1.1.82
[1.1.81]: https://github.com/IFRCGo/go-api/compare/1.1.80...1.1.81
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

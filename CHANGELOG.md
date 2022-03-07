# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Unreleased

 - Changing 1 day limit for registrations to 30

## 1.1.420

### Added
 - Flash update
 - General documents (more convenient creation)
 - Adding poetry as Python package manager
   · Enable buildx for docker build
   · Enable docker layer caching in Circle-CI
   · Update README.md for poetry
   · Add migration check to Circle-CI
   · Provide empty default value for docker-compose env vars to disable warnings
 - Editable slugs for emergencies
 - We can acknowledge the erroneous cronjob runs

## 1.1.419

### Added
 - Registration workflow change  
 - String/List mismatch in email addressees - fixed

## 1.1.418

### Added
 - Safelink Outlook link checking caused double run - fixed
 - TriggeringAmount – better triggering appeal change
 - Fixing appeal-docs ingesting (urllib3)
 - New registration method (without 2 gate-keepers)

## 1.1.417

### Added
 - Deployments/personnel country_to (to model, test and API endpoints)
 - Filling the country_to field with related event first country

## 1.1.416

### Added
 - Timezone into end_date comparison (personnel_by_event)
 - Using https before resource_uri
 - Bump up the necessary packages to use python 3.8 due to Pillow must-upgrade:
     Pillow 9.0.0, boto3==1.20.38, ipython==8.0.0, pandas==1.3.5, psycopg2==2.8.6 (!),
     python-Levenshtein==0.12.1, requests==2.27.1, urllib3==1.26.8

## 1.1.415

### Added
 - Adding ordering (by id) to events KeyFigures
 - Fixing moved snapshot tests

## 1.1.414

### Added
 - Reverting email layout of new operations (Outlook discrepancies)

## 1.1.413

### Added
 - Improved email layout for new operations (=appeals)
 - Ingest appeals - process all, regardless the modify time

## 1.1.412

### Added
 - Django to 2.2.25
 - ESearch:6.8.2 (to be friendly with the new, log4j-fixed ESearch image, 6.8.21)
 - Appeal Ingest - process all appeals regardless of the modify time
 - Using regions label instead of the numeric name
 - Using event name when no operation name in SurgeAlert

## 1.1.411

### Added
 - Enhancements in surge alert notifications
 - New content-visibility level (IFRC_NS: FR, Proj, event)
 - Longer date interval for appeal doc scraper
 - Bump up elasticsearch to 6.3.0, urllib3 to 1.26.7
 - Fixing .dockerignore, bump up pip to 21.1
 - Search parameter for most of /docs endpoints
 - Handle Stand-Downs on Surge page
 - GeneralDocument for general document upload
 - Local development env change: psql 9.6 to 11
 - Molnix_id as read only field
 - Use molnix_id instead of pk while marking deployments inactive

## 1.1.410

### Added
 - No more emails for more surge alerts
 - Appeal-documents: better ingest (they can be on /sites/... too)

## 1.1.409

### Added
 - Appeal documents ingesting is more reliable

## 1.1.408

### Added
 - Fixing ERP interface: Appeal/DREF Value
 - Following the changed structure of appeals web page (ingest_appeal_docs)

## 1.1.407

### Added
  - Surge email notification improvements (links to #surge tab of emergency)
  - Appeal ingest fixes
    · modified_at = time of appeal ingest run
    · real_data_update = max(APD_modify_time) from the appeals API
  - More possibilities for unauthenticated users:
    · the surge (/deployments) page is visible
    · the single emergency-related #surge tab is visible, except persons' name.
    · changed snapshot tests due to the aboves

## 1.1.406

### Added
 - Showing tab titles in API emergency listing (#1204)
 - Better appeal deletion with automatic exclusion filter setting
 - Endpoint for getting outer NS links (for checking).

## 1.1.405
 - Allowing null in region_deployed_to

## 1.1.404

### Added
 - Three sleeps into map tile updater

## 1.1.403

### Added
 - Adding new tileset attributes
 - Fixing databank cron jobs failures

## 1.1.402

### Added
 - Description field to molnixTags

## 1.1.401

### Added
 - Fixing different RR key figures to be in pair
 - Fixing scrape-pdfs temporarily with episerver

## 1.1.400

### Added
 - Fixing appeal-docs scraper for the new ifrc.org

## 1.1.399

### Added
 - Deployments, Surge page Key Figures and tables:
   · Show only unique organization names at Deployments
   · Use correct personnel_count variable to show counts
   · Deployment counts on Emergency pages
   · ERUs Deployed counts in aggregate
   · Counts of Deployments per Emergency in the Deployments Overvw by Emerg. tbl
   · Fix ERU count to show count of all ERUs with a deployed_to country
   · Surge alerts: by default show all, add filter to show only active
   · Fixing event-specific failure of AggregateDeployments

## 1.1.398

### Added
 - Emergency severity color change 2

## 1.1.397

### Added
 - Emergency severity color change

## 1.1.396

### Added
 - Add more fields in MiniUserSerializer

## 1.1.395

### Added
 - Delete RCCE tag

## 1.1.394

### Added
 - Change migrations logic for RCCE tag
 - Using xmltodict instead of XML2Dict==0.2.2 due to security reasons

## 1.1.393

### Added
 - Remove RCCE tag and change it to combination of CEA and HEALTH_PUBLIC

## 1.1.392

### Added
 - Appeal receiver fix (ingest issue) - 2

## 1.1.391

### Added
 - Appeal receiver fix (ingest issue)

## 1.1.390

### Added
 - Store country as separate field on surge alerts, import from molnix

## 1.1.389

### Added
 - Add field modified_by in project model

## 1.1.388

### Added
 - Prod deployment 5.3.0

## 1.1.387

### Added
 - PROD deployment 5.3.0

## 1.1.386

### Added
 - Fix country association with Molnix imports

## 1.1.385

### Added
 - deployments agg

## 1.1.384

### Added
 - maptile - import shapefile by id hotfix

## 1.1.383

### Added
 - maptile - import shapefile by id arg fix

## 1.1.382

### Added
 - maptile - import shapefile by id

## 1.1.381

### Added
 - maptile - import shapefile by id

## 1.1.380

### Added
 - Hotfix after 5.2.0

## 1.1.379

### Added
 - PROD deploy

## 1.1.378

### Added
 - Merged changes

## 1.1.377

### Added
 - Use ongoing projects for global project Endpoint

## 1.1.376

### Added
 - Covid page related update

## 1.1.373

### Added
 - Over-ride matching for NS names from Molnix
 - Update geom if it exists instead of adding new

## 1.1.372

### Added
 - Add email alert for project near complete status
 - Feature/global project api additional fields

## 1.1.371

### Added
 - appealHistory list API fix

## 1.1.370

### Added
 - appealHistory list API

## 1.1.369

### Added
 - Add global project api endpoints

## 1.1.368

### Added
 - Handle case where incoming value for personnel deployment from Molnix is null

## 1.1.367

### Added
 - Return from push_fr_data if ERP_ENDPOINT is 'x' (empty not good: broke tests)

## 1.1.366

### Added
 - Add country iso and name to district and district centroid tilesets
 - Bump django from 2.2.22 to 2.2.24

## 1.1.365

### Added
 - Bump django from 2.2.21 to 2.2.22

## 1.1.364

### Added
 - fix API docs

## 1.1.363

### Added
 - Add Custom CSV serializer for Project, fix test warnings

## 1.1.362

### Added
 - Removing duplicate from reqs, bump up urllib3 

## 1.1.361

### Added
 - appeal history fill

## 1.1.360

### Added
 - Changing ERP to Ocp-Apim authentication

## 1.1.359

### Added
 - appeal history additional fixes

## 1.1.358

### Added
 - appeal history (1.1.357 skipped)

## 1.1.356

### Added
 - change in molnix api returning secondment incoming ns name

## 1.1.355

### Added
 - Adding new ERU types

## 1.1.354

### Added
 - district API country iso

## 1.1.353

### Added
 - appeal filter

## 1.1.352

### Added
 - ERP unit tests. Mapbox tiling fix

## 1.1.351

### Added
 - Trim whitespace from ns names coming from molnix api

## 1.1.350

### Added
 - Remove MDRMM016 from appealFilter

## 1.1.349

### Added
 - Feature molnix hidden

## 1.1.348

### Added
 - Set active personal based on hidden or draft

## 1.1.347

### Added
 - Country info added to district API

## 1.1.346

### Added
 - 3W Project Import: use DD/MM/YYYY

## 1.1.345

### Added
 - Fix variable define error (deployments/forms)

## 1.1.344

### Added
 - Use general user role for project visibility

## 1.1.343

### Added
 - go live

## 1.1.342

### Added
 - modifying elastic search

## 1.1.341

### Added
 - Adding name to elasticsearch fields

## 1.1.340

### Added
 - Enabling ERP sending

## 1.1.339
## 1.1.338

### Added
 - Temporary disable ERP sending

## 1.1.337

### Added
 - Release v5.0.0

## 1.1.336

### Added
 - Using dtype.name instead of id

## 1.1.335

### Added
 - Fix missed range for project status update

## 1.1.334

### Added
 - Empty as InitialRequestType

## 1.1.333

### Added
 - ERP trigger to receivers for Field Reports

## 1.1.332

### Added
 - log incoming API requests to Azure (analytics)

## 1.1.331

### Added
 - Fix broken /docs endpoint via Markdown bump
 - specify languages and string with empty values

## 1.1.330

### Added
 - Update Projects status automatically

## 1.1.329

### Added
 - Query fix for personnel endpoint, CSV export simplify

## 1.1.328

### Added
 - Bump djangorestframework from 3.9.1 to 3.11.2

## 1.1.327

### Added
 - Bump django-debug-toolbar from 2.2 to 2.2.1

## 1.1.326

### Added
 - Add custom permission for Translation Dashboard

## 1.1.325

### Added
 - Django up to 2.2.20

## 1.1.324

### Added
 - merge migrations

## 1.1.323

### Added
 - modify to nullbooleanfields in field report

## 1.1.322

### Added
 - Fix country uppercase migration issue

## 1.1.321

### Added
 - country_from only in active deployments

## 1.1.320

### Added
 - git ignore extended

## 1.1.319

### Added
 - A short demo change

## 1.1.318

### Added
 - Bump lxml 4.6.2 > 4.6.3

## 1.1.317

### Added
 - Bumping up pygments, jinja2, pillow

## 1.1.316

### Added
 - Add back molnix job

## 1.1.315

### Added
 - Hotfix release v4.6.3

## 1.1.314

### Added
 - Hotfix release v4.6.3

## 1.1.313

### Added
 - Skip MDRMM016 Appeal ingestion

## 1.1.312

### Added
 - Fix git tag

## 1.1.311

### Added
 - Release v4.6.2

## 1.1.310

### Added
 - Release v4.6.1

## 1.1.309

### Added
 - Release v4.6

## 1.1.308

### Added
 - Elasticsearch hotfixes

## 1.1.307

### Added
 - Hotfix to add request_assistance to FR serializer

## 1.1.306

### Added
 - Increase version

## 1.1.305

### Added
 - Hoffix for deployments

## 1.1.304

### Added
 - Release v4.5.0

## 1.1.303

### Added
 - Release v4.4.6

## 1.1.302

 - Hotfix: Appeal ingest geo-mapping fix

## 1.1.301

### Added
 - Minor fixes

## 1.1.300

### Added
 - Hotfix - Password Recovery

## 1.1.299

### Added
 - Hotfix - Password Recovery

## 1.1.298

### Added
 - Hotfix - Release v4.4.3

## 1.1.297

### Added
 - Hotfix - Dont overwrite non-english languages

## 1.1.296

### Added
 - Hotfix for languages fallbacks

## 1.1.295

### Added
 - Hotfix for snippets fallback text

## 1.1.294

### Added
 - Hotfix for ingest_appeals

## 1.1.293

### Added
 - Release v4.4.0 - Safari

## 1.1.292

### Added
 - Hotfix for DATA_UPLOAD_MAX_NUMBER_FIELDS

## 1.1.291

### Added
 - Fix version and git tag

## 1.1.290

### Added
 - Hotfix for Elasticsearch

## 1.1.289

### Added
 - Hotfix for FR visibility for IFRC Admins

## 1.1.288

### Added
 - Release v4.3.11

## 1.1.287

### Added
 - Hotfix for SendMail

## 1.1.286

### Added
 - Hotfix of commits in master

## 1.1.285

### Added
 - Release v4.3.9

## 1.1.284

### Added
 - Labels fix for CSVs

## 1.1.283

### Added
 - Release v4.3.6

## 1.1.282

### Added
 - Minor backend fixes for 4.3.5

## 1.1.281

### Added
 - Minor fixes to go with v4.3.5 frontend PR

## 1.1.280

### Added
 - Release v4.3.5

## 1.1.279

### Added
 - Hotfixes after 4.3.4

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
 - Nicing ...success.html and it's email_context
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

[Unreleased]: https://github.com/IFRCGo/go-api/compare/1.1.420...HEAD
[1.1.420]: https://github.com/IFRCGo/go-api/compare/1.1.419...1.1.420
[1.1.419]: https://github.com/IFRCGo/go-api/compare/1.1.418...1.1.419
[1.1.418]: https://github.com/IFRCGo/go-api/compare/1.1.417...1.1.418
[1.1.417]: https://github.com/IFRCGo/go-api/compare/1.1.416...1.1.417
[1.1.416]: https://github.com/IFRCGo/go-api/compare/1.1.415...1.1.416
[1.1.415]: https://github.com/IFRCGo/go-api/compare/1.1.414...1.1.415
[1.1.414]: https://github.com/IFRCGo/go-api/compare/1.1.413...1.1.414
[1.1.413]: https://github.com/IFRCGo/go-api/compare/1.1.412...1.1.413
[1.1.412]: https://github.com/IFRCGo/go-api/compare/1.1.411...1.1.412
[1.1.411]: https://github.com/IFRCGo/go-api/compare/1.1.410...1.1.411
[1.1.410]: https://github.com/IFRCGo/go-api/compare/1.1.409...1.1.410
[1.1.409]: https://github.com/IFRCGo/go-api/compare/1.1.408...1.1.409
[1.1.408]: https://github.com/IFRCGo/go-api/compare/1.1.407...1.1.408
[1.1.407]: https://github.com/IFRCGo/go-api/compare/1.1.406...1.1.407
[1.1.406]: https://github.com/IFRCGo/go-api/compare/1.1.405...1.1.406
[1.1.405]: https://github.com/IFRCGo/go-api/compare/1.1.404...1.1.405
[1.1.404]: https://github.com/IFRCGo/go-api/compare/1.1.403...1.1.404
[1.1.403]: https://github.com/IFRCGo/go-api/compare/1.1.402...1.1.403
[1.1.402]: https://github.com/IFRCGo/go-api/compare/1.1.401...1.1.402
[1.1.401]: https://github.com/IFRCGo/go-api/compare/1.1.400...1.1.401
[1.1.400]: https://github.com/IFRCGo/go-api/compare/1.1.399...1.1.400
[1.1.399]: https://github.com/IFRCGo/go-api/compare/1.1.398...1.1.399
[1.1.398]: https://github.com/IFRCGo/go-api/compare/1.1.397...1.1.398
[1.1.397]: https://github.com/IFRCGo/go-api/compare/1.1.396...1.1.397
[1.1.396]: https://github.com/IFRCGo/go-api/compare/1.1.395...1.1.396
[1.1.395]: https://github.com/IFRCGo/go-api/compare/1.1.394...1.1.395
[1.1.394]: https://github.com/IFRCGo/go-api/compare/1.1.393...1.1.394
[1.1.393]: https://github.com/IFRCGo/go-api/compare/1.1.392...1.1.393
[1.1.392]: https://github.com/IFRCGo/go-api/compare/1.1.391...1.1.392
[1.1.391]: https://github.com/IFRCGo/go-api/compare/1.1.390...1.1.391
[1.1.390]: https://github.com/IFRCGo/go-api/compare/1.1.389...1.1.390
[1.1.389]: https://github.com/IFRCGo/go-api/compare/1.1.388...1.1.389
[1.1.388]: https://github.com/IFRCGo/go-api/compare/1.1.387...1.1.388
[1.1.387]: https://github.com/IFRCGo/go-api/compare/1.1.386...1.1.387
[1.1.386]: https://github.com/IFRCGo/go-api/compare/1.1.385...1.1.386
[1.1.385]: https://github.com/IFRCGo/go-api/compare/1.1.384...1.1.385
[1.1.384]: https://github.com/IFRCGo/go-api/compare/1.1.383...1.1.384
[1.1.383]: https://github.com/IFRCGo/go-api/compare/1.1.382...1.1.383
[1.1.382]: https://github.com/IFRCGo/go-api/compare/1.1.381...1.1.382
[1.1.381]: https://github.com/IFRCGo/go-api/compare/1.1.380...1.1.381
[1.1.380]: https://github.com/IFRCGo/go-api/compare/1.1.379...1.1.380
[1.1.379]: https://github.com/IFRCGo/go-api/compare/1.1.378...1.1.379
[1.1.378]: https://github.com/IFRCGo/go-api/compare/1.1.377...1.1.378
[1.1.377]: https://github.com/IFRCGo/go-api/compare/1.1.376...1.1.377
[1.1.376]: https://github.com/IFRCGo/go-api/compare/1.1.373...1.1.376
[1.1.373]: https://github.com/IFRCGo/go-api/compare/1.1.372...1.1.373
[1.1.372]: https://github.com/IFRCGo/go-api/compare/1.1.371...1.1.372
[1.1.371]: https://github.com/IFRCGo/go-api/compare/1.1.370...1.1.371
[1.1.370]: https://github.com/IFRCGo/go-api/compare/1.1.369...1.1.370
[1.1.369]: https://github.com/IFRCGo/go-api/compare/1.1.368...1.1.369
[1.1.368]: https://github.com/IFRCGo/go-api/compare/1.1.367...1.1.368
[1.1.367]: https://github.com/IFRCGo/go-api/compare/1.1.366...1.1.367
[1.1.366]: https://github.com/IFRCGo/go-api/compare/1.1.365...1.1.366
[1.1.365]: https://github.com/IFRCGo/go-api/compare/1.1.364...1.1.365
[1.1.364]: https://github.com/IFRCGo/go-api/compare/1.1.363...1.1.364
[1.1.363]: https://github.com/IFRCGo/go-api/compare/1.1.362...1.1.363
[1.1.362]: https://github.com/IFRCGo/go-api/compare/1.1.361...1.1.362
[1.1.361]: https://github.com/IFRCGo/go-api/compare/1.1.360...1.1.361
[1.1.360]: https://github.com/IFRCGo/go-api/compare/1.1.359...1.1.360
[1.1.359]: https://github.com/IFRCGo/go-api/compare/1.1.358...1.1.359
[1.1.358]: https://github.com/IFRCGo/go-api/compare/1.1.356...1.1.358
[1.1.356]: https://github.com/IFRCGo/go-api/compare/1.1.355...1.1.356
[1.1.355]: https://github.com/IFRCGo/go-api/compare/1.1.354...1.1.355
[1.1.354]: https://github.com/IFRCGo/go-api/compare/1.1.353...1.1.354
[1.1.353]: https://github.com/IFRCGo/go-api/compare/1.1.352...1.1.353
[1.1.352]: https://github.com/IFRCGo/go-api/compare/1.1.351...1.1.352
[1.1.351]: https://github.com/IFRCGo/go-api/compare/1.1.350...1.1.351
[1.1.350]: https://github.com/IFRCGo/go-api/compare/1.1.349...1.1.350

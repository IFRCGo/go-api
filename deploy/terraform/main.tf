module "resources" {
  source = "./resources/"
  environment = var.environment
  subscriptionId = var.subscriptionId
  domain = var.domain
  additionalDomain = var.additionalDomain
  DJANGO_SECRET_KEY = var.DJANGO_SECRET_KEY
  DJANGO_DB_NAME = var.DJANGO_DB_NAME
  DJANGO_DB_USER = var.DJANGO_DB_USER
  DJANGO_DB_PASS = var.DJANGO_DB_PASS
  DJANGO_DB_HOST = var.DJANGO_DB_HOST
  DJANGO_DB_PORT = var.DJANGO_DB_PORT
  AZURE_STORAGE_ACCOUNT = var.AZURE_STORAGE_ACCOUNT
  AZURE_STORAGE_KEY = var.AZURE_STORAGE_KEY
  EMAIL_API_ENDPOINT = var.EMAIL_API_ENDPOINT
  EMAIL_HOST = var.EMAIL_HOST
  EMAIL_PORT = var.EMAIL_PORT
  EMAIL_USER = var.EMAIL_USER
  EMAIL_PASS = var.EMAIL_PASS
  TEST_EMAILS = var.TEST_EMAILS
  AWS_TRANSLATE_ACCESS_KEY = var.AWS_TRANSLATE_ACCESS_KEY
  AWS_TRANSLATE_SECRET_KEY = var.AWS_TRANSLATE_SECRET_KEY
  AWS_TRANSLATE_REGION = var.AWS_TRANSLATE_REGION
  CELERY_REDIS_URL = var.CELERY_REDIS_URL
  CACHE_MIDDLEWARE_SECONDS = var.CACHE_MIDDLEWARE_SECONDS
  MOLNIX_API_BASE = var.MOLNIX_API_BASE
  MOLNIX_USERNAME = var.MOLNIX_USERNAME
  MOLNIX_PASSWORD = var.MOLNIX_PASSWORD
  ERP_API_ENDPOINT = var.ERP_API_ENDPOINT
  ERP_API_SUBSCRIPTION_KEY = var.ERP_API_SUBSCRIPTION_KEY
  FDRS_APIKEY = var.FDRS_APIKEY
  FDRS_CREDENTIAL = var.FDRS_CREDENTIAL
  HPC_CREDENTIAL = var.HPC_CREDENTIAL
  APPLICATION_INSIGHTS_INSTRUMENTATION_KEY = var.APPLICATION_INSIGHTS_INSTRUMENTATION_KEY
  ELASTIC_SEARCH_HOST = var.ELASTIC_SEARCH_HOST
  GO_FTPHOST = var.GO_FTPHOST
  GO_FTPUSER = var.GO_FTPUSER
  GO_FTPPASS = var.GO_FTPPASS
  GO_DBPASS = var.GO_DBPASS
  APPEALS_USER = var.APPEALS_USER
  APPEALS_PASS = var.APPEALS_PASS
  DJANGO_DEBUG = var.DJANGO_DEBUG
  DOCKER_HOST_IP = var.DOCKER_HOST_IP
  DJANGO_ADDITIONAL_ALLOWED_HOSTS = var.DJANGO_ADDITIONAL_ALLOWED_HOSTS
  GO_ENVIRONMENT = var.GO_ENVIRONMENT
  API_FQDN = var.API_FQDN
  FRONTEND_URL = var.FRONTEND_URL
  DEBUG_EMAIL = var.DEBUG_EMAIL
  RESOURCES_DB_NAME = var.RESOURCES_DB_NAME
  RESOURCES_DB_SERVER = var.RESOURCES_DB_SERVER
  REGION = var.REGION
  SENTRY_DSN = var.SENTRY_DSN
  SENTRY_SAMPLE_RATE = var.SENTRY_SAMPLE_RATE
  DJANGO_READ_ONLY = var.DJANGO_READ_ONLY
  AUTO_TRANSLATION_TRANSLATOR = var.AUTO_TRANSLATION_TRANSLATOR
  IFRC_TRANSLATION_DOMAIN = var.IFRC_TRANSLATION_DOMAIN
  IFRC_TRANSLATION_GET_API_KEY = var.IFRC_TRANSLATION_GET_API_KEY
  IFRC_TRANSLATION_HEADER_API_KEY = var.IFRC_TRANSLATION_HEADER_API_KEY
}

terraform {
  backend "azurerm" {
    resource_group_name  = "ifrctgo002rg"
    storage_account_name = "ifrcgoterraform"
    container_name       = "terraform"
    # this is meant to be replaced in bin/deploy function so the correct environment is deployed
    key                  = "ENVIRONMENT_TO_REPLACE"
  }
}

output "resources" {
  value     = module.resources
  sensitive = true
}

variable "environment" {
  type = string
}

variable "subscriptionId" {
  type = string
}

variable "DJANGO_SECRET_KEY" {
  type = string
}

variable "DJANGO_DB_NAME" {
  type = string
}

variable "DJANGO_DB_USER" {
  type = string
}

variable "DJANGO_DB_PASS" {
  type = string
}

variable "DJANGO_DB_HOST" {
  type = string
}

variable "DJANGO_DB_PORT" {
  type = string
}

variable "AZURE_STORAGE_ACCOUNT" {
  type = string
}

variable "AZURE_STORAGE_KEY" {
  type = string
}

variable "EMAIL_API_ENDPOINT" {
  type = string
}

variable "EMAIL_HOST" {
  type = string
}

variable "EMAIL_PORT" {
  type = string
}

variable "EMAIL_USER" {
  type = string
}

variable "EMAIL_PASS" {
  type = string
}

variable "TEST_EMAILS" {
  type = string
}

variable "AWS_TRANSLATE_ACCESS_KEY" {
  type = string
}

variable "AWS_TRANSLATE_SECRET_KEY" {
  type = string
}

variable "AWS_TRANSLATE_REGION" {
  type = string
}

variable "CELERY_REDIS_URL" {
  type = string
}

variable "MOLNIX_API_BASE" {
  type = string
}

variable "MOLNIX_USERNAME" {
  type = string
}

variable "MOLNIX_PASSWORD" {
  type = string
}

variable "ERP_API_ENDPOINT" {
  type = string
}

variable "ERP_API_SUBSCRIPTION_KEY" {
  type = string
}

variable "FDRS_APIKEY" {
  type = string
}

variable "FDRS_CREDENTIAL" {
  type = string
}

variable "HPC_CREDENTIAL" {
  type = string
}

variable "APPLICATION_INSIGHTS_INSTRUMENTATION_KEY" {
  type = string
}

variable "ELASTIC_SEARCH_HOST" {
  type = string
}

variable "GO_FTPHOST" {
  type = string
}

variable "GO_FTPUSER" {
  type = string
}

variable "GO_FTPPASS" {
  type = string
}

variable "GO_DBPASS" {
  type = string
}

variable "DJANGO_DEBUG" {
  type = string
  default = "False"
}

variable "DOCKER_HOST_IP" {
  type = string
  default = ""
}

variable "DJANGO_ADDITIONAL_ALLOWED_HOSTS" {
  type = string
  default = ""
}

variable "GO_ENVIRONMENT" {
  type = string
  default = "development"
}

variable "API_FQDN" {
  type = string
  default = ""
}

variable "FRONTEND_URL" {
  type = string
  default = ""
}

variable "DEBUG_EMAIL" {
  type = string
  default = "sanjay@developmentseed.org"
}

# -----------------
# Attach ACR
# Defaults to common resources

variable "ifrcgo_test_resources_acr" {
  type    = string
  default = "ifrcgotest"
}

variable "ifrcgo_test_resources_rg" {
  type = string
  default = "ifrcgo_test"
}

variable "ifrcgo_test_resources_db_server" {
  type = string
  #FIXME create a test db server and provide here
  default = "ifrcgotest"
}

variable "ifrcgo_test_resources_db" {
  type = string
  default = "postgres"
}


module "resources" {
  source = "./resources/"
  environment = var.environment

  # DJANGO_SECRET_KEY = var.DJANGO_SECRET_KEY
  # DJANGO_DB_NAME = var.DJANGO_DB_NAME
  # DJANGO_DB_USER = var.DJANGO_DB_USER
  # DJANGO_DB_PASS = var.DJANGO_DB_PASS
  # DJANGO_DB_HOST = var.DJANGO_DB_HOST
  # DJANGO_DB_PORT = var.DJANGO_DB_PORT
  # AZURE_STORAGE_ACCOUNT = var.AZURE_STORAGE_ACCOUNT
  # AZURE_STORAGE_KEY = var.AZURE_STORAGE_KEY
  # EMAIL_API_ENDPOINT = var.EMAIL_API_ENDPOINT
  # EMAIL_HOST = var.EMAIL_HOST
  # EMAIL_PORT = var.EMAIL_PORT
  # EMAIL_USER = var.EMAIL_USER
  # EMAIL_PASS = var.EMAIL_PASS
  # TEST_EMAILS = var.TEST_EMAILS
  # AWS_TRANSLATE_ACCESS_KEY = var.AWS_TRANSLATE_ACCESS_KEY
  # AWS_TRANSLATE_SECRET_KEY = var.AWS_TRANSLATE_SECRET_KEY
  # AWS_TRANSLATE_REGION = var.AWS_TRANSLATE_REGION
  # CELERY_REDIS_URL = var.CELERY_REDIS_URL
  # MOLNIX_API_BASE = var.MOLNIX_API_BASE
  # MOLNIX_USERNAME = var.MOLNIX_USERNAME
  # # MOLNIX_PASSWORD = var.MOLNIX_PASSWORD
  # ERP_API_ENDPOINT = var.ERP_API_ENDPOINT
  # ERP_API_SUBSCRIPTION_KEY = var.ERP_API_SUBSCRIPTION_KEY
  # FDRS_APIKEY = var.FDRS_APIKEY
  # FDRS_CREDENTIAL = var.FDRS_CREDENTIAL
  # HPC_CREDENTIAL = var.HPC_CREDENTIAL
  # APPLICATION_INSIGHTS_INSTRUMENTATION_KEY = var.APPLICATION_INSIGHTS_INSTRUMENTATION_KEY
  # ELASTIC_SEARCH_HOST = var.ELASTIC_SEARCH_HOST
  # GO_FTPHOST = var.GO_FTPHOST
  # GO_FTPUSER = var.GO_FTPUSER
  # GO_FTPPASS = var.GO_FTPPASS
  # GO_DBPASS = var.GO_DBPASS
  # DJANGO_DEBUG = var.DJANGO_DEBUG
  # DOCKER_HOST_IP = var.DOCKER_HOST_IP
  # DJANGO_ADDITIONAL_ALLOWED_HOSTS = var.DJANGO_ADDITIONAL_ALLOWED_HOSTS
  # GO_ENVIRONMENT = var.GO_ENVIRONMENT
  # API_FQDN = var.API_FQDN
  # FRONTEND_URL = var.FRONTEND_URL
  # DEBUG_EMAIL = var.DEBUG_EMAIL
}

terraform {
  backend "azurerm" {
    resource_group_name  = "ifrcgoterraform"
    storage_account_name = "ifrcgo"
    container_name       = "terraform"
    key                  = "staging"
  }
}

output "resources" {
  value     = module.resources
  sensitive = true
}


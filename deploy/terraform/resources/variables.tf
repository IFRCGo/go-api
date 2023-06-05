variable "environment" {
  type = string
}

variable "subscriptionId" {
  type = string
}
variable "region" {
  type = string
default = "West Europe"
}

variable "domain" {
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

variable "CACHE_MIDDLEWARE_SECONDS" {
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

variable "APPEALS_USER" {
  type = string
}

variable "APPEALS_PASS" {
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

# Staging Resources
variable "ifrcgo_test_resources_acr" {
  type    = string
  default = "ifrcgoacr"
}

variable "ifrcgo_test_resources_rg" {
  type = string
  default = "ifrcpgoterraform001rg"
}

variable "ifrcgo_test_resources_db_server" {
  type = string
  default = "ifrctgokdb003"
}

variable "ifrcgo_test_resources_db" {
  type = string
  default = "postgres"
}

# Production Resources
variable "ifrcgo_prod_resources_acr" {
  type    = string
  default = "ifrcgoacr"
}

variable "ifrcgo_prod_resources_rg" {
  type = string
  default = "ifrcpgo002rg"
}

variable "ifrcgo_prod_resources_db_server" {
  type = string
  default = "ifrcpgokdb001"
}

variable "ifrcgo_prod_resources_db" {
  type = string
  default = "postgres"
}


# -----------------
# Local variables

locals {
  stack_id              = "ifrcgo"
  location              = lower(replace(var.region, " ", ""))
  prefix                = var.environment == "staging" ? "ifrctgo" : "ifrcpgo"
  # prefixnodashes        = "${local.stack_id}${var.environment}"
  storage               = "${local.prefix}"
  deploy_secrets_prefix = "${local.prefix}"
}

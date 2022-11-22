variable "environment" {
  type = string
}

variable "subscriptionId" {
  type = string
}

variable "domain" {
    type = string
    default = "api.ifrcgo.com"
}

variable "DJANGO_SECRET_KEY" {
  type = string
}

variable "DJANGO_DB_NAME" {
  type = string
  default = "postgres"
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

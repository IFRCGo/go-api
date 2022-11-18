variable "subscriptionId" {
  type = string
}

module "global_variables" {
    source = "../resources/variables.tf"
}

module "resources" {
  source = "../resources"

  environment          = "staging"
  subscriptionId       = var.subscriptionId
  region               = "West Europe"
  DJANGO_SECRET_KEY  = module.global_variables.var.DJANGO_SECRET_KEY
  DJANGO_DB_NAME  = module.global_variables.var.DJANGO_DB_NAME
  DJANGO_DB_USER  = module.global_variables.var.DJANGO_DB_USER
  DJANGO_DB_PASS  = module.global_variables.var.DJANGO_DB_PASS
  DJANGO_DB_HOST  = module.global_variables.var.DJANGO_DB_HOST
  DJANGO_DB_PORT  = module.global_variables.var.DJANGO_DB_PORT
  AZURE_STORAGE_ACCOUNT  = module.global_variables.var.AZURE_STORAGE_ACCOUNT
  AZURE_STORAGE_KEY  = module.global_variables.var.AZURE_STORAGE_KEY
  EMAIL_API_ENDPOINT  = module.global_variables.var.EMAIL_API_ENDPOINT
  EMAIL_HOST  = module.global_variables.var.EMAIL_HOST
  EMAIL_PORT  = module.global_variables.var.EMAIL_PORT
  EMAIL_USER  = module.global_variables.var.EMAIL_USER
  EMAIL_PASS  = module.global_variables.var.EMAIL_PASS
  TEST_EMAILS  = module.global_variables.var.TEST_EMAILS
  AWS_TRANSLATE_ACCESS_KEY  = module.global_variables.var.AWS_TRANSLATE_ACCESS_KEY
  AWS_TRANSLATE_SECRET_KEY  = module.global_variables.var.AWS_TRANSLATE_SECRET_KEY
  AWS_TRANSLATE_REGION  = module.global_variables.var.AWS_TRANSLATE_REGION
  CELERY_REDIS_URL  = module.global_variables.var.CELERY_REDIS_URL
  MOLNIX_API_BASE  = module.global_variables.var.MOLNIX_API_BASE
  MOLNIX_USERNAME  = module.global_variables.var.MOLNIX_USERNAME
  MOLNIX_PASSWORD  = module.global_variables.var.MOLNIX_PASSWORD
  ERP_API_ENDPOINT  = module.global_variables.var.ERP_API_ENDPOINT
  ERP_API_SUBSCRIPTION_KEY  = module.global_variables.var.ERP_API_SUBSCRIPTION_KEY
  FDRS_APIKEY  = module.global_variables.var.FDRS_APIKEY
  FDRS_CREDENTIAL  = module.global_variables.var.FDRS_CREDENTIAL
  HPC_CREDENTIAL  = module.global_variables.var.HPC_CREDENTIAL
  APPLICATION_INSIGHTS_INSTRUMENTATION_KEY  = module.global_variables.var.APPLICATION_INSIGHTS_INSTRUMENTATION_KEY
  ELASTIC_SEARCH_HOST  = module.global_variables.var.ELASTIC_SEARCH_HOST
  GO_FTPHOST  = module.global_variables.var.GO_FTPHOST
  GO_FTPUSER  = module.global_variables.var.GO_FTPUSER
  GO_FTPPASS  = module.global_variables.var.GO_FTPPASS
  GO_DBPASS  = module.global_variables.var.GO_DBPASS
  DJANGO_DEBUG  = module.global_variables.var.DJANGO_DEBUG
  DOCKER_HOST_IP  = module.global_variables.var.DOCKER_HOST_IP
  DJANGO_ADDITIONAL_ALLOWED_HOSTS  = module.global_variables.var.DJANGO_ADDITIONAL_ALLOWED_HOSTS
  GO_ENVIRONMENT  = module.global_variables.var.GO_ENVIRONMENT
  API_FQDN  = module.global_variables.var.API_FQDN
  FRONTEND_URL  = module.global_variables.var.FRONTEND_URL
  DEBUG_EMAIL  = module.global_variables.var.DEBUG_EMAIL

  admin_email          = "sanjay@developmentseed.org"
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


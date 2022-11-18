var "subscriptionId" {
  type = string
}

module "resources" {
  source = "../resources"

  environment          = "staging"
  subscriptionId       = var.subscriptionId
  region               = "West Europe"
  DJANGO_SECRET_KEY  = module.resources.var.DJANGO_SECRET_KEY
  DJANGO_DB_NAME  = module.resources.var.DJANGO_DB_NAME
  DJANGO_DB_USER  = module.resources.var.DJANGO_DB_USER
  DJANGO_DB_PASS  = module.resources.var.DJANGO_DB_PASS
  DJANGO_DB_HOST  = module.resources.var.DJANGO_DB_HOST
  DJANGO_DB_PORT  = module.resources.var.DJANGO_DB_PORT
  AZURE_STORAGE_ACCOUNT  = module.resources.var.AZURE_STORAGE_ACCOUNT
  AZURE_STORAGE_KEY  = module.resources.var.AZURE_STORAGE_KEY
  EMAIL_API_ENDPOINT  = module.resources.var.EMAIL_API_ENDPOINT
  EMAIL_HOST  = module.resources.var.EMAIL_HOST
  EMAIL_PORT  = module.resources.var.EMAIL_PORT
  EMAIL_USER  = module.resources.var.EMAIL_USER
  EMAIL_PASS  = module.resources.var.EMAIL_PASS
  TEST_EMAILS  = module.resources.var.TEST_EMAILS
  AWS_TRANSLATE_ACCESS_KEY  = module.resources.var.AWS_TRANSLATE_ACCESS_KEY
  AWS_TRANSLATE_SECRET_KEY  = module.resources.var.AWS_TRANSLATE_SECRET_KEY
  AWS_TRANSLATE_REGION  = module.resources.var.AWS_TRANSLATE_REGION
  CELERY_REDIS_URL  = module.resources.var.CELERY_REDIS_URL
  MOLNIX_API_BASE  = module.resources.var.MOLNIX_API_BASE
  MOLNIX_USERNAME  = module.resources.var.MOLNIX_USERNAME
  MOLNIX_PASSWORD  = module.resources.var.MOLNIX_PASSWORD
  ERP_API_ENDPOINT  = module.resources.var.ERP_API_ENDPOINT
  ERP_API_SUBSCRIPTION_KEY  = module.resources.var.ERP_API_SUBSCRIPTION_KEY
  FDRS_APIKEY  = module.resources.var.FDRS_APIKEY
  FDRS_CREDENTIAL  = module.resources.var.FDRS_CREDENTIAL
  HPC_CREDENTIAL  = module.resources.var.HPC_CREDENTIAL
  APPLICATION_INSIGHTS_INSTRUMENTATION_KEY  = module.resources.var.APPLICATION_INSIGHTS_INSTRUMENTATION_KEY
  ELASTIC_SEARCH_HOST  = module.resources.var.ELASTIC_SEARCH_HOST
  GO_FTPHOST  = module.resources.var.GO_FTPHOST
  GO_FTPUSER  = module.resources.var.GO_FTPUSER
  GO_FTPPASS  = module.resources.var.GO_FTPPASS
  GO_DBPASS  = module.resources.var.GO_DBPASS
  DJANGO_DEBUG  = module.resources.var.DJANGO_DEBUG
  DOCKER_HOST_IP  = module.resources.var.DOCKER_HOST_IP
  DJANGO_ADDITIONAL_ALLOWED_HOSTS  = module.resources.var.DJANGO_ADDITIONAL_ALLOWED_HOSTS
  GO_ENVIRONMENT  = module.resources.var.GO_ENVIRONMENT
  API_FQDN  = module.resources.var.API_FQDN
  FRONTEND_URL  = module.resources.var.FRONTEND_URL
  DEBUG_EMAIL  = module.resources.var.DEBUG_EMAIL

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


variable "environment" {
  type = string
}
variable "region" {
  type = string
default = "West Europe"
}

# variable "domain" {
#   type = string
#   default = ""
# }

# variable "admin_email" {
#   type = string
#   default = "sanjay@developmentseed.org"
# }


# variable "subscriptionId" {
#   type = string
# }

# variable "DJANGO_SECRET_KEY" {
#   type = string
# }

# variable "DJANGO_DB_NAME" {
#   type = string
# }

# variable "DJANGO_DB_USER" {
#   type = string
# }

# variable "DJANGO_DB_PASS" {
#   type = string
# }

# variable "DJANGO_DB_HOST" {
#   type = string
# }

# variable "DJANGO_DB_PORT" {
#   type = string
# }

# variable "AZURE_STORAGE_ACCOUNT" {
#   type = string
# }

# variable "AZURE_STORAGE_KEY" {
#   type = string
# }

# variable "EMAIL_API_ENDPOINT" {
#   type = string
# }

# variable "EMAIL_HOST" {
#   type = string
# }

# variable "EMAIL_PORT" {
#   type = string
# }

# variable "EMAIL_USER" {
#   type = string
# }

# variable "EMAIL_PASS" {
#   type = string
# }

# variable "TEST_EMAILS" {
#   type = string
# }

# variable "AWS_TRANSLATE_ACCESS_KEY" {
#   type = string
# }

# variable "AWS_TRANSLATE_SECRET_KEY" {
#   type = string
# }

# variable "AWS_TRANSLATE_REGION" {
#   type = string
# }

# variable "CELERY_REDIS_URL" {
#   type = string
# }

# variable "MOLNIX_API_BASE" {
#   type = string
# }

# variable "MOLNIX_USERNAME" {
#   type = string
# }

# variable "MOLNIX_PASSWORD" {
#   type = string
# }

# variable "ERP_API_ENDPOINT" {
#   type = string
# }

# variable "ERP_API_SUBSCRIPTION_KEY" {
#   type = string
# }

# variable "FDRS_APIKEY" {
#   type = string
# }

# variable "FDRS_CREDENTIAL" {
#   type = string
# }

# variable "HPC_CREDENTIAL" {
#   type = string
# }

# variable "APPLICATION_INSIGHTS_INSTRUMENTATION_KEY" {
#   type = string
# }

# variable "ELASTIC_SEARCH_HOST" {
#   type = string
# }

# variable "GO_FTPHOST" {
#   type = string
# }

# variable "GO_FTPUSER" {
#   type = string
# }

# variable "GO_FTPPASS" {
#   type = string
# }

# variable "GO_DBPASS" {
#   type = string
# }

# variable "DJANGO_DEBUG" {
#   type = string
# }

# variable "DOCKER_HOST_IP" {
#   type = string
# }

# variable "DJANGO_ADDITIONAL_ALLOWED_HOSTS" {
#   type = string
# }

# variable "GO_ENVIRONMENT" {
#   type = string
# }

# variable "API_FQDN" {
#   type = string
# }

# variable "FRONTEND_URL" {
#   type = string
# }

# variable "DEBUG_EMAIL" {
#   type = string
# }


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

# -----------------
# Local variables

locals {
  stack_id              = "ifrcgo"
  location              = lower(replace(var.region, " ", ""))
  prefix                = "${local.stack_id}-${var.environment}"
  prefixnodashes        = "${local.stack_id}${var.environment}"
  storage               = (var.environment == "production" ? "${local.stack_id}tf${var.environment}" : "${local.stack_id}${var.environment}")
  deploy_secrets_prefix = "${local.stack_id}-${var.environment}"
}
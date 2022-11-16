variable "environment" {
  type = string
}

variable "domain" {
  type = string
  default = ""
}

variable "admin_email" {
  type = string
}

variable "region" {
  type = string
}

variable "subscriptionId" {
  type = string
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
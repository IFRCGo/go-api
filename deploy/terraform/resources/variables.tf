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
  #FIXME create an ACR and provide the name here
  default = ""
}

variable "ifrcgo_test_resources_rg" {
  type = string
  #FIXME create a test resource group and provide here
  default = ""
}

variable "ifrcgo_test_resources_db_server" {
  type = string
  #FIXME create a test db server and provide here
  default = ""
}

variable "ifrcgo_test_resources_db" {
  type = string
  #FIXME create a test db and provide here
  default = ""
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
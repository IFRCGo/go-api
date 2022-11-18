module "resources" {
  source = "../resources"

  environment          = "staging"
#   subscriptionId       = var.subscriptionId
  region               = "West Europe"

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


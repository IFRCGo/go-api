variable "subscriptionId" {
  type = string
}

module "resources" {
  source = "../resources"

  environment          = "staging"
  subscriptionId       = var.subscriptionId
  region               = "West Europe"
  aks_node_count       = 1

  admin_email          = "sanjay@developmentseed.org"
}

terraform {
  #FIXME provide resource groups and other details to store tf state
  backend "azurerm" {
    resource_group_name  = ""
    storage_account_name = ""
    container_name       = ""
    key                  = ""
  }
}

output "resources" {
  value     = module.resources
  sensitive = true
}


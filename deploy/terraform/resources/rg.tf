resource "azurerm_resource_group" "ifrcgo" {
  name     = "${local.prefix}_rg"
  location = var.region
}
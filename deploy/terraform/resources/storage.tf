resource "azurerm_storage_account" "ifrcgo" {
  name                     = "${local.storage}"
  resource_group_name      = azurerm_resource_group.ifrcgo.name
  location                 = azurerm_resource_group.ifrcgo.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# FIXME: not sure if data is the name of the container needed
resource "azurerm_storage_container" "data" {
  name                  = "data"
  storage_account_name  = azurerm_storage_account.ifrcgo.name
  container_access_type = "private"
}

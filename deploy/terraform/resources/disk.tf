resource "azurerm_managed_disk" "ifrcgo" {
  name                 = "${local.prefix}-disk001"
  resource_group_name      = data.azurerm_resource_group.ifrcgo.name
  location                 = data.azurerm_resource_group.ifrcgo.location
  storage_account_type = "StandardSSD_LRS"
  create_option        = "Empty"
  disk_size_gb         = "20"
}

resource "azurerm_role_assignment" "disk" {
  scope                = azurerm_managed_disk.ifrcgo.id
  # scope = "/subscriptions/39308fb0-9929-4b29-aafa-b3c78a8b0658/resourceGroups/${azurerm_kubernetes_cluster.ifrcgo.node_resource_group}"
  role_definition_name = "Storage Account Contributor"
  principal_id         = azurerm_kubernetes_cluster.ifrcgo.identity[0].principal_id
}
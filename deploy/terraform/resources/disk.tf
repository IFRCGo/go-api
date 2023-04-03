resource "azurerm_managed_disk" "ifrcgo" {
  name                 = "${local.prefix}-disk001"
  resource_group_name      = azurerm_kubernetes_cluster.ifrcgo.node_resource_group
  location                 = data.azurerm_resource_group.ifrcgo.location
  storage_account_type = "StandardSSD_LRS"
  create_option        = "Empty"
  disk_size_gb         = "20"
}
data "azurerm_container_registry" "ifrcgo" {
  # we'll use the common resource group and ACR for staging and prod
  name                = var.ifrcgo_test_resources_acr
  resource_group_name = var.ifrcgo_test_resources_rg
}

# add the role to the identity the kubernetes cluster was assigned
resource "azurerm_role_assignment" "attach_acr" {
  scope                = data.azurerm_container_registry.ifrcgo.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.ifrcgo.kubelet_identity[0].object_id
}
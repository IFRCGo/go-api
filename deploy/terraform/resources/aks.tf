resource "azurerm_kubernetes_cluster" "ifrcgo" {
  lifecycle {
    ignore_changes = all
  }
  name                = "${local.prefix}-cluster"
  location            = data.azurerm_resource_group.ifrcgo.location
  resource_group_name = data.azurerm_resource_group.ifrcgo.name
  dns_prefix          = "${local.prefix}-cluster"
  kubernetes_version  = "1.25.5"

  default_node_pool {
    name           = "nodepool1"
    vm_size        = "Standard_DS2_v2"
    vnet_subnet_id = azurerm_subnet.aks.id
    enable_auto_scaling   = true
    min_count             = 1
    max_count             = 4
  }

  identity {
    type = "SystemAssigned"
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "IFRCGo"
  }
}

# add the role to the identity the kubernetes cluster was assigned
resource "azurerm_role_assignment" "network" {
  scope                = data.azurerm_resource_group.ifrcgo.id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_kubernetes_cluster.ifrcgo.identity[0].principal_id
}
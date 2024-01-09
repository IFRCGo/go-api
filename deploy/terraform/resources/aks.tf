resource "azurerm_kubernetes_cluster" "ifrcgo" {
  lifecycle {
    ignore_changes = all
  }
  
  name                = "${local.prefix}-cluster"
  location            = data.azurerm_resource_group.ifrcgo.location
  resource_group_name = data.azurerm_resource_group.ifrcgo.name
  dns_prefix          = "${local.prefix}-cluster"
  kubernetes_version  = "1.28.3"

  default_node_pool {
    name           = "nodepool1"
    vm_size        = "Standard_DS3_v2"
    vnet_subnet_id = azurerm_subnet.aks.id
    enable_auto_scaling   = true
    min_count             = 1
    max_count             = 5
    temporary_name_for_rotation = "nodepooltemp"
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

resource "azurerm_role_assignment" "storage" {
  scope                = data.azurerm_resource_group.ifrcgo.id
  role_definition_name = "Storage Account Contributor"
  principal_id         = azurerm_kubernetes_cluster.ifrcgo.identity[0].principal_id
}

# create k8s configmaps and secrets

provider "kubernetes" {
  host                   = azurerm_kubernetes_cluster.ifrcgo.kube_config.0.host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.ifrcgo.kube_config.0.client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.ifrcgo.kube_config.0.client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.ifrcgo.kube_config.0.cluster_ca_certificate)
}

# This ConfigMap stores configurations for resources created by Terraform which 
# are later referenced in the go-api Helm chart. Values from this ConfigMap
# are either directly utilized in Kubernetes resource definitions or provided
# as parameters to the Helm chart.
resource "kubernetes_config_map" "ifrcgo_terraform_managed_resources" {
  metadata {
    name = "ifrcgo-terraform-managed-resources"
  }

  depends_on = [
    azurerm_managed_disk.ifrcgo
  ]

  data = {
    "elasticsearch_disk_name" = "${local.prefix}-disk"
    "elasticsearch_disk_uri"  = azurerm_managed_disk.ifrcgo.id
  }
}

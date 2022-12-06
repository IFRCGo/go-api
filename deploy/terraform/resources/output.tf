output "environment" {
    value = var.environment
}

output "location" {
    value = local.location
}

output "cluster_name" {
  value = azurerm_kubernetes_cluster.ifrcgo.name
}

output "resource_group" {
  value = azurerm_resource_group.ifrcgo.name
}

output "image_registry" {
  value = data.azurerm_container_registry.ifrcgo.name
}

output "azure_storage_name" {
  value = azurerm_storage_account.ifrcgo.id
}

output "azure_strorage_key" {
  value = azurerm_storage_account.ifrcgo.primary_access_key
}

output "azure_storage_connection_string" {
  value = azurerm_storage_account.ifrcgo.primary_connection_string
}

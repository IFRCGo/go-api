resource "azurerm_virtual_network" "ifrcgo-cluster" {
  name                = "${local.prefix}-cluster-network"
  location            = data.azurerm_resource_group.ifrcgo.location
  resource_group_name = data.azurerm_resource_group.ifrcgo.name
  address_space       = ["10.0.0.0/8"]
}

# subnet for node pools
resource "azurerm_subnet" "aks" {
  name                 = "${local.prefix}-aks-subnet"
  virtual_network_name = azurerm_virtual_network.ifrcgo-cluster.name
  resource_group_name  = data.azurerm_resource_group.ifrcgo.name
  address_prefixes     = ["10.1.0.0/16"]
}

# subnet for postgres that's delegated
resource "azurerm_subnet" "postgres" {
  name                 = "${local.prefix}-postgres-subnet"
  virtual_network_name = azurerm_virtual_network.ifrcgo-cluster.name
  resource_group_name  = data.azurerm_resource_group.ifrcgo.name
  address_prefixes     = ["10.2.0.0/16"]
  service_endpoints = [
    "Microsoft.Storage"
  ]
  delegation {
    name = "delegation"

    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
      ]
    }
  }
}

resource "azurerm_private_dns_zone" "ifrcgo" {
  name                = "${local.prefix}.postgres.database.azure.com"
  resource_group_name = data.azurerm_resource_group.ifrcgo.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "ifrcgo" {
  name                  = "${local.prefix}.postgres.database.azure.com"
  private_dns_zone_name = azurerm_private_dns_zone.ifrcgo.name
  virtual_network_id    = azurerm_virtual_network.ifrcgo-cluster.id
  resource_group_name   = data.azurerm_resource_group.ifrcgo.name
}

resource "azurerm_public_ip" "ifrcgo" {
  lifecycle {
    ignore_changes = all
  }
  name                = "${local.prefix}PublicIP"
  resource_group_name = data.azurerm_resource_group.ifrcgo.name
  location            = data.azurerm_resource_group.ifrcgo.location
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = {
    Environment = var.environment
  }
}
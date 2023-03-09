resource "azurerm_public_ip" "ifrcgo" {
  lifecycle {
    ignore_changes = all
  }
  name                = "${local.prefix}PublicIP"
  resource_group_name = azurerm_resource_group.ifrcgo.name
  location            = azurerm_resource_group.ifrcgo.location
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = {
    Environment = var.environment
  }
}
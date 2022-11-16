data "azurerm_postgresql_flexible_server" "ifrcgo" {
  name                   = var.ifrcgo_test_resources_db_server
  resource_group_name    = var.ifrcgo_test_resources_rg
}

data "azurerm_postgresql_flexible_server" "ifrcgo" {
  name                   = var.ifrcgo_test_resources_db_server
  resource_group_name    = var.ifrcgo_test_resources_rg
}

data "azurerm_postgresql_flexible_server_database" "lulc" {
  name      = var.ifrcgo_test_resources_db
  server_id = azurerm_postgresql_flexible_server.ifrcgo.id
  collation = "en_US.utf8"
  charset   = "utf8"
}
# resource "helm_release" "ifrcgo" {
#   name  = "ifrcgo-helm"
#   chart = "../../helm/ifrcgo-helm"
#   wait = false
#   depends_on = [
#     helm_release.ifrcgo-ingress-nginx,
#     helm_release.ifrcgo-cert-manager
#   ]
#   set {
#     name  = "environment"
#     value = var.environment
#   }

#   set {
#     name  = "domain"
#     value = var.domain
#   }

#   set {
#     name  = "api.postgresUrl"
#     value = "postgres://ifrcgo:${var.postgres_password}@${azurerm_postgresql_flexible_server.ifrcgo.fqdn}/ifrcgo?sslmode=require"
#   }

# }

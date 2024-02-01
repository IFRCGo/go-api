resource "helm_release" "ifrcgo-cert-manager" {
  lifecycle {
    ignore_changes = all
  }

  name             = "cert-manager"
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  version          = "v1.6.1"
  namespace        = "cert-manager"
  create_namespace = true

  set {
    name  = "installCRDs"
    value = true
  }
}

resource "helm_release" "ifrcgo-loki-stack" {
  name             = "loki-stack"
  repository       = "https://grafana.github.io/helm-charts"
  chart            = "loki-stack"
  namespace        = "loki-stack"
  create_namespace = true

  set {
    name  = "promtail.enabled"
    value = "true"
  }

  set {
    name  = "prometheus.enabled"
    value = "true"
  }

  set {
    name  = "loki.persistence.enabled"
    value = "true"
  }

  set {
    name  = "loki.persistence.size"
    value = "20Gi"
  }

  set {
    name  = "grafana.enabled"
    value = "true"
  }

}
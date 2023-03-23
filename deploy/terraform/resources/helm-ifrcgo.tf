resource "helm_release" "ifrcgo" {
  name  = "ifrcgo-helm"
  chart = "../helm/ifrcgo-helm"
  wait = false
  depends_on = [
    helm_release.ifrcgo-ingress-nginx,
    helm_release.ifrcgo-cert-manager
  ]
  set {
    name  = "environment"
    value = var.environment
  }

  set {
    name  = "api.domain"
    value = var.domain
  }

  set {
    name = "env.DJANGO_SECRET_KEY"
    value = var.DJANGO_SECRET_KEY
  }

  set {
    name = "env.DJANGO_DB_NAME"
    value = var.DJANGO_DB_NAME
  }

  set {
    name = "env.DJANGO_DB_USER"
    value = var.DJANGO_DB_USER
  }

  set {
    name = "env.DJANGO_DB_PASS"
    value = var.DJANGO_DB_PASS
  }

  set {
    name = "env.DJANGO_DB_HOST"
    value = var.DJANGO_DB_HOST
  }

  set {
    name = "env.DJANGO_DB_PORT"
    value = var.DJANGO_DB_PORT
  }

  set {
    name = "env.AZURE_STORAGE_ACCOUNT"
    value = azurerm_storage_account.ifrcgo.id
  }

  set {
    name = "env.AZURE_STORAGE_KEY"
    value = azurerm_storage_account.ifrcgo.primary_access_key
  }

  set {
    name = "env.EMAIL_API_ENDPOINT"
    value = var.EMAIL_API_ENDPOINT
  }

  set {
    name = "env.EMAIL_HOST"
    value = var.EMAIL_HOST
  }

  set {
    name = "env.EMAIL_PORT"
    value = var.EMAIL_PORT
  }

  set {
    name = "env.EMAIL_USER"
    value = var.EMAIL_USER
  }

  set {
    name = "env.EMAIL_PASS"
    value = var.EMAIL_PASS
  }

  set {
    name = "env.TEST_EMAILS"
    value = var.TEST_EMAILS
  }

  set {
    name = "env.AWS_TRANSLATE_ACCESS_KEY"
    value = var.AWS_TRANSLATE_ACCESS_KEY
  }

  set {
    name = "env.AWS_TRANSLATE_SECRET_KEY"
    value = var.AWS_TRANSLATE_SECRET_KEY
  }

  set {
    name = "env.AWS_TRANSLATE_REGION"
    value = var.AWS_TRANSLATE_REGION
  }

  set {
    name = "env.CELERY_REDIS_URL"
    value = var.CELERY_REDIS_URL
  }

  set {
    name = "env.MOLNIX_API_BASE"
    value = var.MOLNIX_API_BASE
  }

  set {
    name = "env.MOLNIX_USERNAME"
    value = var.MOLNIX_USERNAME
  }

  set {
    name = "env.MOLNIX_PASSWORD"
    value = var.MOLNIX_PASSWORD
  }

  set {
    name = "env.ERP_API_ENDPOINT"
    value = var.ERP_API_ENDPOINT
  }

  set {
    name = "env.ERP_API_SUBSCRIPTION_KEY"
    value = var.ERP_API_SUBSCRIPTION_KEY
  }

  set {
    name = "env.FDRS_APIKEY"
    value = var.FDRS_APIKEY
  }

  set {
    name = "env.FDRS_CREDENTIAL"
    value = var.FDRS_CREDENTIAL
  }

  set {
    name = "env.HPC_CREDENTIAL"
    value = var.HPC_CREDENTIAL
  }

  set {
    name = "env.APPLICATION_INSIGHTS_INSTRUMENTATION_KEY"
    value = var.APPLICATION_INSIGHTS_INSTRUMENTATION_KEY
  }

  set {
    name = "env.ELASTIC_SEARCH_HOST"
    value = var.ELASTIC_SEARCH_HOST
  }

  set {
    name = "env.GO_FTPHOST"
    value = var.GO_FTPHOST
  }

  set {
    name = "env.GO_FTPUSER"
    value = var.GO_FTPUSER
  }

  set {
    name = "env.GO_FTPPASS"
    value = var.GO_FTPPASS
  }

  set {
    name = "env.GO_DBPASS"
    value = var.GO_DBPASS
  }

  set {
    name = "env.DJANGO_DEBUG"
    value = var.DJANGO_DEBUG
  }

  set {
    name = "env.DOCKER_HOST_IP"
    value = var.DOCKER_HOST_IP
  }

  set {
    name = "env.DJANGO_ADDITIONAL_ALLOWED_HOSTS"
    value = var.DJANGO_ADDITIONAL_ALLOWED_HOSTS
  }

  set {
    name = "env.GO_ENVIRONMENT"
    value = var.GO_ENVIRONMENT
  }

  set {
    name = "env.API_FQDN"
    value = var.API_FQDN
  }

  set {
    name = "env.FRONTEND_URL"
    value = var.FRONTEND_URL
  }

  set {
    name = "env.DEBUG_EMAIL"
    value = var.DEBUG_EMAIL
  }

  set {
    name  = "elasticsearch.disk.name"
    value = "${local.prefix}-disk"
  }
  set {
    name  = "elasticsearch.disk.uri"
    value = "/subscriptions/${var.subscriptionId}/resourceGroups/${azurerm_resource_group.ifrcgo.name}/providers/Microsoft.Compute/disks/${azurerm_managed_disk.ifrcgo.id}"
  }
}

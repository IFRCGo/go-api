resource "helm_release" "ifrcgo" {
  name  = "ifrcgo-helm"
  chart = "../helm/ifrcgo-helm"
  wait = false
  depends_on = [
  #  helm_release.ifrcgo-ingress-nginx,
  #  helm_release.ifrcgo-cert-manager
  ]
  set {
    name  = "environment"
    value = var.environment
  }

  set {
    name  = "domain"
    value = var.domain
  }

  set {
    name = "DJANGO_SECRET_KEY"
    value = var.DJANGO_SECRET_KEY
  }

  set {
    name = "DJANGO_DB_NAME"
    value = var.DJANGO_DB_NAME
  }

  set {
    name = "DJANGO_DB_USER"
    value = var.DJANGO_DB_USER
  }

  set {
    name = "DJANGO_DB_PASS"
    value = var.DJANGO_DB_PASS
  }

  set {
    name = "DJANGO_DB_HOST"
    value = var.DJANGO_DB_HOST
  }

  set {
    name = "DJANGO_DB_PORT"
    value = var.DJANGO_DB_PORT
  }

  set {
    name = "AZURE_STORAGE_ACCOUNT"
    value = var.AZURE_STORAGE_ACCOUNT
  }

  set {
    name = "AZURE_STORAGE_KEY"
    value = var.AZURE_STORAGE_KEY
  }

  set {
    name = "EMAIL_API_ENDPOINT"
    value = var.EMAIL_API_ENDPOINT
  }

  set {
    name = "EMAIL_HOST"
    value = var.EMAIL_HOST
  }

  set {
    name = "EMAIL_PORT"
    value = var.EMAIL_PORT
  }

  set {
    name = "EMAIL_USER"
    value = var.EMAIL_USER
  }

  set {
    name = "EMAIL_PASS"
    value = var.EMAIL_PASS
  }

  set {
    name = "TEST_EMAILS"
    value = var.TEST_EMAILS
  }

  set {
    name = "AWS_TRANSLATE_ACCESS_KEY"
    value = var.AWS_TRANSLATE_ACCESS_KEY
  }

  set {
    name = "AWS_TRANSLATE_SECRET_KEY"
    value = var.AWS_TRANSLATE_SECRET_KEY
  }

  set {
    name = "AWS_TRANSLATE_REGION"
    value = var.AWS_TRANSLATE_REGION
  }

  set {
    name = "CELERY_REDIS_URL"
    value = var.CELERY_REDIS_URL
  }

  set {
    name = "MOLNIX_API_BASE"
    value = var.MOLNIX_API_BASE
  }

  set {
    name = "MOLNIX_USERNAME"
    value = var.MOLNIX_USERNAME
  }

  set {
    name = "MOLNIX_PASSWORD"
    value = var.MOLNIX_PASSWORD
  }

  set {
    name = "ERP_API_ENDPOINT"
    value = var.ERP_API_ENDPOINT
  }

  set {
    name = "ERP_API_SUBSCRIPTION_KEY"
    value = var.ERP_API_SUBSCRIPTION_KEY
  }

  set {
    name = "FDRS_APIKEY"
    value = var.FDRS_APIKEY
  }

  set {
    name = "FDRS_CREDENTIAL"
    value = var.FDRS_CREDENTIAL
  }

  set {
    name = "HPC_CREDENTIAL"
    value = var.HPC_CREDENTIAL
  }

  set {
    name = "APPLICATION_INSIGHTS_INSTRUMENTATION_KEY"
    value = var.APPLICATION_INSIGHTS_INSTRUMENTATION_KEY
  }

  set {
    name = "ELASTIC_SEARCH_HOST"
    value = var.ELASTIC_SEARCH_HOST
  }

  set {
    name = "GO_FTPHOST"
    value = var.GO_FTPHOST
  }

  set {
    name = "GO_FTPUSER"
    value = var.GO_FTPUSER
  }

  set {
    name = "GO_FTPPASS"
    value = var.GO_FTPPASS
  }

  set {
    name = "GO_DBPASS"
    value = var.GO_DBPASS
  }

  set {
    name = "DJANGO_DEBUG"
    value = var.DJANGO_DEBUG
  }

  set {
    name = "DOCKER_HOST_IP"
    value = var.DOCKER_HOST_IP
  }

  set {
    name = "DJANGO_ADDITIONAL_ALLOWED_HOSTS"
    value = var.DJANGO_ADDITIONAL_ALLOWED_HOSTS
  }

  set {
    name = "GO_ENVIRONMENT"
    value = var.GO_ENVIRONMENT
  }

  set {
    name = "API_FQDN"
    value = var.API_FQDN
  }

  set {
    name = "FRONTEND_URL"
    value = var.FRONTEND_URL
  }

  set {
    name = "DEBUG_EMAIL"
    value = var.DEBUG_EMAIL
  }

}

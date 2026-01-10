# ArgoCD Applications
# Deploy applications using ArgoCD

locals {
  argocd_apps_path = "${path.module}/argocd-applications"

  # Common template variables passed to all applications
  template_vars = {
    kafka_nodeport      = var.kafka_nodeport
    https_nodeport      = var.https_nodeport
    mgmt_https_nodeport = var.mgmt_https_nodeport
    gateway_dns_suffix  = var.gateway_dns_suffix
  }
}

# Deploy infrastructure applications
resource "kubectl_manifest" "infrastructure_applications" {
  for_each = fileset(local.argocd_apps_path, "infrastructure/*.yaml")

  yaml_body = templatefile("${local.argocd_apps_path}/${each.value}", local.template_vars)

  depends_on = [
    helm_release.argocd,
    kubectl_manifest.argocd_projects
  ]
}

# Deploy application applications (depends on infrastructure)
resource "kubectl_manifest" "application_applications" {
  for_each = fileset(local.argocd_apps_path, "applications/*.yaml")

  yaml_body = templatefile("${local.argocd_apps_path}/${each.value}", local.template_vars)

  depends_on = [
    kubectl_manifest.infrastructure_applications
  ]
}

# Deploy middleware applications (depends on applications)
resource "kubectl_manifest" "middleware_applications" {
  for_each = fileset(local.argocd_apps_path, "middleware/*.yaml")

  yaml_body = templatefile("${local.argocd_apps_path}/${each.value}", local.template_vars)

  depends_on = [
    kubectl_manifest.application_applications
  ]
}

# Deploy observability applications (depends on middleware)
resource "kubectl_manifest" "observability_applications" {
  for_each = fileset(local.argocd_apps_path, "observability/*.yaml")

  yaml_body = templatefile("${local.argocd_apps_path}/${each.value}", local.template_vars)

  depends_on = [
    kubectl_manifest.middleware_applications
  ]
}

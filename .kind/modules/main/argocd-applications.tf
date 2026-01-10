# ArgoCD Applications
# Deploy applications using ArgoCD

locals {
  argocd_apps_path = "${path.module}/argocd-applications"
}

# Deploy gateway application with templated NodePort values
resource "kubectl_manifest" "gateway_application" {
  yaml_body = templatefile("${local.argocd_apps_path}/infrastructure/gateway.yaml", {
    kafka_nodeport      = var.kafka_nodeport
    https_nodeport      = var.https_nodeport
    mgmt_https_nodeport = var.mgmt_https_nodeport
    gateway_dns_suffix  = var.gateway_dns_suffix
  })

  depends_on = [
    helm_release.argocd,
    kubectl_manifest.argocd_projects
  ]
}

# Deploy all other ArgoCD Application manifests (excluding gateway which is templated)
resource "kubectl_manifest" "argocd_applications" {
  for_each = setsubtract(fileset(local.argocd_apps_path, "**/*.yaml"), ["infrastructure/gateway.yaml"])

  yaml_body = file("${local.argocd_apps_path}/${each.value}")

  depends_on = [
    helm_release.argocd,
    kubectl_manifest.argocd_projects
  ]
}

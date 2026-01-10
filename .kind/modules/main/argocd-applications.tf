# ArgoCD Applications
# Deploy applications using ArgoCD

locals {
  argocd_apps_path = "${path.module}/argocd-applications"
}

# Deploy all ArgoCD Application manifests
resource "kubectl_manifest" "argocd_applications" {
  for_each = fileset(local.argocd_apps_path, "**/*.yaml")

  yaml_body = file("${local.argocd_apps_path}/${each.value}")

  depends_on = [
    helm_release.argocd
  ]
}

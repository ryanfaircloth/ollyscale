# ArgoCD Projects for organizing applications by domain

locals {
  argocd_projects_path = "${path.module}/argocd-projects"
}

# Deploy ArgoCD AppProject manifests
resource "kubectl_manifest" "argocd_projects" {
  for_each = fileset(local.argocd_projects_path, "*.yaml")

  yaml_body = file("${local.argocd_projects_path}/${each.value}")

  depends_on = [
    helm_release.argocd
  ]
}

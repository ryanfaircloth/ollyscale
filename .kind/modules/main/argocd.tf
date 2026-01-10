# ArgoCD - GitOps Continuous Delivery
# Deploy ArgoCD for future migration from Flux
# https://argo-cd.readthedocs.io/

resource "kubernetes_namespace_v1" "argocd" {
  metadata {
    name = "argocd"
  }
  lifecycle {
    ignore_changes = [
      metadata[0].annotations,
      metadata[0].labels,
    ]
  }
}

resource "helm_release" "argocd" {
  name       = "argocd"
  namespace  = kubernetes_namespace_v1.argocd.metadata[0].name
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  version    = "7.7.15" # ArgoCD v2.13.2

  # Allow time for CRDs to be created
  timeout = 600
  wait    = true

  values = [
    file("${path.module}/helm-values/argocd-values.yaml")
  ]

  depends_on = [
    kubernetes_namespace_v1.argocd
  ]
}

# Optional: Create an admin password secret
# Default password is the ArgoCD server pod name
# To get initial password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# ArgoCD - GitOps Continuous Delivery
# Deploy ArgoCD for future migration from Flux
# https://argo-cd.readthedocs.io/
#
# Bootstrap Pattern:
# To avoid circular dependency (ArgoCD -> Gateway -> HTTPRoute -> ArgoCD UI),
# we use a two-stage deployment controlled by the 'bootstrap' variable:
#
# Stage 1 (bootstrap=true): Deploy ArgoCD with basic values, no HTTPRoute
# Stage 2 (bootstrap=false): Update ArgoCD with gateway domain, create HTTPRoute
#
# The Makefile automatically handles this by checking if the cluster exists.

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
  version    = "9.2.4"

  # Allow time for CRDs to be created
  timeout = 600
  wait    = true

  values = [
    var.bootstrap ? file("${path.module}/helm-values/argocd-bootstrap-values.yaml") : templatefile("${path.module}/helm-values/argocd-values.yaml", {
      gateway_dns_suffix = var.gateway_dns_suffix
    })
  ]

  depends_on = [
    kubernetes_namespace_v1.argocd
  ]
}

# Data source to read ArgoCD initial admin password
data "kubernetes_secret_v1" "argocd_initial_admin_secret" {
  metadata {
    name      = "argocd-initial-admin-secret"
    namespace = "argocd"
  }

  depends_on = [
    helm_release.argocd
  ]
}

# Optional: Create an admin password secret
# Default password is the ArgoCD server pod name
# To get initial password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

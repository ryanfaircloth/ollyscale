
resource "kubernetes_namespace_v1" "flux_system" {
  metadata {
    name = var.flux_namespace
  }
  lifecycle {
    ignore_changes = [
      metadata[0].annotations,
      metadata[0].labels,
    ]
  }
}


resource "helm_release" "flux_operator" {
  name       = "flux-operator"
  namespace  = kubernetes_namespace_v1.flux_system.metadata[0].name
  repository = "oci://ghcr.io/controlplaneio-fluxcd/charts"
  chart      = "flux-operator"
  version    = "0.38.1"
  values = [
    file("${path.module}/helm-values/flux-operator-values.yaml")
  ]
}

resource "helm_release" "flux_instance" {
  name       = "flux-instance"
  namespace  = kubernetes_namespace_v1.flux_system.metadata[0].name
  repository = "oci://ghcr.io/controlplaneio-fluxcd/charts"
  chart      = "flux-instance"
  version    = "0.38.1"
  values = [
    file("${path.module}/helm-values/flux-instance-values.yaml")
  ]
  depends_on = [helm_release.flux_operator]
}

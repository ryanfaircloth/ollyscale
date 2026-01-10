resource "kubernetes_namespace_v1" "cert_manager" {
  metadata {
    name = "cert-manager"
  }
  depends_on = [
    resource.helm_release.flux_instance
  ]
}


resource "kubectl_manifest" "cert_manager" {
  yaml_body          = file("${path.module}/flux2-manifests/cert-manager-helmrelease.yaml")
  override_namespace = kubernetes_namespace_v1.cert_manager.metadata[0].name
  depends_on         = [kubectl_manifest.jetstack_helmrepository]
  wait_for {
    field {
      key   = "status.conditions.[0].status"
      value = "True"
    }
  }
}

# Deploy trust-manager HelmRelease using the jetstack chart
resource "kubectl_manifest" "trust_manager_helmrelease" {
  yaml_body          = file("${path.module}/flux2-manifests/trust-manager-helmrelease.yaml")
  override_namespace = kubernetes_namespace_v1.cert_manager.metadata[0].name
  depends_on         = [kubectl_manifest.jetstack_helmrepository, kubectl_manifest.cert_manager]
  wait_for {
    field {
      key   = "status.conditions.[0].status"
      value = "True"
    }
  }
}


# Deploy cluster-issuer HelmRelease using the bedag/raw chart
resource "kubectl_manifest" "cluster_issuer_helmrelease" {
  yaml_body          = file("${path.module}/flux2-manifests/cluster-issuer-helmrelease.yaml")
  override_namespace = kubernetes_namespace_v1.cert_manager.metadata[0].name
  depends_on = [
    kubectl_manifest.bedag_helmrepository,
    kubectl_manifest.cert_manager,
    kubectl_manifest.trust_manager_helmrelease
  ]
  wait_for {
    field {
      key   = "status.conditions.[0].status"
      value = "True"
    }
  }
}

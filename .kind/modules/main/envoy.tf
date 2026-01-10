resource "kubernetes_namespace_v1" "envoy_gateway_system" {
  metadata {
    name = "envoy-gateway-system"
  }

  depends_on = [
    resource.helm_release.flux_instance
  ]
}

resource "kubectl_manifest" "envoyproxy_charts_oci_helmrepository" {
  yaml_body          = file("${path.module}/flux2-manifests/envoyproxy-charts-oci-helmrepository.yaml")
  override_namespace = kubernetes_namespace_v1.flux_system.metadata[0].name
  depends_on         = [helm_release.flux_instance]
}

resource "kubectl_manifest" "envoyproxy_helmrelease" {
  yaml_body          = file("${path.module}/flux2-manifests/envoyproxy-helmrelease.yaml")
  override_namespace = kubernetes_namespace_v1.envoy_gateway_system.metadata[0].name
  depends_on = [
    kubectl_manifest.envoyproxy_charts_oci_helmrepository,
    kubectl_manifest.cert_manager
  ]
  wait_for {
    field {
      key   = "status.conditions.[0].status"
      value = "True"
    }
  }
}


resource "kubectl_manifest" "envoyproxy_gateway" {
  yaml_body          = file("${path.module}/flux2-manifests/gateway-helmrelease.yaml")
  override_namespace = kubernetes_namespace_v1.envoy_gateway_system.metadata[0].name
  depends_on = [
    kubectl_manifest.envoyproxy_helmrelease,
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

resource "kubernetes_namespace_v1" "strimzi_operator" {
  metadata {
    name = "strimzi-operator"
  }
  depends_on = [
    resource.helm_release.flux_instance
  ]
}

resource "kubectl_manifest" "strimzi_charts_oci_helmrepository" {
  yaml_body          = file("${path.module}/flux2-manifests/strimzi-charts-oci-helmrepository.yaml")
  override_namespace = kubernetes_namespace_v1.flux_system.metadata[0].name
  depends_on         = [helm_release.flux_instance]

}


resource "kubectl_manifest" "strimzi_operator" {
  yaml_body          = file("${path.module}/flux2-manifests/strimzi-operator-helmrelease.yaml")
  override_namespace = kubernetes_namespace_v1.strimzi_operator.metadata[0].name
  depends_on = [
    kubectl_manifest.strimzi_charts_oci_helmrepository,
    kubectl_manifest.cert_manager
  ]
  wait_for {
    field {
      key   = "status.conditions.[0].status"
      value = "True"
    }
  }
}

# Strimzi Access Operator HelmRelease
resource "kubectl_manifest" "strimzi_access_operator" {
  yaml_body          = file("${path.module}/flux2-manifests/strimzi-access-operator-helmrelease.yaml")
  override_namespace = kubernetes_namespace_v1.strimzi_operator.metadata[0].name
  depends_on = [
    kubectl_manifest.strimzi_operator
  ]
  wait_for {
    field {
      key   = "status.conditions.[0].status"
      value = "True"
    }
  }
}


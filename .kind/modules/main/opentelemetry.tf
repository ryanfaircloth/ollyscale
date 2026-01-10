resource "kubernetes_namespace_v1" "opentelemetry_operator_system" {
  metadata {
    name = "opentelemetry-operator-system"
  }

  depends_on = [
    resource.helm_release.flux_instance
  ]
}

resource "kubectl_manifest" "opentelemetry_helmrepository" {
  yaml_body          = file("${path.module}/flux2-manifests/opentelemetry-helmrepository.yaml")
  override_namespace = kubernetes_namespace_v1.flux_system.metadata[0].name
  depends_on         = [helm_release.flux_instance]
}

resource "kubectl_manifest" "opentelemetry_operator_helmrelease" {
  yaml_body          = file("${path.module}/flux2-manifests/opentelemetry-operator-helmrelease.yaml")
  override_namespace = kubernetes_namespace_v1.opentelemetry_operator_system.metadata[0].name
  depends_on = [
    kubectl_manifest.opentelemetry_helmrepository,
    kubectl_manifest.cert_manager
  ]
  wait_for {
    field {
      key   = "status.conditions.[0].status"
      value = "True"
    }
  }
}

resource "kubectl_manifest" "otel_logs_collector_helmrelease" {
  yaml_body          = file("${path.module}/flux2-manifests/otel-logs-collector-helmrelease.yaml")
  override_namespace = kubernetes_namespace_v1.opentelemetry_operator_system.metadata[0].name
  depends_on = [
    kubectl_manifest.opentelemetry_operator_helmrelease,
    kubectl_manifest.bedag_helmrepository
  ]
  wait_for {
    field {
      key   = "status.conditions.[0].status"
      value = "True"
    }
  }
}

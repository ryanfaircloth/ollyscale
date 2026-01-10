resource "kubectl_manifest" "jetstack_helmrepository" {
  yaml_body          = file("${path.module}/flux2-manifests/jetstack-helmrepository.yaml")
  override_namespace = kubernetes_namespace_v1.flux_system.metadata[0].name
  depends_on         = [helm_release.flux_instance]
}


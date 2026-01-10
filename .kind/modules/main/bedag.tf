resource "kubectl_manifest" "bedag_helmrepository" {
  yaml_body  = file("${path.module}/flux2-manifests/bedag-helmrepository.yaml")
  depends_on = [helm_release.flux_instance]
}

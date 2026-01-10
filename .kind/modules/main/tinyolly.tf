# TinyOlly deployment disabled - deploy manually via k8s/02-deploy-tinyolly.sh if needed
# # TinyOlly Observability Platform
# # Deploy TinyOlly observability backend for Kafka monitoring and telemetry
# resource "kubernetes_namespace_v1" "tinyolly" {
#   metadata {
#     name = "tinyolly"
#   }
#   depends_on = [
#     resource.helm_release.flux_instance
#   ]
# }
# 
# resource "kubectl_manifest" "tinyolly" {
#   yaml_body          = file("${path.module}/flux2-manifests/tinyolly-helmrelease.yaml")
#   override_namespace = kubernetes_namespace_v1.tinyolly.metadata[0].name
#   depends_on = [
#     resource.kubernetes_namespace_v1.tinyolly,
#     resource.kubectl_manifest.bedag_helmrepository,
#     resource.helm_release.flux_instance
#   ]
#   wait_for {
#     field {
#       key   = "status.conditions.[0].status"
#       value = "True"
#     }
#   }
# }

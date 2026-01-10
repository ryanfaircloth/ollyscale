# Kafka UI deployment disabled - depends on Strimzi cluster
# # Kafka UI - Web-based administration tool for Apache Kafka
# # Deploy Kafka UI for cluster management and monitoring
# 
# # Namespace for kafka-ui
# resource "kubernetes_namespace_v1" "kafka_ui" {
#   metadata {
#     name = "kafka-ui"
#   }
#   depends_on = [
#     resource.helm_release.flux_instance
#   ]
# }
# 
# # HelmRepository for kafka-ui charts
# resource "kubectl_manifest" "kafka_ui_helmrepository" {
#   yaml_body          = file("${path.module}/flux2-manifests/kafka-ui-helmrepository.yaml")
#   override_namespace = var.flux_namespace
#   depends_on         = [helm_release.flux_instance]
# }
# 
# # HelmRelease for kafka-ui application
# resource "kubectl_manifest" "kafka_ui" {
#   yaml_body          = file("${path.module}/flux2-manifests/kafka-ui-helmrelease.yaml")
#   override_namespace = kubernetes_namespace_v1.kafka_ui.metadata[0].name
#   depends_on = [
#     kubectl_manifest.kafka_ui_helmrepository,
#     kubectl_manifest.strimzi_cluster_instance_helmrelease,
#     kubectl_manifest.envoyproxy_gateway,
#     kubectl_manifest.strimzi_access_operator
#   ]
#   wait_for {
#     field {
#       key   = "status.conditions.[0].status"
#       value = "True"
#     }
#   }
# }
# 
# # HelmRelease for kafka-ui resources (KafkaUser, KafkaAccess, HTTPRoute)
# resource "kubectl_manifest" "kafka_ui_resources" {
#   yaml_body          = file("${path.module}/flux2-manifests/kafka-ui-resources-helmrelease.yaml")
#   override_namespace = kubernetes_namespace_v1.kafka_ui.metadata[0].name
#   depends_on = [
#     kubectl_manifest.bedag_helmrepository,
#     kubectl_manifest.strimzi_cluster_instance_helmrelease,
#     kubectl_manifest.strimzi_access_operator
#   ]
#   wait_for {
#     field {
#       key   = "status.conditions.[0].status"
#       value = "True"
#     }
#   }
# }

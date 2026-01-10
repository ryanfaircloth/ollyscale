
# Strimzi cluster deployment disabled - deploy manually via k8s/ scripts if needed
# # Namespace for tinyolly-instance HelmRelease
# resource "kubernetes_namespace_v1" "kafka" {
#   metadata {
#     name = "kafka"
#   }
#   depends_on = [
#     resource.helm_release.flux_instance
#   ]
# }
# 
# # Local HelmRepository for localregistry (OCI)
# resource "kubectl_manifest" "localregistry_helmrepository" {
#   yaml_body          = file("${path.module}/flux2-manifests/localregistry-helmrepository.yaml")
#   override_namespace = var.flux_namespace
#   depends_on         = [helm_release.flux_instance]
# }
# 
# # ConfigMap for strimzi cluster values
# resource "kubernetes_config_map_v1" "strimzi_cluster_values" {
#   metadata {
#     name      = "flux-tinyolly-values"
#     namespace = kubernetes_namespace_v1.kafka.metadata[0].name
#   }
# 
#   data = {
#     "values.yaml" = templatefile("${path.module}/helm-values/flux-tinyolly-values.yaml", {
#       gateway_dns_suffix = var.gateway_dns_suffix
#     })
#   }
# 
#   depends_on = [kubernetes_namespace_v1.kafka]
# }
# 
# 
# 
# # HelmRelease for tinyolly-instance from localregistry
# resource "kubectl_manifest" "strimzi_cluster_instance_helmrelease" {
#   yaml_body = templatefile("${path.module}/flux2-manifests/tinyolly-instance-helmrelease.yaml", {
#     strimzi_cluster_instance_version = var.strimzi_cluster_instance_version
#   })
#   override_namespace = kubernetes_namespace_v1.kafka.metadata[0].name
#   depends_on = [
#     kubectl_manifest.localregistry_helmrepository,
#     kubernetes_config_map_v1.strimzi_cluster_values,
#     kubectl_manifest.trust_manager_helmrelease,
#     kubectl_manifest.strimzi_access_operator
#   ]
#   wait_for {
#     field {
#       key   = "status.conditions.[0].status"
#       value = "True"
#     }
#   }
# }


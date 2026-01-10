output "endpoint" {
  value = kind_cluster.default.endpoint
}
output "cluster_ca_certificate" {
  value = kind_cluster.default.cluster_ca_certificate
}
output "client_certificate" {
  value = kind_cluster.default.client_certificate
}
output "client_key" {
  value = kind_cluster.default.client_key
}

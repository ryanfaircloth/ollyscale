
# Terraform configuration for bootstrapping Flux2 using HelmRelease

module "kind_cluster" {
  source = "./modules/kind_cluster"
}

module "main" {
  source                           = "./modules/main"
  endpoint                         = module.kind_cluster.endpoint
  cluster_ca_certificate           = module.kind_cluster.cluster_ca_certificate
  client_certificate               = module.kind_cluster.client_certificate
  client_key                       = module.kind_cluster.client_key
  strimzi_cluster_instance_version = var.strimzi_cluster_instance_version
  gateway_dns_suffix               = var.gateway_dns_suffix
}

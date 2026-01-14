# Local values for conditional configuration
locals {
  # Determine if we should use local registry
  # Priority: explicit variable > auto-detect via env > default to remote
  use_local_registry = var.use_local_registry

  # Image registry configuration
  # When use_local_registry=true:  docker-registry.registry.svc.cluster.local:5000/tinyolly
  # When use_local_registry=false: ghcr.io/ryanfaircloth/tinyolly
  image_registry = local.use_local_registry ? "docker-registry.registry.svc.cluster.local:5000/tinyolly" : "ghcr.io/ryanfaircloth/tinyolly"

  # Chart registry configuration
  # When use_local_registry=true:  oci://docker-registry.registry.svc.cluster.local:5000/tinyolly/charts
  # When use_local_registry=false: oci://ghcr.io/ryanfaircloth/tinyolly/charts
  chart_registry = local.use_local_registry ? "docker-registry.registry.svc.cluster.local:5000/tinyolly/charts" : "oci://ghcr.io/ryanfaircloth/tinyolly/charts"

  # Image tags
  tinyolly_tag   = var.tinyolly_tag
  opamp_tag      = var.opamp_tag
  demo_tag       = var.demo_tag
  demo_agent_tag = var.demo_agent_tag
}

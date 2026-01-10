# kind_cluster module: Provisions the Kind cluster

terraform {
  required_version = ">= 1.0.0"
  required_providers {

    kind = {
      source  = "tehcyx/kind"
      version = "0.10.0"
    }
  }
}

resource "kind_cluster" "default" {
  name           = var.name
  wait_for_ready = true
  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"
    node {
      role = "control-plane"
      labels = {
        "topology.kubernetes.io/zone" = "az-1"
        "ingress-ready"               = "true"
      }
      extra_port_mappings {
        container_port = 30994
        host_port      = 9094
        protocol       = "TCP"
      }
      extra_port_mappings {
        container_port = 30943
        host_port      = 9443
        protocol       = "TCP"
      }
      extra_port_mappings {
        container_port = 30949
        host_port      = 49443
        protocol       = "TCP"
      }
    }
    node {
      role = "worker"
      labels = {
        "topology.kubernetes.io/zone" = "az-1"
      }
    }
    node {
      role = "worker"
      labels = {
        "topology.kubernetes.io/zone" = "az-2"
      }
    }
    node {
      role = "worker"
      labels = {
        "topology.kubernetes.io/zone" = "az-3"
      }
    }
  }
}

resource "null_resource" "export_kubeconfig" {
  count = var.export_kubectl_conf ? 1 : 0

  depends_on = [kind_cluster.default]

  provisioner "local-exec" {
    command = "kind export kubeconfig --name ${var.name}"
  }
}

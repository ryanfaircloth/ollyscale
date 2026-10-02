# kind_cluster module: Provisions the Kind cluster

terraform {
  required_version = ">= 1.0.0"
  required_providers {

    kind = {
      source  = "tehcyx/kind"
      version = "0.11.0"
    }
  }
}

resource "kind_cluster" "default" {
  name           = var.name
  wait_for_ready = true
  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    # Configure containerd to use the in-cluster registry via control-plane node
    # The registry runs on the control-plane node and is accessible via NodePort
    containerd_config_patches = [
      <<-TOML
      [plugins."io.containerd.grpc.v1.cri".registry]
        [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
          [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker-registry.registry.svc.cluster.local:5000"]
            endpoint = ["http://${var.name}-control-plane:30500"]
        [plugins."io.containerd.grpc.v1.cri".registry.configs]
          [plugins."io.containerd.grpc.v1.cri".registry.configs."${var.name}-control-plane:30500".tls]
            insecure_skip_verify = true
      TOML
    ]

    node {
      role = "control-plane"
      labels = {
        "topology.kubernetes.io/zone" = "az-1"
        "ingress-ready"               = "true"
      }
      extra_port_mappings {
        container_port = var.kafka_nodeport
        host_port      = var.kafka_host_port
        protocol       = "TCP"
      }
      extra_port_mappings {
        container_port = var.https_nodeport
        host_port      = var.https_host_port
        protocol       = "TCP"
      }
      extra_port_mappings {
        container_port = var.mgmt_https_nodeport
        host_port      = var.mgmt_https_host_port
        protocol       = "TCP"
      }
      extra_port_mappings {
        container_port = var.registry_nodeport
        host_port      = var.registry_host_port
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

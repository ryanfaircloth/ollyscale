terraform {
  required_version = ">= 1.0.0"
}



# Providers are now configured in the respective modules:
# - kind_cluster: for Kind cluster provisioning
# - main: for Kubernetes, Helm, and Kubectl providers

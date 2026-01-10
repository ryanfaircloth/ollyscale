# Makefile for TinyOlly KIND cluster management
#
# Targets:
#   up           : Create KIND cluster with local registry
#   down         : Destroy KIND cluster and registry
#   clean        : Remove terraform state files

# Cluster configuration
CLUSTER_NAME := tinyolly

.PHONY: up down clean

## Create KIND cluster with local registry
up:
	@if [ ! -f .kind/terraform.tfstate ]; then \
		pushd .kind && terraform init && popd; \
	fi
	pushd .kind && terraform apply -auto-approve || terraform apply -auto-approve && popd
	@echo ""
	@echo "🎉 TinyOlly cluster deployment complete!"
	@echo ""
	@echo "📋 Next Steps:"
	@echo "  1. Deploy TinyOlly: cd k8s && ./02-deploy-tinyolly.sh"
	@echo "  2. Access UI via kubectl port-forward or LoadBalancer"
	@echo ""

## Destroy KIND cluster and registry
down:
	@echo "Deleting KIND cluster..."
	-kind delete cluster --name $(CLUSTER_NAME)
	@echo "Cleaning up terraform state and config files..."
	-rm -f .kind/terraform.tfstate .kind/terraform.tfstate.backup
	-rm -f .kind/$(CLUSTER_NAME)-config
	@echo "Cleanup complete!"

## Remove terraform state files
clean:
	rm -f .kind/terraform.tfstate .kind/terraform.tfstate.backup
	rm -f .kind/$(CLUSTER_NAME)-config
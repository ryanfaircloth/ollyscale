output "argocd_admin_password" {
  description = "ArgoCD initial admin password (base64 decoded)"
  value       = module.main.argocd_admin_password
  sensitive   = true
}

output "argocd_url" {
  description = "ArgoCD UI URL"
  value       = "https://argocd.${var.gateway_dns_suffix}:49443"
}

output "registry_url" {
  description = "Docker Registry URL"
  value       = "https://registry.${var.gateway_dns_suffix}:49443"
}

output "hostctl_command" {
  description = "Command to add DNS entries to /etc/hosts using hostctl"
  value       = "sudo hostctl add domains ollyscale argocd.${var.gateway_dns_suffix} registry.${var.gateway_dns_suffix} ollyscale.${var.gateway_dns_suffix}"
}

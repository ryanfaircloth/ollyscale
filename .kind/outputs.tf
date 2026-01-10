output "argocd_admin_password" {
  description = "ArgoCD initial admin password (base64 decoded)"
  value       = module.main.argocd_admin_password
  sensitive   = true
}

output "argocd_url" {
  description = "ArgoCD UI URL"
  value       = "https://argocd.${var.gateway_dns_suffix}:49443"
}

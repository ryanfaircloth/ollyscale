output "argocd_admin_password" {
  description = "ArgoCD initial admin password"
  value       = try(data.kubernetes_secret_v1.argocd_initial_admin_secret.data["password"], "")
  sensitive   = true
}

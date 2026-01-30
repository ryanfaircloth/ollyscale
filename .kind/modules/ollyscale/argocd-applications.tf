
resource "kubectl_manifest" "observability_applications" {
  for_each = fileset("${path.module}/argocd-applications/observability", "*.yaml")

  yaml_body = templatefile(
    "${path.module}/argocd-applications/observability/${each.value}",
    {
      gateway_dns_suffix         = var.gateway_dns_suffix
      custom_demo_frontend_image = var.custom_demo_frontend_image
      custom_demo_frontend_tag   = var.custom_demo_frontend_tag
      custom_demo_backend_image  = var.custom_demo_backend_image
      custom_demo_backend_tag    = var.custom_demo_backend_tag
      ai_agent_image             = var.ai_agent_image
      ai_agent_tag               = var.ai_agent_tag
      ai_agent_chart_tag         = var.ai_agent_chart_tag
    }
  )
}

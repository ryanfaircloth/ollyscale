"""Application configuration and settings"""

import os
from typing import List


class Settings:
    """Application settings loaded from environment variables"""
    
    # Redis
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6579"))
    
    # Server
    port: int = int(os.getenv("PORT", "5002"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # OpAMP
    opamp_server_url: str = os.getenv("OPAMP_SERVER_URL", "http://localhost:4321")
    otelcol_default_config: str = os.getenv("OTELCOL_DEFAULT_CONFIG", "/app/otelcol-config.yaml")
    otelcol_templates_dir: str = os.getenv("OTELCOL_TEMPLATES_DIR", "/app/otelcol-templates")
    otel_collector_container: str = os.getenv("OTEL_COLLECTOR_CONTAINER", "otel-collector")
    
    # OTLP
    otel_exporter_otlp_metrics_endpoint: str = os.getenv(
        "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
        "http://localhost:5001/v1/metrics"
    )
    
    # CORS
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:*,http://127.0.0.1:*")
    
    # Deployment
    deployment_env: str = os.getenv("DEPLOYMENT_ENV", "docker")
    
    @property
    def allowed_origins(self) -> List[str]:
        """Parse CORS origins into a list"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

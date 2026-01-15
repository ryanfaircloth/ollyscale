# BSD 3-Clause License
#
# Copyright (c) 2025, Infrastructure Architects, LLC
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Application configuration and settings"""

import os


class Settings:
    """Application settings loaded from environment variables"""

    # Redis
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))

    # Server
    port: int = int(os.getenv("PORT", "5002"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # OpAMP
    opamp_server_url: str = os.getenv("OPAMP_SERVER_URL", "http://localhost:4321")
    otelcol_default_config: str = os.getenv("OTELCOL_DEFAULT_CONFIG", "/app/otelcol-config.yaml")
    otelcol_templates_dir: str = os.getenv("OTELCOL_TEMPLATES_DIR", "/app/otelcol-templates")
    otel_collector_container: str = os.getenv("OTEL_COLLECTOR_CONTAINER", "otel-collector")

    # OTLP - These are only used if not auto-instrumented by the OTel Operator
    # In Kubernetes, the operator injects all OTEL_* env vars automatically
    otel_service_name: str = os.getenv("OTEL_SERVICE_NAME", "tinyolly-ui")

    # CORS
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:*,http://127.0.0.1:*")

    # Deployment
    deployment_env: str = os.getenv("DEPLOYMENT_ENV", "docker")

    @property
    def allowed_origins(self) -> list[str]:
        """Parse CORS origins into a list"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

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

"""HTTP middleware configuration"""

import time
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from ..config import settings
from .telemetry import get_metrics


def setup_middleware(app):
    """Setup all middleware for the FastAPI app"""
    metrics = get_metrics()
    
    # Add custom metrics middleware
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        """Track request metrics for all HTTP endpoints"""
        start_time = time.time()
        
        # Track request
        metrics["request_counter"].add(1, {
            "method": request.method,
            "endpoint": request.url.path
        })
        
        try:
            response = await call_next(request)
            
            # Track response time
            duration_ms = (time.time() - start_time) * 1000
            metrics["response_time_histogram"].record(duration_ms, {
                "method": request.method,
                "endpoint": request.url.path,
                "status": response.status_code
            })
            
            # Track errors
            if response.status_code >= 400:
                metrics["error_counter"].add(1, {
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status": response.status_code
                })
            
            return response
        except Exception as e:
            # Track exceptions
            metrics["error_counter"].add(1, {
                "method": request.method,
                "endpoint": request.url.path,
                "error_type": type(e).__name__
            })
            raise
    
    # Add CORS middleware
    # Default to localhost only for security, can be customized via environment variable
    # Example: CORS_ORIGINS="http://localhost:*,http://127.0.0.1:*,https://example.com"
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add GZip compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

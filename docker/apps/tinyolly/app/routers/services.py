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

"""Service-related endpoints"""

from typing import Dict, Any, List
from fastapi import APIRouter, Query, Depends

from models import ServiceMap
from ..dependencies import get_storage
from common import Storage

router = APIRouter(prefix="/api", tags=["Services"])


@router.get(
    '/service-map',
    response_model=ServiceMap,
    operation_id="get_service_map",
    summary="Get service dependency graph",
    responses={
        200: {"description": "Service dependency graph with nodes and edges"}
    }
)
async def get_service_map(
    limit: int = Query(default=500, le=5000, description="Maximum number of traces to analyze (max 5000)"),
    storage: Storage = Depends(get_storage)
):
    """
    Get service dependency graph showing connections between services.
    
    Analyzes recent traces to build a directed graph of service-to-service 
    communication patterns. Returns nodes (services) and edges (calls between services)
    with request counts and error rates.
    
    Perfect for visualizing microservice architectures and understanding dependencies.
    """
    graph = await storage.get_service_graph(limit)
    return graph


@router.get(
    '/service-catalog',
    response_model=List[Dict[str, Any]],
    operation_id="get_service_catalog",
    summary="Get service catalog with RED metrics",
    responses={
        200: {"description": "Service catalog with Rate, Errors, Duration metrics"}
    }
)
async def get_service_catalog(storage: Storage = Depends(get_storage)):
    """
    Get service catalog with RED metrics (Rate, Errors, Duration).
    
    Returns all services discovered from traces with their golden signals:
    - **Rate**: Requests per second
    - **Errors**: Error rate percentage
    - **Duration**: Average, P95, and P99 latency
    
    Essential for service health monitoring and SLO tracking.
    """
    services = await storage.get_service_catalog()
    return services


@router.get(
    '/stats',
    response_model=Dict[str, Any],
    operation_id="get_stats",
    summary="Get system statistics",
    responses={
        200: {"description": "Overall telemetry data statistics"}
    }
)
async def get_stats(storage: Storage = Depends(get_storage)):
    """
    Get overall system statistics.
    
    Returns aggregate counts for all telemetry data types:
    - Total traces
    - Total spans
    - Total logs
    - Total unique metrics
    - Total services
    
    Useful for monitoring TinyOlly's data volume and health.
    """
    return await storage.get_stats()

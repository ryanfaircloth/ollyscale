import os

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.models.otel import OTLPLogRequest, OTLPMetricRequest, OTLPTraceRequest
from app.storage_v2 import StorageV2

MODE = os.environ.get("OLLYSCALE_MODE", "frontend").lower()
app = FastAPI(title=f"ollyScale v2 API ({MODE} mode)")
storage = StorageV2()

if MODE == "frontend":

    @app.get("/healthz")
    async def healthz():
        return {"status": "ok"}

    @app.get("/health/db")
    async def health_db():
        return await storage.health()


if MODE == "receiver":

    @app.post("/otlp", status_code=200)
    async def otlp_receiver(request: Request):
        body = await request.json()
        # Try to parse as trace, log, or metric request
        try:
            OTLPTraceRequest.model_validate(body)
            # await storage.store_trace(body)  # Future: store in DB
            return JSONResponse({"result": "ok", "type": "trace"}, status_code=status.HTTP_200_OK)
        except Exception:
            pass
        try:
            OTLPLogRequest.model_validate(body)
            # await storage.store_log(body)  # Future: store in DB
            return JSONResponse({"result": "ok", "type": "log"}, status_code=status.HTTP_200_OK)
        except Exception:
            pass
        try:
            OTLPMetricRequest.model_validate(body)
            # await storage.store_metric(body)  # Future: store in DB
            return JSONResponse({"result": "ok", "type": "metric"}, status_code=status.HTTP_200_OK)
        except Exception:
            pass
        return JSONResponse({"error": "Invalid OTLP payload"}, status_code=status.HTTP_400_BAD_REQUEST)

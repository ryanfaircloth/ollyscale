from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.models.otel import OTLPLogRequest, OTLPMetricRequest, OTLPTraceRequest

app = FastAPI(title="ollyScale v2 API (frontend)")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/v2/otlp", status_code=200)
async def otlp_receiver(request: Request):
    body = await request.json()
    # Try to parse as trace, log, or metric request
    try:
        OTLPTraceRequest.model_validate(body)
        return JSONResponse({"result": "ok", "type": "trace"}, status_code=status.HTTP_200_OK)
    except Exception:
        pass
    try:
        OTLPLogRequest.model_validate(body)
        return JSONResponse({"result": "ok", "type": "log"}, status_code=status.HTTP_200_OK)
    except Exception:
        pass
    try:
        OTLPMetricRequest.model_validate(body)
        return JSONResponse({"result": "ok", "type": "metric"}, status_code=status.HTTP_200_OK)
    except Exception:
        pass
    return JSONResponse({"error": "Invalid OTLP payload"}, status_code=status.HTTP_400_BAD_REQUEST)

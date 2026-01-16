# ollyScale Unified Dockerfile
# Single image that can run in either UI or RECEIVER mode
# Mode is selected via MODE environment variable

FROM python:3.14-slim

WORKDIR /app

# Install application dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=1000:1000 main.py .
COPY --chown=1000:1000 models.py .
COPY --chown=1000:1000 common/ common/
COPY --chown=1000:1000 app/ app/
COPY --chown=1000:1000 receiver/ receiver/

# Expose ports (both UI and receiver)
EXPOSE 5002
EXPOSE 4343

# Set Python to unbuffered mode for immediate log output
ENV PYTHONUNBUFFERED=1

# Run main.py which selects mode based on MODE env var
# MODE=ui (default) runs FastAPI UI on port 5002
# MODE=receiver runs gRPC receiver on port 4343
CMD ["python", "-u", "main.py"]

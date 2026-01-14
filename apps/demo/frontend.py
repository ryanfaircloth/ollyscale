# BSD 3-Clause License
#
# Copyright (c) 2025, Infrastructure Architects, LLC
# All rights reserved.

import logging
import os
import random
import threading
import time

import requests
from flask import Flask, jsonify
from prometheus_client import Counter, Histogram, start_http_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter("demo_frontend_requests_total", "Total requests", ["endpoint", "status"])
REQUEST_DURATION = Histogram("demo_frontend_request_duration_seconds", "Request duration", ["endpoint"])

# OTel auto-instrumentation via Instrumentation CR - no manual setup needed

app = Flask(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://demo-backend:5000")


@app.route("/")
def home():
    REQUEST_COUNT.labels(endpoint="/", status="200").inc()
    return jsonify({"message": "Demo Frontend", "endpoints": ["/", "/hello", "/calculate", "/error", "/process-order"]})


@app.route("/hello")
def hello():
    REQUEST_COUNT.labels(endpoint="/hello", status="200").inc()
    return jsonify({"message": "Hello from frontend!"})


@app.route("/calculate")
def calculate():
    with REQUEST_DURATION.labels(endpoint="/calculate").time():
        try:
            response = requests.get(f"{BACKEND_URL}/calculate", timeout=5)
            REQUEST_COUNT.labels(endpoint="/calculate", status="200").inc()
            return jsonify(response.json())
        except Exception as e:
            REQUEST_COUNT.labels(endpoint="/calculate", status="500").inc()
            return jsonify({"error": str(e)}), 500


@app.route("/error")
def trigger_error():
    REQUEST_COUNT.labels(endpoint="/error", status="500").inc()
    raise Exception("Intentional error for demo purposes")


@app.route("/process-order")
def process_order():
    with REQUEST_DURATION.labels(endpoint="/process-order").time():
        order_id = random.randint(1000, 9999)

        # Call backend to process order
        try:
            response = requests.post(f"{BACKEND_URL}/process", json={"order_id": order_id}, timeout=5)
            result = response.json()

            if result.get("status") == "success":
                REQUEST_COUNT.labels(endpoint="/process-order", status="200").inc()
                return jsonify({"status": "success", "order_id": order_id, "details": result})
            else:
                REQUEST_COUNT.labels(endpoint="/process-order", status="500").inc()
                return jsonify({"status": "failed", "order_id": order_id}), 500
        except Exception as e:
            REQUEST_COUNT.labels(endpoint="/process-order", status="500").inc()
            return jsonify({"status": "failed", "error": str(e)}), 500


def auto_generate_traffic():
    """Background thread to automatically generate traffic"""
    time.sleep(10)  # Wait for app to start
    logger.info("Starting auto-traffic generation...")

    while True:
        try:
            rand = random.randint(1, 100)
            if rand <= 10:
                requests.get("http://localhost:5000/error")
            elif rand <= 30:
                requests.get("http://localhost:5000/calculate")
            elif rand <= 50:
                requests.get("http://localhost:5000/hello")
            else:
                requests.get("http://localhost:5000/process-order")
        except Exception:
            pass

        time.sleep(random.uniform(3, 8))


if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(8000)

    # Start auto-traffic generator in background
    traffic_thread = threading.Thread(target=auto_generate_traffic, daemon=True)
    traffic_thread.start()

    app.run(host="0.0.0.0", port=5000)

# BSD 3-Clause License
#
# Copyright (c) 2025, Infrastructure Architects, LLC
# All rights reserved.

import logging
import random
import time

from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OTel auto-instrumentation via Instrumentation CR - no manual setup needed

app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/calculate")
def calculate():
    # Auto-instrumentation will create spans
    # Simulate computation
    time.sleep(random.uniform(0.1, 0.3))

    a = random.randint(1, 100)
    b = random.randint(1, 100)
    result = a + b

    return jsonify({"operation": "add", "a": a, "b": b, "result": result})


@app.route("/process", methods=["POST"])
def process_order():
    data = request.get_json()
    order_id = data.get("order_id")

    # Auto-instrumentation will create spans
    # Simulate order validation
    time.sleep(random.uniform(0.05, 0.15))
    valid = random.random() > 0.1  # 90% success rate

    if not valid:
        return jsonify({"status": "failed", "reason": "validation_failed"}), 400

    # Simulate payment processing
    time.sleep(random.uniform(0.1, 0.3))

    # Simulate inventory check
    time.sleep(random.uniform(0.05, 0.15))

    return jsonify({"status": "success", "order_id": order_id, "processing_time_ms": random.randint(100, 500)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

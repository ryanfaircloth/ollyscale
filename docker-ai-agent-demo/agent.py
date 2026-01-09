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

# AI Agent Demo - Zero-Code Auto-Instrumentation
# NO OpenTelemetry imports needed - opentelemetry-instrument handles everything!

import time
import random
import os
import logging
from ollama import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
client = Client(host=OLLAMA_HOST)

PROMPTS = [
    "Write a haiku about observability.",
    "Explain distributed tracing in one sentence.",
    "What is OpenTelemetry?",
    "Name three monitoring best practices.",
    "What makes a good dashboard?",
    "Describe the purpose of spans in tracing.",
]


def run_agent_workflow():
    prompt_text = random.choice(PROMPTS)
    logger.info(f"Calling Ollama with prompt: {prompt_text}")

    # This call is AUTO-INSTRUMENTED by opentelemetry-instrumentation-ollama
    # Spans with gen_ai.* attributes are created automatically!
    response = client.chat(
        model="tinyllama",
        messages=[{"role": "user", "content": prompt_text}]
    )

    content = response["message"]["content"]
    logger.info(f"Got response: {content[:100]}...")
    return content


if __name__ == "__main__":
    logger.info("Starting AI Agent Demo...")
    logger.info(f"Ollama host: {OLLAMA_HOST}")

    # Wait for Ollama to be ready
    time.sleep(10)

    logger.info("Starting agent loop...")
    while True:
        try:
            run_agent_workflow()
        except Exception as e:
            logger.error(f"Agent error: {e}")
        time.sleep(15)

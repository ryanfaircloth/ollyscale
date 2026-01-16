# Demo Applications

ollyScale includes several demo applications to help you explore its observability capabilities. These demos range from simple microservices to complex distributed systems.

## Available Demos

### [Custom Demo Applications](custom-demo.md)

Simple Python Flask microservices demonstrating core observability features:

- **Services**: demo-frontend and demo-backend
- **Languages**: Python
- **Features**: Auto-traffic generation, distributed tracing, Prometheus metrics
- **Resource Usage**: Low (~256MB)
- **Best For**: Quick testing, development, learning basics

**Key Highlights:**

- Automatic traffic generation every 3-8 seconds
- Multiple endpoints (simple requests, calculations, complex orders, errors)
- Easy to understand and modify
- Minimal resource requirements

[View Documentation →](custom-demo.md)

---

### [OpenTelemetry Demo](otel-demo.md)

The official OpenTelemetry demo application ("Astronomy Shop"):

- **Services**: 11+ microservices
- **Languages**: Go, Java, Python, .NET, Node.js, Rust, Ruby, PHP
- **Features**: E-commerce workflows, built-in load generator, multi-language instrumentation
- **Resource Usage**: High (~2-4GB)
- **Best For**: Comprehensive demos, training, polyglot environments

**Key Highlights:**

- Production-realistic distributed system
- Showcases OTel instrumentation across 7+ languages
- Complex distributed traces (10-20 spans)
- Realistic user workflows (browse, cart, checkout, payment)

[View Documentation →](otel-demo.md)

---

## Advanced Demos

### [eBPF Zero-Code Tracing](../ebpf.md)

Automatic distributed tracing without code changes using eBPF:

- **Technology**: eBPF with Beyla auto-instrumentation
- **Features**: Zero-code instrumentation, HTTP/gRPC tracing
- **Best For**: Legacy applications, no-modification observability

[View Documentation →](../ebpf.md)

---

### [AI Agent with Ollama](../ai-agent.md)

GenAI observability demo with LLM instrumentation:

- **Technology**: Ollama LLM with OTel instrumentation
- **Features**: LLM span attributes, token tracking, prompt/response logging
- **Best For**: AI/ML observability, GenAI applications

[View Documentation →](../ai-agent.md)

---

## Quick Comparison

| Demo            | Complexity | Services | Languages | Resource Usage | Auto-Traffic |
| --------------- | ---------- | -------- | --------- | -------------- | ------------ |
| **Custom Demo** | Simple     | 2        | Python    | Low            | ✅           |
| **OTel Demo**   | Complex    | 11+      | 7+        | High           | ✅           |
| **eBPF Demo**   | Medium     | 2        | Go        | Low            | ❌           |
| **AI Agent**    | Simple     | 1        | Python    | Medium         | ✅           |

## Deployment

All demos can be deployed via:

### Helm

```bash
# Custom Demo
helm install ollyscale-demos charts/ollyscale-demos \
  --namespace ollyscale-demos \
  --create-namespace

# OTel Demo
helm install ollyscale-demos charts/ollyscale-demos \
  --set customDemo.enabled=false \
  --set otelDemo.enabled=true
```

### Terraform/ArgoCD (Recommended)

```bash
cd .kind

# Enable Custom Demo
terraform apply -var="custom_demo_enabled=true"

# Enable OTel Demo
terraform apply -var="otel_demo_enabled=true" -var="custom_demo_enabled=false"
```

## Accessing Demos

After deployment, demos are available via HTTPRoutes:

- **Custom Demo Frontend**: `https://demo-frontend.ollyscale.test:49443`
- **OTel Demo**: `https://otel-demo.ollyscale.test:49443`
- **ollyScale UI**: `https://ollyscale.ollyscale.test:49443`

## Viewing Telemetry

All demos send telemetry to ollyScale. Open the ollyScale UI to explore:

1. **Service Map**: Visual representation of service dependencies
2. **Traces**: Distributed traces with timing and attributes
3. **Logs**: Application logs with trace correlation
4. **Metrics**: RED metrics (Rate, Errors, Duration)

## Choosing a Demo

**For Learning/Development:**

- Start with **Custom Demo** - simple, fast, easy to understand

**For Demonstrations/Training:**

- Use **OTel Demo** - comprehensive, production-realistic

**For Polyglot Environments:**

- Use **OTel Demo** - showcases multiple languages

**For Legacy Applications:**

- Try **eBPF Demo** - no code changes required

**For AI/ML Workloads:**

- Try **AI Agent** - GenAI-specific instrumentation

## Migration

If you're migrating from the old `k8s-demo/` or `k8s-otel-demo/` directories, see the migration sections in:

- [Custom Demo Migration](custom-demo.md#migration-from-k8s-demo)
- [OTel Demo Migration](otel-demo.md#migration-from-k8s-otel-demo)

## Support

For issues or questions:

- [GitHub Issues](https://github.com/ryanfaircloth/ollyscale/issues)
- [Documentation](https://ollyscale.io/docs)

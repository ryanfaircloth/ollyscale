# Cardinality Protection

<div align="center">
  <img src="../images/spans.png" alt="Cardinality Protection" width="600">
  <p><em>Span waterfall showing distributed trace complexity</em></p>
</div>

---

ollyScale includes built-in protection against metric cardinality explosion with a configurable limit on unique metric names.

## Configuration

### Environment Variables

| Variable                 | Default | Description                 |
| ------------------------ | ------- | --------------------------- |
| `MAX_METRIC_CARDINALITY` | 1000    | Maximum unique metric names |
| `REDIS_TTL`              | 1800    | Metric retention (seconds)  |

### Kubernetes Deployment

Update Helm values in `charts/ollyscale/values.yaml`:

```yaml
otlpReceiver:
  env:
    MAX_METRIC_CARDINALITY: "2000" # Increase limit
    REDIS_TTL: "3600" # 1 hour retention
```

Then upgrade the deployment:

```bash
cd charts
helm upgrade ollyscale ./ollyscale -n ollyscale
```

### Docker Deployment

Update `docker-compose-ollyscale-core.yml` in the `docker/` directory:

```yaml
environment:
  MAX_METRIC_CARDINALITY: 2000
  REDIS_TTL: 3600
```

## Monitoring

The UI displays cardinality warnings when approaching the limit:

- **Yellow Warning:** 70-90% of limit reached
- **Red Alert:** 90%+ of limit reached

Check current cardinality via the API:

```bash
curl http://localhost:5005/api/stats
```

Response:

```json
{
  "traces": 145,
  "logs": 892,
  "metrics": 850,
  "metrics_max": 1000,
  "metrics_dropped": 23
}
```

# OllyScale PostgreSQL Chart

This Helm chart deploys a CloudNativePG (CNPG) PostgreSQL cluster optimized for OllyScale.

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- CloudNativePG Operator installed (see [CNPG documentation](https://cloudnative-pg.io/documentation/current/installation_upgrade/))

## Installation

```bash
# Add the chart repository (if published)
helm repo add ollyscale oci://ghcr.io/ryanfaircloth/ollyscale/charts

# Install the chart
helm install ollyscale-postgres ollyscale/ollyscale-postgres \
  --namespace ollyscale-postgres \
  --create-namespace
```

## Configuration

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `namespace` | Namespace for PostgreSQL resources | `ollyscale-postgres` |
| `numberOfInstances` | Number of PostgreSQL instances (HA replicas) | `1` |
| `volume.size` | Persistent volume size | `10Gi` |
| `volume.storageClass` | Storage class name | `""` (cluster default) |
| `resources.requests.cpu` | CPU request | `100m` |
| `resources.requests.memory` | Memory request | `256Mi` |
| `resources.limits.cpu` | CPU limit | `1000m` |
| `resources.limits.memory` | Memory limit | `1Gi` |
| `postgresql.version` | PostgreSQL major version | `17` |

### Example Values

```yaml
# Production configuration with HA
numberOfInstances: 3
volume:
  size: 50Gi
  storageClass: fast-ssd
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 4Gi
```

## Connection Details

After installation, CNPG creates a secret with connection credentials:

```bash
# Get connection URI
kubectl get secret ollyscale-postgres-app -n ollyscale-postgres \
  -o jsonpath='{.data.uri}' | base64 -d

# Connect via psql
kubectl exec -n ollyscale-postgres ollyscale-postgres-1 -c postgres -- \
  psql -U ollyscale -d ollyscale
```

The secret contains:
- `uri`: Full PostgreSQL connection URI
- `username`: Database username (`ollyscale`)
- `password`: Auto-generated password
- `dbname`: Database name (`ollyscale`)
- `host`: Service hostname
- `port`: Service port (`5432`)

## Features

### High Availability

- Patroni-based automatic failover
- Synchronous replication (configurable)
- Split-brain protection
- Automatic backup and recovery (CNPG features)

### Monitoring

CNPG exposes Prometheus metrics on each pod at `:9187/metrics`. Configure your Prometheus to scrape:

```yaml
- job_name: 'cnpg'
  kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
          - ollyscale-postgres
  relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_cnpg_io_cluster]
      action: keep
      regex: ollyscale-postgres
```

## Maintenance

### Scaling

```bash
# Scale to 3 instances for HA
helm upgrade ollyscale-postgres ollyscale/ollyscale-postgres \
  --set numberOfInstances=3 \
  --reuse-values
```

### Backups

CNPG supports continuous backup to object storage. See [CNPG backup documentation](https://cloudnative-pg.io/documentation/current/backup/) for configuration.

### Upgrades

PostgreSQL major version upgrades require a new cluster and data migration. Minor version upgrades are handled automatically by CNPG.

## Integration with OllyScale

The OllyScale API chart expects the database secret to be available at `ollyscale-postgres-app` in the configured namespace. Configure the API chart:

```yaml
api:
  databaseSecretName: ollyscale-postgres-app
```

## Troubleshooting

### Check Cluster Status

```bash
kubectl get cluster ollyscale-postgres -n ollyscale-postgres
```

### View Logs

```bash
# Primary pod logs
kubectl logs -n ollyscale-postgres ollyscale-postgres-1 -c postgres

# CNPG operator logs
kubectl logs -n cnpg-system -l app.kubernetes.io/name=cloudnative-pg
```

### Common Issues

1. **Pods not starting**: Check PVC creation and storage class availability
2. **Connection refused**: Verify CNPG operator is running and cluster status is "Cluster in healthy state"
3. **Performance issues**: Adjust `resources` and `postgresql.parameters` for your workload

## License

AGPL-3.0 - see LICENSE file for details

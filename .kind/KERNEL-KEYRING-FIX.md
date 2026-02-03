# Kernel Keyring Quota Issue Fix

## Problem

When running a large number of containers in KIND on Podman Machine, you may encounter errors like:

```text
Error: failed to create containerd task: failed to create shim task:
OCI runtime create failed: runc create failed: unable to start container process:
error during container init: unable to join session keyring:
unable to create session key: disk quota exceeded
```

**This is NOT a disk space issue** - it's a Linux kernel keyring limit being exceeded.

## Root Cause

The Podman Machine (Fedora CoreOS) has very low default kernel keyring limits:

- `kernel.keys.maxkeys = 200` (max number of keys)
- `kernel.keys.maxbytes = 20000` (max memory for keys)

With ~56 deployments/statefulsets across multiple namespaces (otel-demo, ollyscale, infrastructure),
you easily hit this limit as each container needs kernel keys for session management.

## Solution

Increase the kernel keyring limits inside the Podman machine:

```bash
# Check current usage (you were at 197/200!)
podman machine ssh cat /proc/keys | wc -l

# Increase limits (TEMPORARY - lost on reboot)
podman machine ssh sudo sysctl -w kernel.keys.maxkeys=10000
podman machine ssh sudo sysctl -w kernel.keys.maxbytes=2000000

# Verify
podman machine ssh sysctl kernel.keys.maxkeys kernel.keys.maxbytes
```

## Make it Permanent

To persist these settings across Podman machine restarts, you need to configure the Podman machine
to apply these sysctl settings on boot.

**Option 1: Via Ignition config (when creating machine):**

Add to your podman machine init config:

```bash
podman machine init --rootful --now \
  --ignition=<(cat <<EOF
{
  "ignition": {"version": "3.0.0"},
  "storage": {
    "files": [{
      "path": "/etc/sysctl.d/99-keyring.conf",
      "mode": 420,
      "contents": {"source": "data:,kernel.keys.maxkeys%3D10000%0Akernel.keys.maxbytes%3D2000000"}
    }]
  }
}
EOF
)
```

**Option 2: Manual (existing machine):**

```bash
podman machine ssh
sudo tee /etc/sysctl.d/99-keyring.conf <<EOF
kernel.keys.maxkeys = 10000
kernel.keys.maxbytes = 2000000
EOF
sudo sysctl -p /etc/sysctl.d/99-keyring.conf
```

## Verification

After increasing limits, clean up failed pods:

```bash
# Delete failed pods in all namespaces
kubectl delete pods --all-namespaces --field-selector=status.phase=Failed

# Watch pods come back up
kubectl get pods -A -w
```

## References

- [Podman Issue #10027](https://github.com/containers/podman/issues/10027)
- [KIND Issue #1988](https://github.com/kubernetes-sigs/kind/issues/1988)
- [Linux Kernel Keyring Documentation](https://www.kernel.org/doc/html/latest/security/keys/core.html)

## Applied

Fixed on: 2026-02-01

- Increased from 200 → 10000 keys
- Increased from 20000 → 2000000 bytes
- All pods started successfully after this change

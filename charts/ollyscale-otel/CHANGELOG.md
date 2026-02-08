# Changelog

## 0.1.0 (TBD)

### Features

* Initial release - separates OpenTelemetry collector infrastructure from main ollyscale chart
* Deploys to otel-system namespace for clear separation of concerns
* Includes agent collector (DaemonSet), gateway collector, and browser collector
* Instrumentation CR for auto-instrumentation across namespaces
* eBPF agent support (disabled by default)
* Configurable polling templates via ConfigMap

{{/*
Expand the name of the chart.
*/}}
{{- define "tinyolly-ai-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "tinyolly-ai-agent.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "tinyolly-ai-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "tinyolly-ai-agent.labels" -}}
helm.sh/chart: {{ include "tinyolly-ai-agent.chart" . }}
{{ include "tinyolly-ai-agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "tinyolly-ai-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "tinyolly-ai-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Ollama labels
*/}}
{{- define "tinyolly-ai-agent.ollama.labels" -}}
helm.sh/chart: {{ include "tinyolly-ai-agent.chart" . }}
{{ include "tinyolly-ai-agent.ollama.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: ollama
{{- end }}

{{- define "tinyolly-ai-agent.ollama.selectorLabels" -}}
app.kubernetes.io/name: {{ include "tinyolly-ai-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: ollama
app: ollama
{{- end }}

{{/*
Agent labels
*/}}
{{- define "tinyolly-ai-agent.agent.labels" -}}
helm.sh/chart: {{ include "tinyolly-ai-agent.chart" . }}
{{ include "tinyolly-ai-agent.agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: ai-agent
{{- end }}

{{- define "tinyolly-ai-agent.agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "tinyolly-ai-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: ai-agent
app: ai-agent
{{- end }}

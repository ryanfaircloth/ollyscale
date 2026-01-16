{{/*
Common labels
*/}}
{{- define "ollyscale.labels" -}}
helm.sh/chart: {{ include "ollyscale.chart" . }}
{{ include "ollyscale.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ollyscale.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ollyscale.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "ollyscale.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Expand the name of the chart.
*/}}
{{- define "ollyscale.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "ollyscale.fullname" -}}
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
UI component name
*/}}
{{- define "ollyscale.ui.name" -}}
{{ include "ollyscale.fullname" . }}-ui
{{- end }}

{{/*
UI service account name
*/}}
{{- define "ollyscale.ui.serviceAccountName" -}}
{{- if .Values.ui.serviceAccount.create }}
{{- default (include "ollyscale.ui.name" .) .Values.ui.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.ui.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
UI component labels
*/}}
{{- define "ollyscale.ui.labels" -}}
{{ include "ollyscale.labels" . }}
app.kubernetes.io/component: ui
{{- end }}

{{/*
UI selector labels
*/}}
{{- define "ollyscale.ui.selectorLabels" -}}
{{ include "ollyscale.selectorLabels" . }}
app.kubernetes.io/component: ui
app: ollyscale-ui
{{- end }}

{{/*
Frontend component name (renamed from ui)
*/}}
{{- define "ollyscale.frontend.name" -}}
{{ include "ollyscale.fullname" . }}-frontend
{{- end }}

{{/*
Frontend component fullname (for service references)
*/}}
{{- define "ollyscale.frontend.fullname" -}}
{{ include "ollyscale.fullname" . }}-frontend
{{- end }}

{{/*
Frontend service account name
*/}}
{{- define "ollyscale.frontend.serviceAccountName" -}}
{{- if .Values.frontend.serviceAccount.create }}
{{- default (include "ollyscale.frontend.name" .) .Values.frontend.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.frontend.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Frontend component labels
*/}}
{{- define "ollyscale.frontend.labels" -}}
{{ include "ollyscale.labels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Frontend selector labels
*/}}
{{- define "ollyscale.frontend.selectorLabels" -}}
{{ include "ollyscale.selectorLabels" . }}
app.kubernetes.io/component: frontend
app: ollyscale-frontend
{{- end }}

{{/*
Web UI component name
*/}}
{{- define "ollyscale.webui.name" -}}
{{ include "ollyscale.fullname" . }}-webui
{{- end }}

{{/*
Web UI component fullname (for service references)
*/}}
{{- define "ollyscale.webui.fullname" -}}
{{ include "ollyscale.fullname" . }}-webui
{{- end }}

{{/*
Web UI service account name
*/}}
{{- define "ollyscale.webui.serviceAccountName" -}}
{{- if .Values.webui.serviceAccount.create }}
{{- default (include "ollyscale.webui.name" .) .Values.webui.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.webui.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Web UI component labels
*/}}
{{- define "ollyscale.webui.labels" -}}
{{ include "ollyscale.labels" . }}
app.kubernetes.io/component: webui
{{- end }}

{{/*
Web UI selector labels
*/}}
{{- define "ollyscale.webui.selectorLabels" -}}
{{ include "ollyscale.selectorLabels" . }}
app.kubernetes.io/component: webui
app: ollyscale-webui
{{- end }}

{{/*
OpAMP Server component name
*/}}
{{- define "ollyscale.opampServer.name" -}}
{{ include "ollyscale.fullname" . }}-opamp-server
{{- end }}

{{/*
OpAMP Server service account name
*/}}
{{- define "ollyscale.opampServer.serviceAccountName" -}}
{{- if .Values.opampServer.serviceAccount.create }}
{{- default (include "ollyscale.opampServer.name" .) .Values.opampServer.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.opampServer.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
OpAMP Server component labels
*/}}
{{- define "ollyscale.opampServer.labels" -}}
{{ include "ollyscale.labels" . }}
app.kubernetes.io/component: opamp-server
{{- end }}

{{/*
OpAMP Server selector labels
*/}}
{{- define "ollyscale.opampServer.selectorLabels" -}}
{{ include "ollyscale.selectorLabels" . }}
app.kubernetes.io/component: opamp-server
app: ollyscale-opamp-server
{{- end }}

{{/*
OTLP Receiver component name
*/}}
{{- define "ollyscale.otlpReceiver.name" -}}
{{ include "ollyscale.fullname" . }}-otlp-receiver
{{- end }}

{{/*
OTLP Receiver service account name
*/}}
{{- define "ollyscale.otlpReceiver.serviceAccountName" -}}
{{- if .Values.otlpReceiver.serviceAccount.create }}
{{- default (include "ollyscale.otlpReceiver.name" .) .Values.otlpReceiver.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.otlpReceiver.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
OTLP Receiver component labels
*/}}
{{- define "ollyscale.otlpReceiver.labels" -}}
{{ include "ollyscale.labels" . }}
app.kubernetes.io/component: otlp-receiver
{{- end }}

{{/*
OTLP Receiver selector labels
*/}}
{{- define "ollyscale.otlpReceiver.selectorLabels" -}}
{{ include "ollyscale.selectorLabels" . }}
app.kubernetes.io/component: otlp-receiver
app: ollyscale-otlp-receiver
{{- end }}

{{/*
Image pull policy helper
Usage: include "ollyscale.imagePullPolicy" (dict "component" .Values.ui.image "global" .)
*/}}
{{- define "ollyscale.imagePullPolicy" -}}
{{- if .component.pullPolicy -}}
{{- .component.pullPolicy -}}
{{- else -}}
{{- .global.Values.image.pullPolicy -}}
{{- end -}}
{{- end }}

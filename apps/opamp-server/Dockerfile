# Build stage
FROM golang:1.25-alpine AS builder

WORKDIR /app

# Install git for fetching dependencies
RUN apk add --no-cache git

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY *.go ./

# Build the binary
RUN CGO_ENABLED=0 GOOS=linux go build -o /ollyscale-opamp-server .

# Runtime stage - using scratch for absolute minimum size
# Note: If HTTPS/TLS calls fail, switch to distroless/static-debian12:nonroot for CA certs
FROM scratch

COPY --from=builder /ollyscale-opamp-server /ollyscale-opamp-server

# OpAMP port for collector connections
EXPOSE 4320
# HTTP REST API port
EXPOSE 4321

ENTRYPOINT ["/ollyscale-opamp-server"]

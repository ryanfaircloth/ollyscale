# OTLP Specification Compliance Requirements

## Trace/Span ID Handling

### Specification

- **Source**: OpenTelemetry Protocol (OTLP) v1.x
- **trace_id**: 16 bytes (128 bits)
- **span_id**: 8 bytes (64 bits)
- **Encoding in JSON**: base64
- **Display format**: hex (lowercase)

### Required Conversions

#### Storage (Write Path)

```text
Input: OTLP JSON with base64 IDs
{
  "traceId": "AQIDBAUGBwgJCgsMDQ4PEA==",  // 16 bytes base64
  "spanId": "AQIDBAUGBwg="                // 8 bytes base64
}

Conversion:
1. base64.b64decode() → bytes
2. bytes.hex() → hex string
3. Store in VARCHAR(32) and VARCHAR(16)

Output: Database storage
trace_id = "0102030405060708090a0b0c0d0e0f10"  (32 hex chars)
span_id = "0102030405060708"                   (16 hex chars)
```

#### Retrieval (Read Path)

```text
Input: Database VARCHAR
trace_id = "0102030405060708090a0b0c0d0e0f10"
span_id = "0102030405060708"

Output: API JSON response
{
  "trace_id": "0102030405060708090a0b0c0d0e0f10",
  "span_id": "0102030405060708"
}
```

### Unit Test Requirements

1. **test_base64_to_hex_conversion()**
   - Input: Valid base64 trace_id (24 chars base64)
   - Expected: 32 char hex string
   - Input: Valid base64 span_id (12 chars base64)
   - Expected: 16 char hex string

2. **test_store_traces_converts_ids()**
   - Input: OTLP JSON with base64 IDs
   - Verify: Database contains hex strings of correct length
   - Verify: No empty strings stored

3. **test_retrieve_traces_returns_hex()**
   - Setup: Insert spans with known hex IDs
   - Retrieve: Via get_trace_by_id()
   - Verify: Returns hex strings, not empty, not bytes

4. **test_mixed_format_handling()**
   - Input: Already-hex IDs (from tests)
   - Input: Base64 IDs (from real OTLP)
   - Verify: Both work correctly

### Current Failures

1. Database contains empty trace_id/span_id
2. API returns empty strings for IDs
3. No unit tests exist for ID conversion
4. Code has untested logic branches

### Correction Plan

1. ✅ Document specification requirements (this file)
2. ❌ Write comprehensive unit tests FIRST
3. ❌ Verify current database state (check actual values)
4. ❌ Fix storage code with proper validation
5. ❌ Fix retrieval code with proper validation
6. ❌ Run tests to prove correctness
7. ❌ Deploy and verify with real data

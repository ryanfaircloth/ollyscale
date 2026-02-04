import { useState, useMemo } from 'react';
import { Modal, Card, Badge, Row, Col, Alert } from 'react-bootstrap';
import { TraceWaterfall } from '@/components/trace/TraceWaterfall';
import { TruncatedId } from '@/components/common/TruncatedId';
import { formatDuration, formatRelativeTime, formatNumber } from '@/utils/formatting';
import type { Trace, Span } from '@/api/types/common';

interface AISessionDetailModalProps {
  trace: Trace | null;
  onHide: () => void;
}

/**
 * Extract value from OTLP attribute array or object
 */
const getAttrValue = (attributes: any, key: string): any => {
  if (!attributes) return undefined;

  // Handle array format: [{ key: '...', value: { string_value: '...' } }]
  if (Array.isArray(attributes)) {
    const attr = attributes.find((a: any) => a.key === key);
    if (!attr?.value) return undefined;
    const val = attr.value;
    // API uses snake_case for OTLP attribute values
    return val.string_value ?? val.int_value ?? val.bool_value ?? val.double_value ?? val.array_value ?? val.kvlist_value ?? val;
  }

  // Handle object format: { 'key': 'value' }
  return attributes[key];
};

/**
 * Check if a span has GenAI attributes
 */
const hasGenAIAttrs = (span: Span): boolean => {
  const attrs = span.attributes;
  return !!(
    getAttrValue(attrs, 'gen_ai.system') ||
    getAttrValue(attrs, 'gen_ai.request.model') ||
    getAttrValue(attrs, 'gen_ai.usage.input_tokens')
  );
};

/**
 * Check if a span is a tool call
 */
const isToolSpan = (span: Span): boolean => {
  return span.name.toLowerCase().includes('tool') || !!getAttrValue(span.attributes, 'agent.tool.name');
};

/**
 * Extract multiple possible attribute keys and return the actual value
 */
const extractAttr = (span: Span, keys: string[]): any => {
  for (const key of keys) {
    const val = getAttrValue(span.attributes, key);
    if (val !== undefined && val !== null) {
      // getAttrValue already extracts the actual value from OTLP structure
      return val;
    }
  }
  return undefined;
};

export function AISessionDetailModal({ trace, onHide }: AISessionDetailModalProps) {
  const [selectedSpan, setSelectedSpan] = useState<Span | null>(null);

  // Identify AI and tool spans
  const categorizedSpans = useMemo(() => {
    if (!trace) return { aiSpans: [], toolSpans: [], otherSpans: [] };

    const aiSpans: Span[] = [];
    const toolSpans: Span[] = [];
    const otherSpans: Span[] = [];

    trace.spans.forEach((span) => {
      if (hasGenAIAttrs(span)) {
        aiSpans.push(span);
      } else if (isToolSpan(span)) {
        toolSpans.push(span);
      } else {
        otherSpans.push(span);
      }
    });

    return { aiSpans, toolSpans, otherSpans };
  }, [trace]);

  // Calculate summary stats
  const summary = useMemo(() => {
    if (!trace) return null;

    let totalPromptTokens = 0;
    let totalCompletionTokens = 0;
    let totalTokens = 0;
    const models = new Set<string>();

    categorizedSpans.aiSpans.forEach((span) => {
      const promptTokens = parseInt(String(extractAttr(span, ['gen_ai.usage.input_tokens', 'gen_ai.usage.prompt_tokens']) || 0));
      const completionTokens = parseInt(String(extractAttr(span, ['gen_ai.usage.output_tokens', 'gen_ai.usage.completion_tokens']) || 0));

      totalPromptTokens += promptTokens;
      totalCompletionTokens += completionTokens;
      totalTokens += promptTokens + completionTokens;

      const model = extractAttr(span, ['gen_ai.request.model', 'gen_ai.model']);
      // extractAttr now returns the actual value, just convert to string
      if (model) models.add(String(model));
    });

    return {
      totalPromptTokens,
      totalCompletionTokens,
      totalTokens,
      models: Array.from(models),
      aiSpanCount: categorizedSpans.aiSpans.length,
      toolSpanCount: categorizedSpans.toolSpans.length,
    };
  }, [trace, categorizedSpans]);

  const handleSpanClick = (span: Span) => {
    setSelectedSpan(selectedSpan?.span_id === span.span_id ? null : span);
  };

  if (!trace) return null;

  return (
    <Modal show={true} onHide={onHide} size="xl" fullscreen="lg-down">
      <Modal.Header closeButton>
        <Modal.Title>
          <i className="bi bi-robot me-2"></i>
          AI Session Detail
          <span className="ms-2">
            <TruncatedId id={trace.trace_id} maxLength={16} />
          </span>
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {/* Summary Cards */}
        {summary && (
          <Row className="mb-3">
            <Col md={3}>
              <Card className="text-center">
                <Card.Body>
                  <h6 className="text-muted mb-1">AI Spans</h6>
                  <h3 className="mb-0">{summary.aiSpanCount}</h3>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3}>
              <Card className="text-center">
                <Card.Body>
                  <h6 className="text-muted mb-1">Total Tokens</h6>
                  <h3 className="mb-0">{formatNumber(summary.totalTokens)}</h3>
                  <small className="text-muted">
                    <span className="text-success">↓ {formatNumber(summary.totalPromptTokens)}</span>
                    {' / '}
                    <span className="text-warning">↑ {formatNumber(summary.totalCompletionTokens)}</span>
                  </small>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3}>
              <Card className="text-center">
                <Card.Body>
                  <h6 className="text-muted mb-1">Tool Calls</h6>
                  <h3 className="mb-0">{summary.toolSpanCount}</h3>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3}>
              <Card className="text-center">
                <Card.Body>
                  <h6 className="text-muted mb-1">Models</h6>
                  <div className="mt-2">
                    {summary.models.map((model) => (
                      <Badge key={model} bg="info" className="me-1">
                        {model}
                      </Badge>
                    ))}
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        )}

        {/* Legend */}
        <Alert variant="light" className="py-2">
          <small>
            <strong>Legend:</strong>
            <Badge bg="primary" className="ms-2 me-1">🤖</Badge> AI Spans
            <Badge bg="secondary" className="ms-2 me-1">🛠️</Badge> Tool Calls
            <Badge bg="light" text="dark" className="ms-2 me-1">⚡</Badge> Other Spans
          </small>
        </Alert>

        {/* Waterfall View */}
        <Card>
          <Card.Header>
            <strong>Trace Timeline</strong>
            <small className="text-muted ms-2">
              Duration: {trace.duration_seconds ? formatDuration(trace.duration_seconds) : '-'}
            </small>
          </Card.Header>
          <Card.Body>
            <TraceWaterfall spans={trace.spans} onSpanClick={handleSpanClick} />
          </Card.Body>
        </Card>

        {/* Selected Span Detail */}
        {selectedSpan && (
          <Card className="mt-3">
            <Card.Header>
              <strong>Span Details</strong>
              {hasGenAIAttrs(selectedSpan) && <Badge bg="primary" className="ms-2">🤖 AI Span</Badge>}
              {isToolSpan(selectedSpan) && <Badge bg="secondary" className="ms-2">🛠️ Tool Call</Badge>}
            </Card.Header>
            <Card.Body>
              {/* Basic Info */}
              <Row className="mb-3">
                <Col md={6}>
                  <div className="mb-2">
                    <strong>Span Name:</strong> <code className="ms-2">{selectedSpan.name}</code>
                  </div>
                  <div className="mb-2">
                    <strong>Span ID:</strong> <code className="ms-2 small">{selectedSpan.span_id}</code>
                  </div>
                  <div className="mb-2">
                    <strong>Service:</strong> <code className="ms-2">{selectedSpan.service_name}</code>
                  </div>
                </Col>
                <Col md={6}>
                  <div className="mb-2">
                    <strong>Duration:</strong> {formatDuration((new Date(selectedSpan.end_time).getTime() - new Date(selectedSpan.start_time).getTime()) / 1000)}
                  </div>
                  <div className="mb-2">
                    <strong>Start:</strong> {formatRelativeTime(selectedSpan.start_time)}
                  </div>
                  <div className="mb-2">
                    <strong>Status:</strong> <Badge bg={selectedSpan.status?.code === 2 ? 'danger' : 'success'}>
                      {selectedSpan.status?.code === 2 ? 'Error' : 'OK'}
                    </Badge>
                  </div>
                </Col>
              </Row>

              {/* AI-Specific Details */}
              {hasGenAIAttrs(selectedSpan) && (
                <>
                  <hr />
                  <Row className="mb-3">
                    <Col md={6}>
                      <div className="mb-2">
                        <strong>Model:</strong>
                        <Badge bg="info" className="ms-2">
                          {extractAttr(selectedSpan, ['gen_ai.request.model', 'gen_ai.model']) || 'Unknown'}
                        </Badge>
                      </div>
                      <div className="mb-2">
                        <strong>Tokens:</strong>
                        <span className="ms-2 text-success">
                          ↓ {formatNumber(parseInt(String(extractAttr(selectedSpan, ['gen_ai.usage.input_tokens', 'gen_ai.usage.prompt_tokens']) || 0)))}
                        </span>
                        {' / '}
                        <span className="text-warning">
                          ↑ {formatNumber(parseInt(String(extractAttr(selectedSpan, ['gen_ai.usage.output_tokens', 'gen_ai.usage.completion_tokens']) || 0)))}
                        </span>
                      </div>
                    </Col>
                    <Col md={6}>
                      {extractAttr(selectedSpan, ['gen_ai.request.temperature']) !== undefined && (
                        <div className="mb-2">
                          <strong>Temperature:</strong> {extractAttr(selectedSpan, ['gen_ai.request.temperature'])}
                        </div>
                      )}
                      {extractAttr(selectedSpan, ['gen_ai.request.max_tokens']) !== undefined && (
                        <div className="mb-2">
                          <strong>Max Tokens:</strong> {extractAttr(selectedSpan, ['gen_ai.request.max_tokens'])}
                        </div>
                      )}
                    </Col>
                  </Row>

                  {/* Prompt and Response */}
                  <Row>
                    <Col md={6}>
                      <h6 className="mb-2">
                        <i className="bi bi-chat-left-text me-2"></i>Prompt
                      </h6>
                      <pre
                        className="bg-light p-2 rounded small"
                        style={{
                          maxHeight: '250px',
                          overflow: 'auto',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                        }}
                      >
                        {extractAttr(selectedSpan, [
                          'gen_ai.prompt.0.content',
                          'gen_ai.prompt',
                          'gen_ai.request.prompt',
                          'llm.prompts.0.content',
                          'llm.prompt'
                        ]) || 'No prompt data'}
                      </pre>
                    </Col>
                    <Col md={6}>
                      <h6 className="mb-2">
                        <i className="bi bi-chat-right-text me-2"></i>Response
                      </h6>
                      <pre
                        className="bg-light p-2 rounded small"
                        style={{
                          maxHeight: '250px',
                          overflow: 'auto',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                        }}
                      >
                        {extractAttr(selectedSpan, [
                          'gen_ai.completion.0.content',
                          'gen_ai.completion',
                          'gen_ai.response.completion',
                          'llm.completions.0.content',
                          'llm.completion',
                          'gen_ai.response'
                        ]) || 'No response data'}
                      </pre>
                    </Col>
                  </Row>
                </>
              )}
            </Card.Body>
          </Card>
        )}
      </Modal.Body>
    </Modal>
  );
}

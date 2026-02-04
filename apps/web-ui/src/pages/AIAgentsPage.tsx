import { useState } from 'react';
import { Container, Row, Col, Card, Table, Badge, Button, Form, InputGroup } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { useAutoRefresh } from '@/hooks/useAutoRefresh';
import { useSpansQuery } from '@/api/queries/useSpansQuery';
import { useTracesQuery } from '@/api/queries/useTracesQuery';
import { formatRelativeTime, formatDuration, formatNumber, formatAttributeValue } from '@/utils/formatting';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';
import { AISessionDetailModal } from '@/components/ai/AISessionDetailModal';

interface GenAISpan {
  span_id: string;
  trace_id: string;
  name: string;
  timestamp: string;
  duration_seconds: number;
  service_name: string;
  model?: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  temperature?: number;
  max_tokens?: number;
  prompt?: string;
  response?: string;
}

export default function AIAgentsPage() {
  const { t } = useTranslation();
  const [selectedModel, setSelectedModel] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedSpan, setExpandedSpan] = useState<string | null>(null);
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);

  // Fetch spans and filter for GenAI attributes on client-side
  // Backend doesn't support attribute-based filtering, so we fetch more spans and filter client-side
  const [timeRange] = useState({
    start_time: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // Last 30 minutes
    end_time: new Date(Date.now()).toISOString(),
  });

  const { data, isLoading, error, refetch } = useSpansQuery({
    time_range: timeRange,
    filters: [], // No backend filters - we'll filter on client-side for GenAI attributes
    pagination: { limit: 1000 }, // Fetch more spans to find GenAI ones
  });

  useAutoRefresh(refetch);

  // Fetch trace details when a trace is selected
  const { data: traceData } = useTracesQuery(
    {
      time_range: timeRange,
      filters: [{ field: 'trace_id', operator: 'eq', value: selectedTraceId! }],
      pagination: { limit: 1 },
    },
    { enabled: !!selectedTraceId }
  );

  const selectedTrace = traceData?.traces?.[0] || null;

  if (isLoading) return <LoadingSpinner message={t('aiAgents.loading', 'Loading AI agent sessions...')} />;
  if (error) return <EmptyState title={t('common.error', 'Error')} description={t('aiAgents.errorDesc', 'Failed to load AI agents: {{message}}', { message: error.message })} />;
  if (!data || !data.spans || data.spans.length === 0) {
    return <EmptyState title={t('aiAgents.noActivity', 'No AI Agent Activity')} description={t('aiAgents.noActivityDesc', 'No GenAI spans found in the last 30 minutes.')} />;
  }

  // Transform spans to GenAI format
  const genAISpans: GenAISpan[] = data.spans.map((span) => {
    const attrs = span.attributes || [];
    const getAttr = (key: string) => {
      const attr = attrs.find((a) => a.key === key);
      if (!attr?.value) return '';
      const val = attr.value as any;
      // Extract actual value from OTLP structure (API uses snake_case)
      const actualValue = val.string_value ?? val.int_value ?? val.bool_value ?? val.double_value ?? val;
      return formatAttributeValue(actualValue);
    };
    const getIntAttr = (key: string) => {
      const attr = attrs.find((a) => a.key === key);
      if (!attr?.value) return undefined;
      const val = attr.value as any;
      // Extract actual numeric value from OTLP structure (API uses snake_case)
      const actualValue = val.int_value ?? val.double_value ?? val.string_value ?? val;
      return typeof actualValue === 'number' ? actualValue : (actualValue ? Number(actualValue) : undefined);
    };

    // Extract prompt - try multiple attribute names for compatibility
    const extractPrompt = (): string => {
      // Try different GenAI semantic convention attributes
      const promptKeys = [
        'gen_ai.prompt.0.content',
        'gen_ai.prompt',
        'gen_ai.request.prompt',
        'llm.prompts.0.content',
        'llm.prompt'
      ];
      for (const key of promptKeys) {
        const val = getAttr(key);
        if (val) return val;
      }
      return '';
    };

    // Extract response - try multiple attribute names for compatibility
    const extractResponse = (): string => {
      const responseKeys = [
        'gen_ai.completion.0.content',
        'gen_ai.completion',
        'gen_ai.response',
        'llm.completions.0.content',
        'llm.completion',
        'llm.response'
      ];
      for (const key of responseKeys) {
        const val = getAttr(key);
        if (val) return val;
      }
      return '';
    };

    return {
      span_id: span.span_id,
      trace_id: span.trace_id,
      name: span.name,
      timestamp: span.start_time,
      duration_seconds: span.duration_seconds || 0,
      service_name: getAttr('service.name'),
      model: getAttr('gen_ai.request.model') || getAttr('gen_ai.system') || getAttr('llm.model'),
      prompt_tokens: getIntAttr('gen_ai.usage.input_tokens') || getIntAttr('llm.usage.prompt_tokens'),
      completion_tokens: getIntAttr('gen_ai.usage.output_tokens') || getIntAttr('llm.usage.completion_tokens'),
      total_tokens: getIntAttr('gen_ai.usage.total_tokens') || getIntAttr('llm.usage.total_tokens'),
      temperature: getIntAttr('gen_ai.request.temperature') || getIntAttr('llm.temperature'),
      max_tokens: getIntAttr('gen_ai.request.max_tokens') || getIntAttr('llm.max_tokens'),
      prompt: extractPrompt(),
      response: extractResponse(),
    };
  });

  // Filter to only include spans with GenAI attributes (at least has a model attribute)
  // This excludes non-AI spans from the view
  const genAISpansOnly = genAISpans.filter((span) => {
    // Must have at least one GenAI-related attribute to be considered an AI span
    return span.model || span.prompt || span.response || span.total_tokens;
  });

  // Filter by model and search term
  const filteredSpans = genAISpansOnly.filter((span) => {
    if (selectedModel !== 'all' && span.model !== selectedModel) return false;
    if (searchTerm && !span.name.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  // Extract unique models from GenAI spans only
  const uniqueModels = Array.from(new Set(genAISpansOnly.map((s) => s.model).filter(Boolean)));

  // Calculate aggregate stats from GenAI spans only
  const totalTokens = genAISpansOnly.reduce((sum, s) => sum + (s.total_tokens || 0), 0);
  const totalPromptTokens = genAISpansOnly.reduce((sum, s) => sum + (s.prompt_tokens || 0), 0);
  const totalCompletionTokens = genAISpansOnly.reduce((sum, s) => sum + (s.completion_tokens || 0), 0);
  const avgDuration = genAISpansOnly.length > 0
    ? genAISpansOnly.reduce((sum, s) => sum + s.duration_seconds, 0) / genAISpansOnly.length
    : 0;

  const toggleExpand = (spanId: string) => {
    setExpandedSpan(expandedSpan === spanId ? null : spanId);
  };

  return (
    <Container fluid className="p-4">
      <Row className="mb-4">
        <Col>
          <h2 className="mb-3">
            <i className="bi bi-robot me-2"></i>
            AI Agents
          </h2>
          <p className="text-muted">Monitor LLM calls with prompts, responses, and token usage</p>
        </Col>
      </Row>

      {/* Summary Cards */}
      <Row className="mb-4">
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h6 className="text-muted mb-2">Total LLM Calls</h6>
              <h3>{genAISpansOnly.length}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h6 className="text-muted mb-2">Total Tokens</h6>
              <h3>{formatNumber(totalTokens)}</h3>
              <small className="text-muted">
                {formatNumber(totalPromptTokens)} in / {formatNumber(totalCompletionTokens)} out
              </small>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h6 className="text-muted mb-2">Avg Duration</h6>
              <h3>{formatDuration(avgDuration)}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h6 className="text-muted mb-2">Unique Models</h6>
              <h3>{uniqueModels.length}</h3>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Row className="mb-3">
        <Col md={4}>
          <Form.Group>
            <Form.Label>Filter by Model</Form.Label>
            <Form.Select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)}>
              <option value="all">All Models</option>
              {uniqueModels.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </Form.Select>
          </Form.Group>
        </Col>
        <Col md={8}>
          <Form.Group>
            <Form.Label>Search</Form.Label>
            <InputGroup>
              <InputGroup.Text>
                <i className="bi bi-search"></i>
              </InputGroup.Text>
              <Form.Control
                type="text"
                placeholder="Search by span name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </InputGroup>
          </Form.Group>
        </Col>
      </Row>

      {/* GenAI Spans Table */}
      <Card>
        <Card.Header>
          <strong>LLM Call History</strong> ({filteredSpans.length} calls)
        </Card.Header>
        <Card.Body className="p-0">
          <Table responsive hover className="mb-0">
            <thead>
              <tr>
                <th style={{ width: '40px' }}></th>
                <th>Span Name</th>
                <th>Model</th>
                <th>Tokens (In/Out)</th>
                <th>Duration</th>
                <th>Service</th>
                <th>Timestamp</th>
                <th>Trace ID</th>
              </tr>
            </thead>
            <tbody>
              {filteredSpans.map((span) => (
                <>
                  <tr key={span.span_id} style={{ cursor: 'pointer' }} onClick={() => toggleExpand(span.span_id)}>
                    <td>
                      <Button variant="link" size="sm" className="p-0">
                        <i className={`bi bi-chevron-${expandedSpan === span.span_id ? 'down' : 'right'}`}></i>
                      </Button>
                    </td>
                    <td>
                      <code className="small">{span.name}</code>
                    </td>
                    <td>
                      <Badge bg="info">{span.model || 'unknown'}</Badge>
                    </td>
                    <td>
                      <span className="text-success">{formatNumber(span.prompt_tokens || 0)}</span>
                      {' / '}
                      <span className="text-warning">{formatNumber(span.completion_tokens || 0)}</span>
                      {span.total_tokens && (
                        <>
                          {' '}
                          <small className="text-muted">({formatNumber(span.total_tokens)} total)</small>
                        </>
                      )}
                    </td>
                    <td>{formatDuration(span.duration_seconds)}</td>
                    <td>{span.service_name}</td>
                    <td>{formatRelativeTime(span.timestamp)}</td>
                    <td>
                      <a
                        href="#"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedTraceId(span.trace_id);
                        }}
                        className="text-decoration-none"
                      >
                        <code className="small">{span.trace_id.substring(0, 16)}...</code>
                      </a>
                    </td>
                  </tr>
                  {expandedSpan === span.span_id && (
                    <tr>
                      <td colSpan={8}>
                        <Card className="m-2">
                          <Card.Body>
                            {/* Summary Section - Preserve metadata */}
                            <Row className="mb-3 align-items-center">
                              <Col md={6}>
                                <div className="d-flex align-items-center gap-2 mb-2">
                                  <strong>Model:</strong>
                                  <Badge bg="info">{span.model || 'unknown'}</Badge>
                                </div>
                                <div className="d-flex align-items-center gap-2 mb-2">
                                  <strong>Tokens:</strong>
                                  <span className="text-success">
                                    <i className="bi bi-arrow-down"></i> {formatNumber(span.prompt_tokens || 0)}
                                  </span>
                                  <span className="text-warning">
                                    <i className="bi bi-arrow-up"></i> {formatNumber(span.completion_tokens || 0)}
                                  </span>
                                  {span.total_tokens && (
                                    <small className="text-muted">({formatNumber(span.total_tokens)} total)</small>
                                  )}
                                </div>
                              </Col>
                              <Col md={6}>
                                <div className="mb-2">
                                  <strong>Service:</strong> <code className="small ms-2">{span.service_name}</code>
                                </div>
                                <div className="mb-2">
                                  <strong>Duration:</strong> <span className="ms-2">{formatDuration(span.duration_seconds)}</span>
                                </div>
                                <div className="mb-2">
                                  <strong>Timestamp:</strong> <span className="ms-2">{formatRelativeTime(span.timestamp)}</span>
                                </div>
                              </Col>
                            </Row>
                            <hr />
                            {/* Prompt and Response */}
                            <Row>
                              <Col md={6}>
                                <h6 className="mb-2">
                                  <i className="bi bi-chat-left-text me-2"></i>Prompt
                                </h6>
                                <pre
                                  className="bg-light p-2 rounded small"
                                  style={{
                                    maxHeight: '300px',
                                    overflow: 'auto',
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word'
                                  }}
                                >
                                  {span.prompt || 'No prompt data available'}
                                </pre>
                              </Col>
                              <Col md={6}>
                                <h6 className="mb-2">
                                  <i className="bi bi-chat-right-text me-2"></i>Response
                                </h6>
                                <pre
                                  className="bg-light p-2 rounded small"
                                  style={{
                                    maxHeight: '300px',
                                    overflow: 'auto',
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word'
                                  }}
                                >
                                  {span.response || 'No response data available'}
                                </pre>
                              </Col>
                            </Row>
                            {/* Parameters and Actions */}
                            <hr />
                            <Row className="align-items-center">
                              <Col md={6}>
                                <strong>Parameters:</strong>
                                {span.temperature !== undefined && <Badge bg="secondary" className="ms-2">temp: {span.temperature}</Badge>}
                                {span.max_tokens !== undefined && <Badge bg="secondary" className="ms-2">max_tokens: {span.max_tokens}</Badge>}
                              </Col>
                              <Col md={6} className="text-end">
                                <Button
                                  variant="outline-primary"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedTraceId(span.trace_id);
                                  }}
                                >
                                  <i className="bi bi-diagram-3 me-1"></i>View Full Trace
                                </Button>
                              </Col>
                            </Row>
                          </Card.Body>
                        </Card>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      <div className="mt-3 text-muted small">
        <i className="bi bi-info-circle me-2"></i>
        GenAI spans are automatically captured when using OpenTelemetry instrumentation for LLMs (Ollama, OpenAI, etc.).
        Token counts and model parameters are extracted from span attributes following OpenTelemetry GenAI semantic conventions.
      </div>

      {/* AI Session Detail Modal */}
      <AISessionDetailModal
        trace={selectedTrace}
        onHide={() => setSelectedTraceId(null)}
      />
    </Container>
  );
}

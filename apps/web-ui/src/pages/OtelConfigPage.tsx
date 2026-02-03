import { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Card, Button, Alert, Badge, ListGroup, Modal } from 'react-bootstrap';
import { apiClient } from '@/api/client';

interface OpAMPStatus {
  status: string;
  agent_count: number;
  agents: AgentInfo[];
}

interface AgentInfo {
  agent_id: string;
  version: string;
  last_seen: string;
}

interface ConfigTemplate {
  name: string;
  description: string;
}

interface ValidationError {
  section?: string;
  message: string;
  valid_values?: string[];
}

interface DiffLine {
  type: 'context' | 'added' | 'removed';
  content: string;
}

export default function OtelConfigPage() {
  const [status, setStatus] = useState<OpAMPStatus | null>(null);
  const [templates, setTemplates] = useState<ConfigTemplate[]>([]);
  const [config, setConfig] = useState('');
  const [originalConfig, setOriginalConfig] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [showDiffModal, setShowDiffModal] = useState(false);
  const [diff, setDiff] = useState<DiffLine[]>([]);

  const editorRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);

  // Load OpAMP status
  const loadStatus = async () => {
    try {
      const response = await apiClient.get<OpAMPStatus>('/api/opamp/status');
      const statusData = response.data;

      // Convert agents to array if it's an object
      if (statusData && typeof statusData.agents === 'object' && !Array.isArray(statusData.agents)) {
        statusData.agents = Object.values(statusData.agents);
      }

      // Ensure agents is always an array
      if (statusData && !Array.isArray(statusData.agents)) {
        statusData.agents = [];
      }

      setStatus(statusData);
    } catch (error) {
      console.error('Failed to load OpAMP status:', error);
      setStatusMessage({ type: 'error', text: 'Failed to load OpAMP status' });
    }
  };

  // Load available templates
  const loadTemplates = async () => {
    try {
      const response = await apiClient.get<ConfigTemplate[]>('/api/opamp/templates');
      // Ensure we always set an array, even if the API returns something unexpected
      setTemplates(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Failed to load templates:', error);
      setTemplates([]); // Ensure templates is always an array even on error
    }
  };

  // Load current configuration
  const loadConfig = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get<{ config: string }>('/api/opamp/config');
      setConfig(response.data.config);
      setOriginalConfig(response.data.config);
      setValidationErrors([]);
      updateLineNumbers();
    } catch (error) {
      console.error('Failed to load config:', error);
      setStatusMessage({ type: 'error', text: 'Failed to load configuration' });
    } finally {
      setIsLoading(false);
    }
  };

  // Load template
  const loadTemplate = async (templateName: string) => {
    try {
      const params = new URLSearchParams({ template: templateName });
      const response = await apiClient.get<{ config: string }>(`/api/opamp/templates/${templateName}?${params}`);
      setConfig(response.data.config);
      setValidationErrors([]);
      updateLineNumbers();
      setStatusMessage({ type: 'info', text: `Loaded template: ${templateName}` });
    } catch (error) {
      console.error('Failed to load template:', error);
      setStatusMessage({ type: 'error', text: 'Failed to load template' });
    }
  };

  // Validate configuration
  const validateConfig = async (): Promise<boolean> => {
    try {
      const response = await apiClient.post<{ valid: boolean; errors?: ValidationError[] }>('/api/opamp/validate', { config });
      if (response.data.valid) {
        setValidationErrors([]);
        return true;
      } else {
        // Ensure errors is always an array
        const errors = Array.isArray(response.data.errors) ? response.data.errors : [];
        setValidationErrors(errors);
        return false;
      }
    } catch (error: unknown) {
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string | ValidationError[] } } };
        const detail = axiosError.response?.data?.detail;
        if (typeof detail === 'string') {
          setValidationErrors([{ message: detail }]);
        } else if (Array.isArray(detail)) {
          setValidationErrors(detail as ValidationError[]);
        } else {
          setValidationErrors([{ message: 'Validation failed' }]);
        }
      } else {
        setValidationErrors([{ message: 'Validation failed' }]);
      }
      return false;
    }
  };

  // Compute diff between original and current config
  const computeDiff = () => {
    // Ensure both config strings are defined
    const original = originalConfig || '';
    const current = config || '';

    const originalLines = original.split('\n');
    const currentLines = current.split('\n');
    const diffLines: DiffLine[] = [];

    const maxLen = Math.max(originalLines.length, currentLines.length);
    for (let i = 0; i < maxLen; i++) {
      const origLine = originalLines[i] || '';
      const currLine = currentLines[i] || '';

      if (origLine === currLine) {
        diffLines.push({ type: 'context', content: origLine });
      } else {
        if (origLine) {
          diffLines.push({ type: 'removed', content: origLine });
        }
        if (currLine) {
          diffLines.push({ type: 'added', content: currLine });
        }
      }
    }

    setDiff(diffLines);
  };

  // Show diff preview
  const handleShowDiff = async () => {
    const isValid = await validateConfig();
    if (isValid) {
      computeDiff();
      setShowDiffModal(true);
    } else {
      setStatusMessage({ type: 'error', text: 'Configuration is invalid. Please fix errors before viewing diff.' });
    }
  };

  // Apply configuration
  const handleApplyConfig = async () => {
    setIsSaving(true);
    setShowDiffModal(false);
    try {
      await apiClient.post('/api/opamp/config', { config });
      setOriginalConfig(config);
      setStatusMessage({ type: 'success', text: 'Configuration applied successfully' });
      await loadStatus();
    } catch (error) {
      console.error('Failed to apply config:', error);
      setStatusMessage({ type: 'error', text: 'Failed to apply configuration' });
    } finally {
      setIsSaving(false);
    }
  };

  // Update line numbers
  const updateLineNumbers = () => {
    if (!lineNumbersRef.current || !editorRef.current) return;

    const lineCount = (config || '').split('\n').length;
    const lineHeight = 20; // Approximate line height
    const numbers = Array.from({ length: lineCount }, (_, i) => i + 1).join('\n');
    lineNumbersRef.current.textContent = numbers;
    lineNumbersRef.current.style.height = `${lineCount * lineHeight}px`;
  };

  // Handle editor scroll
  const handleEditorScroll = () => {
    if (editorRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = editorRef.current.scrollTop;
    }
  };

  // Handle tab key in editor
  const handleEditorKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const target = e.currentTarget;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      const newValue = config.substring(0, start) + '  ' + config.substring(end);
      setConfig(newValue);
      setTimeout(() => {
        target.selectionStart = target.selectionEnd = start + 2;
      }, 0);
    }
  };

  // Load initial data
  useEffect(() => {
    loadStatus();
    loadTemplates();
    loadConfig();
  }, []);

  // Update line numbers when config changes
  useEffect(() => {
    updateLineNumbers();
  }, [config]);

  return (
    <Container fluid className="p-4">
      <Row className="mb-4">
        <Col>
          <h2 className="mb-3">
            <i className="bi bi-gear me-2"></i>
            OpenTelemetry Collector Configuration
          </h2>
          <p className="text-muted">Manage collector configuration via OpAMP protocol</p>
        </Col>
      </Row>

      {statusMessage && (
        <Alert variant={statusMessage.type === 'error' ? 'danger' : statusMessage.type} dismissible onClose={() => setStatusMessage(null)}>
          {statusMessage.text}
        </Alert>
      )}

      {/* OpAMP Status */}
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Header>
              <strong>OpAMP Status</strong>
            </Card.Header>
            <Card.Body>
              {isLoading ? (
                <div className="text-center">
                  <div className="spinner-border spinner-border-sm" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                </div>
              ) : status ? (
                <div>
                  <div className="mb-3">
                    <Badge bg={status.status === 'ok' ? 'success' : 'danger'} className="me-2">
                      {status.status}
                    </Badge>
                    <span>{status.agent_count} agent(s) connected</span>
                  </div>
                  {status.agents && status.agents.length > 0 && (
                    <ListGroup>
                      {status.agents.map((agent) => (
                        <ListGroup.Item key={agent.agent_id}>
                          <strong>{agent.agent_id}</strong>
                          <br />
                          <small className="text-muted">
                            Version: {agent.version} | Last seen: {new Date(agent.last_seen).toLocaleString()}
                          </small>
                        </ListGroup.Item>
                      ))}
                    </ListGroup>
                  )}
                </div>
              ) : (
                <Alert variant="warning">Failed to load OpAMP status</Alert>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Configuration Editor */}
      <Row>
        <Col md={9}>
          <Card className="mb-3">
            <Card.Header className="d-flex justify-content-between align-items-center">
              <strong>Configuration Editor</strong>
              <div>
                <Button variant="outline-primary" size="sm" className="me-2" onClick={handleShowDiff} disabled={isSaving}>
                  <i className="bi bi-eye me-2"></i>
                  Show Diff
                </Button>
                <Button variant="primary" size="sm" onClick={handleApplyConfig} disabled={isSaving}>
                  {isSaving ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      Applying...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-check me-2"></i>
                      Apply
                    </>
                  )}
                </Button>
              </div>
            </Card.Header>
            <Card.Body className="p-0">
              <div style={{ display: 'flex', position: 'relative' }}>
                <div
                  ref={lineNumbersRef}
                  style={{
                    width: '50px',
                    backgroundColor: '#f8f9fa',
                    borderRight: '1px solid #dee2e6',
                    padding: '10px 5px',
                    fontFamily: 'Monaco, Courier, monospace',
                    fontSize: '14px',
                    textAlign: 'right',
                    lineHeight: '20px',
                    overflow: 'hidden',
                    userSelect: 'none',
                  }}
                />
                <textarea
                  ref={editorRef}
                  value={config}
                  onChange={(e) => setConfig(e.target.value)}
                  onScroll={handleEditorScroll}
                  onKeyDown={handleEditorKeyDown}
                  style={{
                    flex: 1,
                    fontFamily: 'Monaco, Courier, monospace',
                    fontSize: '14px',
                    lineHeight: '20px',
                    padding: '10px',
                    border: 'none',
                    resize: 'vertical',
                    minHeight: '400px',
                    outline: 'none',
                  }}
                />
              </div>
            </Card.Body>
          </Card>

          {validationErrors && validationErrors.length > 0 && (
            <Alert variant="danger">
              <strong>Validation Errors:</strong>
              <ul className="mb-0 mt-2">
                {validationErrors.map((error, idx) => (
                  <li key={idx}>
                    {error.section && <strong>[{error.section}]</strong>} {error.message}
                    {error.valid_values && error.valid_values.length > 0 && (
                      <div className="small mt-1">
                        Valid values: {error.valid_values.slice(0, 5).join(', ')}
                        {error.valid_values.length > 5 && '...'}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </Alert>
          )}
        </Col>

        <Col md={3}>
          <Card>
            <Card.Header>
              <strong>Templates</strong>
            </Card.Header>
            <ListGroup variant="flush">
              {templates && templates.map((template) => (
                <ListGroup.Item key={template.name} action onClick={() => loadTemplate(template.name)} style={{ cursor: 'pointer' }}>
                  <strong>{template.name}</strong>
                  <br />
                  <small className="text-muted">{template.description}</small>
                </ListGroup.Item>
              ))}
            </ListGroup>
          </Card>
        </Col>
      </Row>

      {/* Diff Modal */}
      <Modal show={showDiffModal} onHide={() => setShowDiffModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Configuration Diff</Modal.Title>
        </Modal.Header>
        <Modal.Body style={{ maxHeight: '600px', overflow: 'auto', fontFamily: 'Monaco, Courier, monospace', fontSize: '14px' }}>
          {diff && diff.map((line, idx) => (
            <div
              key={idx}
              style={{
                backgroundColor: line.type === 'added' ? '#d4edda' : line.type === 'removed' ? '#f8d7da' : 'transparent',
                color: line.type === 'added' ? '#155724' : line.type === 'removed' ? '#721c24' : '#333',
                padding: '2px 5px',
                whiteSpace: 'pre',
              }}
            >
              {line.type === 'added' ? '+ ' : line.type === 'removed' ? '- ' : '  '}
              {line.content}
            </div>
          ))}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDiffModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleApplyConfig}>
            Apply Configuration
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}

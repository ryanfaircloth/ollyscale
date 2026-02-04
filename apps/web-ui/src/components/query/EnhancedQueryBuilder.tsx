import { useState } from 'react';
import { Card, Button, Form, Row, Col, Badge, InputGroup, Modal, Alert, Collapse } from 'react-bootstrap';
import { useQuery } from '@/contexts/QueryContext';
import { QueryBuilderWrapper, type FieldSchema } from './QueryBuilderWrapper';

interface EnhancedQueryBuilderProps {
  fieldSchema: FieldSchema[];
  availableNamespaces?: string[];
  availableServices?: string[];
  showFreeTextSearch?: boolean;
}

const TIME_RANGES = [
  { label: 'Last 15 minutes', minutes: 15 },
  { label: 'Last 30 minutes', minutes: 30 },
  { label: 'Last hour', minutes: 60 },
  { label: 'Last 3 hours', minutes: 180 },
  { label: 'Last 6 hours', minutes: 360 },
  { label: 'Last 12 hours', minutes: 720 },
  { label: 'Last 24 hours', minutes: 1440 },
];

export function EnhancedQueryBuilder({
  fieldSchema,
  availableNamespaces = [],
  availableServices = [],
  showFreeTextSearch = true,
}: EnhancedQueryBuilderProps) {
  const {
    queryState,
    updateFilters,
    updateTimeRange,
    updateTimeField,
    updateTimezone,
    updateFreeTextSearch,
    updateSelectedNamespaces,
    updateSelectedServices,
    updateLiveMode,
    resetQuery,
    presets,
    savePreset,
    loadPreset,
    deletePreset,
  } = useQuery();

  const [showBuilder, setShowBuilder] = useState(true);
  const [showPresetModal, setShowPresetModal] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [presetDescription, setPresetDescription] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(true);

  const handleTimeRangePreset = (minutes: number) => {
    const end = new Date();
    const start = new Date(end.getTime() - minutes * 60 * 1000);
    // Store relative minutes and enable live mode
    queryState.relativeMinutes = minutes;
    queryState.liveMode = true;
    updateTimeRange({
      start_time: start.toISOString(),
      end_time: end.toISOString(),
    }, true);
  };

  const handleSavePreset = () => {
    if (presetName.trim()) {
      savePreset(presetName.trim(), presetDescription.trim() || undefined);
      setPresetName('');
      setPresetDescription('');
      setShowPresetModal(false);
    }
  };

  const activeFiltersCount =
    queryState.filters.length +
    (queryState.freeTextSearch ? 1 : 0) +
    queryState.selectedNamespaces.length +
    queryState.selectedServices.length;

  return (
    <>
      <Card className="mb-3">
        <Card.Header className="d-flex justify-content-between align-items-center py-2">
          <div>
            <strong>
              <i className="bi bi-funnel me-2"></i>
              Filters
            </strong>
            {activeFiltersCount > 0 && (
              <Badge bg="primary" className="ms-2">
                {activeFiltersCount}
              </Badge>
            )}
          </div>
          <div>
            {presets.length > 0 && (
              <Form.Select
                size="sm"
                className="d-inline-block w-auto me-2"
                value=""
                onChange={(e) => e.target.value && loadPreset(e.target.value)}
              >
                <option value="">Load Preset...</option>
                {presets.map((preset) => (
                  <option key={preset.id} value={preset.id}>
                    {preset.name}
                  </option>
                ))}
              </Form.Select>
            )}
            <Button variant="link" size="sm" onClick={() => setShowPresetModal(true)} className="py-0">
              <i className="bi bi-save"></i>
            </Button>
            <Button variant="link" size="sm" onClick={resetQuery} className="py-0">
              <i className="bi bi-x-circle"></i>
            </Button>
            <Button variant="link" size="sm" onClick={() => setShowBuilder(!showBuilder)} className="py-0">
              <i className={`bi bi-chevron-${showBuilder ? 'up' : 'down'}`}></i>
            </Button>
          </div>
        </Card.Header>

        <Collapse in={showBuilder}>
          <div>
            <Card.Body className="py-2">
              {/* Time Range Section - Compact horizontal layout */}
              <Row className="mb-2 g-2 align-items-end">
                <Col xs="auto">
                  <div className="d-flex gap-1 align-items-center">
                    <Button
                      variant={queryState.liveMode ? 'success' : 'outline-secondary'}
                      size="sm"
                      onClick={() => updateLiveMode(!queryState.liveMode)}
                      title={queryState.liveMode ? 'Live mode: Time window slides forward on refresh' : 'Static mode: Fixed time range'}
                      style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem', fontWeight: 'bold' }}
                    >
                      <i className={`bi bi-${queryState.liveMode ? 'broadcast' : 'pause-circle'} me-1`}></i>
                      {queryState.liveMode ? 'LIVE' : 'PAUSED'}
                    </Button>
                    <div className="vr" style={{ height: '20px' }}></div>
                    {TIME_RANGES.map((range) => (
                      <Button
                        key={range.minutes}
                        variant={queryState.liveMode && queryState.relativeMinutes === range.minutes ? 'primary' : 'outline-secondary'}
                        size="sm"
                        onClick={() => handleTimeRangePreset(range.minutes)}
                        style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                      >
                        {range.label.replace('Last ', '')}
                      </Button>
                    ))}
                  </div>
                </Col>
                <Col md={2}>
                  <Form.Control
                    type="datetime-local"
                    size="sm"
                    value={new Date(queryState.timeRange.start_time).toISOString().slice(0, 16)}
                    onChange={(e) =>
                      updateTimeRange({
                        ...queryState.timeRange,
                        start_time: new Date(e.target.value).toISOString(),
                      })
                    }
                  />
                </Col>
                <Col md={2}>
                  <Form.Control
                    type="datetime-local"
                    size="sm"
                    value={new Date(queryState.timeRange.end_time).toISOString().slice(0, 16)}
                    onChange={(e) =>
                      updateTimeRange({
                        ...queryState.timeRange,
                        end_time: new Date(e.target.value).toISOString(),
                      })
                    }
                  />
                </Col>
                <Col md="auto">
                  <Form.Select size="sm" value={queryState.timeField} onChange={(e) => updateTimeField(e.target.value as any)}>
                    <option value="db_time">DB Time</option>
                    <option value="event_time">Event</option>
                    <option value="observed_time">Observed</option>
                  </Form.Select>
                </Col>
                <Col md="auto">
                  <Form.Select size="sm" value={queryState.timezone} onChange={(e) => updateTimezone(e.target.value)}>
                    <option value="local">Local</option>
                    <option value="UTC">UTC</option>
                    <option value="America/New_York">ET</option>
                    <option value="America/Chicago">CT</option>
                    <option value="America/Los_Angeles">PT</option>
                    <option value="Europe/London">London</option>
                    <option value="Asia/Tokyo">Tokyo</option>
                  </Form.Select>
                </Col>
              </Row>

              <hr className="my-2" />

              {/* Quick Filters - Compact single row */}
              <Row className="mb-2 g-2">
                {availableNamespaces.length > 0 && (
                  <Col md={3}>
                    <Form.Select
                      size="sm"
                      multiple
                      value={queryState.selectedNamespaces}
                      onChange={(e) =>
                        updateSelectedNamespaces(Array.from(e.target.selectedOptions, (option) => option.value))
                      }
                      style={{ height: '60px' }}
                    >
                      <option disabled>-- Namespaces --</option>
                      {availableNamespaces.map((ns) => (
                        <option key={ns} value={ns}>
                          {ns}
                        </option>
                      ))}
                    </Form.Select>
                  </Col>
                )}
                {availableServices.length > 0 && (
                  <Col md={3}>
                    <Form.Select
                      size="sm"
                      multiple
                      value={queryState.selectedServices}
                      onChange={(e) =>
                        updateSelectedServices(Array.from(e.target.selectedOptions, (option) => option.value))
                      }
                      style={{ height: '60px' }}
                    >
                      <option disabled>-- Services --</option>
                      {availableServices.map((svc) => (
                        <option key={svc} value={svc}>
                          {svc}
                        </option>
                      ))}
                    </Form.Select>
                  </Col>
                )}
                {showFreeTextSearch && (
                  <Col md={6}>
                    <InputGroup size="sm">
                      <InputGroup.Text>
                        <i className="bi bi-search"></i>
                      </InputGroup.Text>
                      <Form.Control
                        type="text"
                        placeholder="Search in body, attributes..."
                        value={queryState.freeTextSearch}
                        onChange={(e) => updateFreeTextSearch(e.target.value)}
                      />
                    </InputGroup>
                  </Col>
                )}
              </Row>

              <hr className="my-3" />

              {/* Saved Presets */}
              {presets.length > 0 && (
                <div className="mb-3">
                  <h6 className="mb-2">Saved Presets</h6>
                  <div className="d-flex flex-wrap gap-2">
                    {presets.map((preset) => (
                      <Button
                        key={preset.id}
                        variant="outline-secondary"
                        size="sm"
                        onClick={() => loadPreset(preset.id)}
                        className="d-flex align-items-center"
                      >
                        <span>{preset.name}</span>
                        <Badge
                          bg="danger"
                          className="ms-2"
                          style={{ cursor: 'pointer' }}
                          onClick={(e) => {
                            e.stopPropagation();
                            deletePreset(preset.id);
                          }}
                        >
                          <i className="bi bi-x"></i>
                        </Badge>
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              <hr className="my-3" />

              {/* Advanced Filters - react-querybuilder */}
              <div className="mb-3">
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <h6 className="mb-0">
                    <Button variant="link" size="sm" onClick={() => setShowAdvanced(!showAdvanced)} className="p-0">
                      <i className={`bi bi-chevron-${showAdvanced ? 'down' : 'right'} me-1`}></i>
                      Advanced Filters
                    </Button>
                  </h6>
                </div>

                <Collapse in={showAdvanced}>
                  <div>
                    <QueryBuilderWrapper
                      fieldSchema={fieldSchema}
                      filters={queryState.filters}
                      onFiltersChange={updateFilters}
                    />
                  </div>
                </Collapse>
              </div>

              <div className="mt-2 text-muted" style={{ fontSize: '0.75rem' }}>
                <i className="bi bi-info-circle me-1"></i>
                Use the query builder to create complex filters. Supports AND/OR logic and nested groups.
              </div>
            </Card.Body>
          </div>
        </Collapse>
      </Card>

      {/* Save Preset Modal */}
      <Modal show={showPresetModal} onHide={() => setShowPresetModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Save Query Preset</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Preset Name</Form.Label>
              <Form.Control
                type="text"
                placeholder="e.g., Error Traces Last Hour"
                value={presetName}
                onChange={(e) => setPresetName(e.target.value)}
                autoFocus
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Description (Optional)</Form.Label>
              <Form.Control
                as="textarea"
                rows={2}
                placeholder="Brief description of this query..."
                value={presetDescription}
                onChange={(e) => setPresetDescription(e.target.value)}
              />
            </Form.Group>
            <Alert variant="info" className="small">
              <i className="bi bi-info-circle me-2"></i>
              This preset will save all current filters, time range, timezone, and selected services/namespaces.
            </Alert>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowPresetModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSavePreset} disabled={!presetName.trim()}>
            Save Preset
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}

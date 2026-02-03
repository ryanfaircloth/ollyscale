import { useState } from 'react';
import { Offcanvas, Button, Form, InputGroup, Modal, Alert, ButtonGroup, Card } from 'react-bootstrap';
import { useQuery } from '@/contexts/QueryContext';
import { QueryBuilderWrapper } from './QueryBuilderWrapper';
import { type FieldSchema } from './QueryBuilder';
import { QuerySummary } from './QuerySummary';

interface CompactQueryBuilderProps {
  fieldSchema: FieldSchema[];
  availableNamespaces?: string[];
  availableServices?: string[];
  showFreeTextSearch?: boolean;
}

const TIME_RANGES = [
  { label: '5m', minutes: 5 },
  { label: '15m', minutes: 15 },
  { label: '30m', minutes: 30 },
  { label: '1h', minutes: 60 },
  { label: '3h', minutes: 180 },
  { label: '6h', minutes: 360 },
  { label: '12h', minutes: 720 },
  { label: '24h', minutes: 1440 },
];

/**
 * Compact query builder with slide-out panel
 * Shows summary badges when collapsed, full builder in Offcanvas when expanded
 */
export function CompactQueryBuilder({
  fieldSchema,
  availableNamespaces = [],
  availableServices = [],
  showFreeTextSearch = true,
}: CompactQueryBuilderProps) {
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

  const [showBuilder, setShowBuilder] = useState(false);
  const [showPresetModal, setShowPresetModal] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [presetDescription, setPresetDescription] = useState('');

  const handleTimeRangePreset = (minutes: number) => {
    const end = new Date();
    const start = new Date(end.getTime() - minutes * 60 * 1000);
    updateTimeRange(
      {
        start_time: start.toISOString(),
        end_time: end.toISOString(),
      },
      true // Enable live mode
    );
  };

  const handleSavePreset = () => {
    if (presetName.trim()) {
      savePreset(presetName.trim(), presetDescription.trim() || undefined);
      setPresetName('');
      setPresetDescription('');
      setShowPresetModal(false);
    }
  };

  return (
    <>
      {/* Compact summary view */}
      <div className="border-bottom bg-body-tertiary px-3">
        <QuerySummary onExpand={() => setShowBuilder(true)} />
      </div>

      {/* Slide-out query builder */}
      <Offcanvas
        show={showBuilder}
        onHide={() => setShowBuilder(false)}
        placement="end"
        style={{ width: '600px' }}
      >
        <Offcanvas.Header closeButton>
          <Offcanvas.Title>
            <i className="bi bi-funnel me-2"></i>
            Query Builder
          </Offcanvas.Title>
        </Offcanvas.Header>
        <Offcanvas.Body>
          {/* Mode Selection: Live vs Historical */}
          <Card className="mb-3">
            <Card.Body className="py-2">
              <div className="d-flex align-items-center justify-content-between mb-2">
                <small className="text-muted">
                  <strong>Query Mode</strong>
                </small>
                <ButtonGroup size="sm">
                  <Button
                    variant={queryState.liveMode ? 'success' : 'outline-secondary'}
                    onClick={() => updateLiveMode(true)}
                  >
                    <i className="bi bi-broadcast me-1"></i>
                    Live
                  </Button>
                  <Button
                    variant={!queryState.liveMode ? 'primary' : 'outline-secondary'}
                    onClick={() => updateLiveMode(false)}
                  >
                    <i className="bi bi-pause-circle me-1"></i>
                    Historical
                  </Button>
                </ButtonGroup>
              </div>
              <Alert variant={queryState.liveMode ? 'success' : 'info'} className="mb-0 py-2 small">
                <i className={`bi bi-${queryState.liveMode ? 'info-circle' : 'clock-history'} me-1`}></i>
                {queryState.liveMode ? (
                  <>
                    <strong>Live mode:</strong> Time window automatically slides forward on refresh. Select relative time
                    ranges below.
                  </>
                ) : (
                  <>
                    <strong>Historical mode:</strong> Fixed time range. Auto-refresh is disabled. Select exact start/end
                    times.
                  </>
                )}
              </Alert>
            </Card.Body>
          </Card>

          {/* Time Range Configuration */}
          <Card className="mb-3">
            <Card.Header className="py-2">
              <strong>Time Range</strong>
            </Card.Header>
            <Card.Body>
              {queryState.liveMode ? (
                <>
                  {/* Live Mode: Relative Time Ranges */}
                  <Form.Label className="small text-muted">Relative Time Window</Form.Label>
                  <div className="d-flex flex-wrap gap-2 mb-3">
                    {TIME_RANGES.map((range) => (
                      <Button
                        key={range.minutes}
                        variant={queryState.relativeMinutes === range.minutes ? 'primary' : 'outline-secondary'}
                        size="sm"
                        onClick={() => handleTimeRangePreset(range.minutes)}
                      >
                        Last {range.label}
                      </Button>
                    ))}
                  </div>
                </>
              ) : (
                <>
                  {/* Historical Mode: Fixed Time Range */}
                  <Form.Group className="mb-2">
                    <Form.Label className="small text-muted">Start Time</Form.Label>
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
                  </Form.Group>
                  <Form.Group className="mb-3">
                    <Form.Label className="small text-muted">End Time</Form.Label>
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
                  </Form.Group>
                </>
              )}

              {/* Time Field Selection */}
              <Form.Group className="mb-2">
                <Form.Label className="small text-muted">
                  Time Field
                  <i
                    className="bi bi-info-circle ms-1"
                    title="Which timestamp field to use for filtering"
                  ></i>
                </Form.Label>
                <Form.Select
                  size="sm"
                  value={queryState.timeField}
                  onChange={(e) => updateTimeField(e.target.value as any)}
                >
                  <option value="event_time">Event Time (recommended)</option>
                  <option value="db_time">Database Time</option>
                  <option value="observed_time">Observed Time</option>
                </Form.Select>
                <Form.Text className="text-muted">
                  {queryState.timeField === 'event_time' && 'When the event actually occurred'}
                  {queryState.timeField === 'db_time' && 'When the event was stored in the database'}
                  {queryState.timeField === 'observed_time' && 'When the event was observed by the collector'}
                </Form.Text>
              </Form.Group>

              {/* Timezone */}
              <Form.Group>
                <Form.Label className="small text-muted">Timezone</Form.Label>
                <Form.Select size="sm" value={queryState.timezone} onChange={(e) => updateTimezone(e.target.value)}>
                  <option value="local">Local</option>
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">Eastern Time</option>
                  <option value="America/Chicago">Central Time</option>
                  <option value="America/Los_Angeles">Pacific Time</option>
                  <option value="Europe/London">London</option>
                  <option value="Asia/Tokyo">Tokyo</option>
                </Form.Select>
              </Form.Group>
            </Card.Body>
          </Card>

          {/* Quick Filters */}
          <Card className="mb-3">
            <Card.Header className="py-2">
              <strong>Quick Filters</strong>
            </Card.Header>
            <Card.Body>
              {availableNamespaces.length > 0 && (
                <Form.Group className="mb-2">
                  <Form.Label className="small text-muted">Namespaces</Form.Label>
                  <Form.Select
                    size="sm"
                    multiple
                    value={queryState.selectedNamespaces}
                    onChange={(e) =>
                      updateSelectedNamespaces(Array.from(e.target.selectedOptions, (option) => option.value))
                    }
                    style={{ height: '80px' }}
                  >
                    {availableNamespaces.map((ns) => (
                      <option key={ns} value={ns}>
                        {ns}
                      </option>
                    ))}
                  </Form.Select>
                  <Form.Text className="text-muted">Hold Ctrl/Cmd to select multiple</Form.Text>
                </Form.Group>
              )}

              {availableServices.length > 0 && (
                <Form.Group className="mb-2">
                  <Form.Label className="small text-muted">Services</Form.Label>
                  <Form.Select
                    size="sm"
                    multiple
                    value={queryState.selectedServices}
                    onChange={(e) =>
                      updateSelectedServices(Array.from(e.target.selectedOptions, (option) => option.value))
                    }
                    style={{ height: '80px' }}
                  >
                    {availableServices.map((svc) => (
                      <option key={svc} value={svc}>
                        {svc}
                      </option>
                    ))}
                  </Form.Select>
                  <Form.Text className="text-muted">Hold Ctrl/Cmd to select multiple</Form.Text>
                </Form.Group>
              )}

              {showFreeTextSearch && (
                <Form.Group>
                  <Form.Label className="small text-muted">Text Search</Form.Label>
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
                </Form.Group>
              )}
            </Card.Body>
          </Card>

          {/* Advanced Filters */}
          <Card className="mb-3">
            <Card.Header className="py-2">
              <strong>Advanced Filters</strong>
            </Card.Header>
            <Card.Body>
              <QueryBuilderWrapper
                fieldSchema={fieldSchema}
                filters={queryState.filters}
                onFiltersChange={updateFilters}
              />
            </Card.Body>
          </Card>

          {/* Saved Presets */}
          <Card className="mb-3">
            <Card.Header className="py-2 d-flex justify-content-between align-items-center">
              <strong>Saved Presets</strong>
              <Button variant="outline-success" size="sm" onClick={() => setShowPresetModal(true)}>
                <i className="bi bi-save me-1"></i>
                Save Current
              </Button>
            </Card.Header>
            <Card.Body>
              {presets.length === 0 ? (
                <div className="text-center text-muted py-3">
                  <i className="bi bi-bookmark display-4 d-block mb-2" style={{ opacity: 0.3 }}></i>
                  <small>No saved presets</small>
                </div>
              ) : (
                <div className="d-flex flex-column gap-2">
                  {presets.map((preset) => (
                    <Card key={preset.id} className="border">
                      <Card.Body className="py-2 px-3 d-flex justify-content-between align-items-center">
                        <div className="flex-grow-1" style={{ cursor: 'pointer' }} onClick={() => loadPreset(preset.id)}>
                          <strong>{preset.name}</strong>
                          {preset.description && (
                            <div className="small text-muted">{preset.description}</div>
                          )}
                        </div>
                        <Button
                          variant="outline-danger"
                          size="sm"
                          onClick={() => deletePreset(preset.id)}
                          title="Delete preset"
                        >
                          <i className="bi bi-trash"></i>
                        </Button>
                      </Card.Body>
                    </Card>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>

          {/* Actions */}
          <div className="d-flex justify-content-between">
            <Button variant="outline-secondary" onClick={resetQuery}>
              <i className="bi bi-x-circle me-1"></i>
              Reset All
            </Button>
            <Button variant="primary" onClick={() => setShowBuilder(false)}>
              <i className="bi bi-check-lg me-1"></i>
              Apply & Close
            </Button>
          </div>
        </Offcanvas.Body>
      </Offcanvas>

      {/* Save Preset Modal */}
      <Modal show={showPresetModal} onHide={() => setShowPresetModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Save Query Preset</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Preset Name</Form.Label>
            <Form.Control
              type="text"
              placeholder="e.g., Errors in Production"
              value={presetName}
              onChange={(e) => setPresetName(e.target.value)}
              autoFocus
            />
          </Form.Group>
          <Form.Group>
            <Form.Label>Description (optional)</Form.Label>
            <Form.Control
              as="textarea"
              rows={2}
              placeholder="Brief description of this query..."
              value={presetDescription}
              onChange={(e) => setPresetDescription(e.target.value)}
            />
          </Form.Group>
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

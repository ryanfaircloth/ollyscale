import { useState } from 'react';
import { Card, Button, Form, Row, Col, Badge } from 'react-bootstrap';
import { type Filter } from '@/api/types/common';

interface QueryBuilderProps {
  onFiltersChange: (filters: Filter[]) => void;
  fieldSchema: FieldSchema[];
  initialFilters?: Filter[];
}

export interface FieldSchema {
  field: string;
  label: string;
  type: 'string' | 'number' | 'boolean' | 'enum';
  enumValues?: string[];
  description?: string;
}

const OPERATORS = {
  string: [
    { value: 'eq', label: 'equals' },
    { value: 'ne', label: 'not equals' },
    { value: 'contains', label: 'contains' },
    { value: 'regex', label: 'regex' },
  ],
  number: [
    { value: 'eq', label: 'equals' },
    { value: 'ne', label: 'not equals' },
    { value: 'gt', label: 'greater than' },
    { value: 'gte', label: 'greater than or equal' },
    { value: 'lt', label: 'less than' },
    { value: 'lte', label: 'less than or equal' },
  ],
  boolean: [
    { value: 'eq', label: 'equals' },
    { value: 'ne', label: 'not equals' },
  ],
  enum: [
    { value: 'eq', label: 'equals' },
    { value: 'ne', label: 'not equals' },
  ],
};

export function QueryBuilder({ onFiltersChange, fieldSchema, initialFilters = [] }: QueryBuilderProps) {
  const [filters, setFilters] = useState<Filter[]>(initialFilters);
  const [showBuilder, setShowBuilder] = useState(false);

  const addFilter = () => {
    const newFilter: Filter = {
      field: fieldSchema[0]?.field || '',
      operator: 'eq',
      value: '',
    };
    const newFilters = [...filters, newFilter];
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const removeFilter = (index: number) => {
    const newFilters = filters.filter((_, i) => i !== index);
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const updateFilter = (index: number, updates: Partial<Filter>) => {
    const newFilters = filters.map((filter, i) => (i === index ? { ...filter, ...updates } : filter));
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const clearAll = () => {
    setFilters([]);
    onFiltersChange([]);
  };

  const getFieldType = (fieldName: string): FieldSchema['type'] => {
    return fieldSchema.find((f) => f.field === fieldName)?.type || 'string';
  };

  const getFieldEnumValues = (fieldName: string): string[] | undefined => {
    return fieldSchema.find((f) => f.field === fieldName)?.enumValues;
  };

  const getOperatorsForField = (fieldName: string) => {
    const fieldType = getFieldType(fieldName);
    return OPERATORS[fieldType] || OPERATORS.string;
  };

  return (
    <Card className="mb-3">
      <Card.Header className="d-flex justify-content-between align-items-center">
        <div>
          <strong>
            <i className="bi bi-funnel me-2"></i>
            Query Builder
          </strong>
          {filters.length > 0 && (
            <Badge bg="primary" className="ms-2">
              {filters.length} filter{filters.length !== 1 ? 's' : ''}
            </Badge>
          )}
        </div>
        <div>
          <Button variant="link" size="sm" onClick={() => setShowBuilder(!showBuilder)}>
            {showBuilder ? 'Hide' : 'Show'}
          </Button>
        </div>
      </Card.Header>

      {showBuilder && (
        <Card.Body>
          {filters.length === 0 ? (
            <div className="text-center text-muted py-3">
              <i className="bi bi-funnel fs-1"></i>
              <p className="mt-2 mb-0">No filters applied. Click "Add Filter" to begin.</p>
            </div>
          ) : (
            <div>
              {filters.map((filter, index) => {
                const fieldType = getFieldType(filter.field);
                const enumValues = getFieldEnumValues(filter.field);
                const operators = getOperatorsForField(filter.field);

                return (
                  <Row key={index} className="mb-3 align-items-end">
                    <Col md={4}>
                      <Form.Group>
                        <Form.Label className="small text-muted">Field</Form.Label>
                        <Form.Select
                          size="sm"
                          value={filter.field}
                          onChange={(e) => updateFilter(index, { field: e.target.value })}
                        >
                          {fieldSchema.map((field) => (
                            <option key={field.field} value={field.field}>
                              {field.label}
                            </option>
                          ))}
                        </Form.Select>
                      </Form.Group>
                    </Col>

                    <Col md={3}>
                      <Form.Group>
                        <Form.Label className="small text-muted">Operator</Form.Label>
                        <Form.Select
                          size="sm"
                          value={filter.operator}
                          onChange={(e) =>
                            updateFilter(index, {
                              operator: e.target.value as Filter['operator'],
                            })
                          }
                        >
                          {operators.map((op) => (
                            <option key={op.value} value={op.value}>
                              {op.label}
                            </option>
                          ))}
                        </Form.Select>
                      </Form.Group>
                    </Col>

                    <Col md={4}>
                      <Form.Group>
                        <Form.Label className="small text-muted">Value</Form.Label>
                        {fieldType === 'enum' && enumValues ? (
                          <Form.Select
                            size="sm"
                            value={String(filter.value)}
                            onChange={(e) => updateFilter(index, { value: e.target.value })}
                          >
                            {enumValues.map((val) => (
                              <option key={val} value={val}>
                                {val}
                              </option>
                            ))}
                          </Form.Select>
                        ) : fieldType === 'boolean' ? (
                          <Form.Select
                            size="sm"
                            value={String(filter.value)}
                            onChange={(e) => updateFilter(index, { value: e.target.value === 'true' })}
                          >
                            <option value="true">true</option>
                            <option value="false">false</option>
                          </Form.Select>
                        ) : fieldType === 'number' ? (
                          <Form.Control
                            size="sm"
                            type="number"
                            value={String(filter.value)}
                            onChange={(e) => updateFilter(index, { value: Number(e.target.value) })}
                          />
                        ) : (
                          <Form.Control
                            size="sm"
                            type="text"
                            value={String(filter.value)}
                            onChange={(e) => updateFilter(index, { value: e.target.value })}
                            placeholder="Enter value..."
                          />
                        )}
                      </Form.Group>
                    </Col>

                    <Col md={1}>
                      <Button variant="outline-danger" size="sm" onClick={() => removeFilter(index)}>
                        <i className="bi bi-trash"></i>
                      </Button>
                    </Col>
                  </Row>
                );
              })}
            </div>
          )}

          <div className="d-flex gap-2 mt-3">
            <Button variant="outline-primary" size="sm" onClick={addFilter}>
              <i className="bi bi-plus-circle me-1"></i>
              Add Filter
            </Button>
            {filters.length > 0 && (
              <Button variant="outline-secondary" size="sm" onClick={clearAll}>
                <i className="bi bi-x-circle me-1"></i>
                Clear All
              </Button>
            )}
          </div>

          <div className="mt-3 text-muted small">
            <i className="bi bi-info-circle me-1"></i>
            Filters are combined with AND logic. Use regex for pattern matching (e.g., <code>^error.*</code>).
          </div>
        </Card.Body>
      )}
    </Card>
  );
}

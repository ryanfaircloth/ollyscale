import { QueryBuilder as RQB, type Field, type RuleGroupType } from 'react-querybuilder';
import { QueryBuilderBootstrap } from '@react-querybuilder/bootstrap';
import { type Filter } from '@/api/types/common';
import 'react-querybuilder/dist/query-builder.css';

export interface FieldSchema {
  field: string;
  label: string;
  type: 'string' | 'number' | 'boolean' | 'enum';
  enumValues?: string[];
  description?: string;
}

interface QueryBuilderWrapperProps {
  fieldSchema: FieldSchema[];
  filters: Filter[];
  onFiltersChange: (filters: Filter[]) => void;
}

// Convert our FieldSchema to react-querybuilder Field format
function schemaToFields(schema: FieldSchema[]): Field[] {
  return schema.map((s) => ({
    name: s.field,
    label: s.label,
    inputType: s.type === 'number' ? 'number' : s.type === 'boolean' ? 'checkbox' : 'text',
    valueEditorType: s.type === 'enum' ? 'select' : undefined,
    values: s.enumValues?.map((v) => ({ name: v, label: v })),
    validator: s.type === 'number' ? (r) => {
      if (r.value && isNaN(Number(r.value))) {
        return { valid: false, reasons: ['Must be a number'] };
      }
      return true;
    } : undefined,
  }));
}

// Convert our Filter[] to RuleGroupType
function filtersToQuery(filters: Filter[]): RuleGroupType {
  return {
    combinator: 'and',
    rules: filters.map((f) => ({
      field: f.field,
      operator: f.operator,
      value: f.value,
    })),
  };
}

// Convert RuleGroupType back to Filter[]
function queryToFilters(query: RuleGroupType): Filter[] {
  const filters: Filter[] = [];

  function extractRules(group: RuleGroupType) {
    for (const rule of group.rules) {
      if ('field' in rule && 'operator' in rule && 'value' in rule) {
        // It's a rule, not a group
        filters.push({
          field: rule.field,
          operator: rule.operator as Filter['operator'],
          value: rule.value,
        });
      } else if ('combinator' in rule && 'rules' in rule) {
        // It's a nested group
        extractRules(rule as RuleGroupType);
      }
    }
  }

  extractRules(query);
  return filters;
}

export function QueryBuilderWrapper({ fieldSchema, filters, onFiltersChange }: QueryBuilderWrapperProps) {
  const fields = schemaToFields(fieldSchema);
  const query = filtersToQuery(filters);

  const handleQueryChange = (newQuery: RuleGroupType) => {
    const newFilters = queryToFilters(newQuery);
    onFiltersChange(newFilters);
  };

  return (
    <QueryBuilderBootstrap>
      <RQB
        fields={fields}
        query={query}
        onQueryChange={handleQueryChange}
        showCombinatorsBetweenRules
        showNotToggle
        addRuleToNewGroups
        controlClassnames={{
          queryBuilder: 'query-builder-bootstrap',
        }}
      />
    </QueryBuilderBootstrap>
  );
}

#!/usr/bin/env python3
"""
Generate attribute_keys table population and typed attribute table schemas
based on the analysis from attribute-key-analysis.sql

This script reads analysis results and generates:
1. INSERT statements for attribute_keys table
2. CREATE TABLE statements for type-specific attribute tables
3. Migration scripts for moving data from JSONB to typed tables

Usage:
    # Run analysis first
    psql -f attribute-key-analysis.sql > analysis_results.txt

    # Then use those results to generate schema
    python generate-attribute-schema.py --analysis analysis_results.txt
"""

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AttributeKey:
    """Represents a discovered attribute key."""

    key: str
    value_type: str  # string, number, boolean, array, object
    total_occurrences: int
    max_distinct_values: int
    contexts: set[str]  # resource, scope, span, log, metric
    is_indexed: bool = False
    is_searchable: bool = False


def map_jsonb_type_to_sql(jsonb_type: str) -> str:
    """Map JSONB type to SQL type."""
    mapping = {
        "string": "TEXT",
        "number": "DOUBLE PRECISION",  # Use double for all numbers, can cast to BIGINT if needed
        "boolean": "BOOLEAN",
        "array": "JSONB",  # Keep arrays in JSONB
        "object": "JSONB",  # Keep objects in JSONB
    }
    return mapping.get(jsonb_type, "JSONB")


def map_jsonb_type_to_table_suffix(jsonb_type: str) -> str:
    """Map JSONB type to table name suffix."""
    mapping = {
        "string": "string",
        "number": "double",  # Default to double, can create separate int table if needed
        "boolean": "bool",
    }
    return mapping.get(jsonb_type)


def should_promote_to_typed_table(attr: AttributeKey, occurrence_threshold: int = 1000) -> bool:
    """Determine if an attribute should be promoted to a typed table."""
    # Only promote simple types (not arrays or objects)
    if attr.value_type in ("array", "object"):
        return False

    # Must exceed occurrence threshold
    return not attr.total_occurrences < occurrence_threshold


def generate_attribute_keys_inserts(attributes: list[AttributeKey], promoted_only: bool = False) -> str:
    """Generate INSERT statements for attribute_keys table."""
    sql_parts = [
        "-- Populate attribute_keys table",
        "-- Pre-populate with discovered keys from current database",
        "",
        "INSERT INTO attribute_keys (key, value_type, is_indexed, is_searchable) VALUES",
    ]

    inserts = []
    for attr in attributes:
        if promoted_only and not should_promote_to_typed_table(attr):
            continue

        # Determine if should be indexed based on cardinality
        is_indexed = attr.max_distinct_values < 10000
        is_searchable = attr.total_occurrences > 100

        # Map JSONB type to our internal type
        type_map = {
            "string": "string",
            "number": "double",
            "boolean": "bool",
            "array": "array",
            "object": "object",
        }
        internal_type = type_map.get(attr.value_type, attr.value_type)

        inserts.append(f"  ('{attr.key}', '{internal_type}', {str(is_indexed).lower()}, {str(is_searchable).lower()})")

    sql_parts.append(",\n".join(inserts))
    sql_parts.append("ON CONFLICT (key) DO UPDATE SET")
    sql_parts.append("  is_indexed = EXCLUDED.is_indexed,")
    sql_parts.append("  is_searchable = EXCLUDED.is_searchable;")
    sql_parts.append("")

    return "\n".join(sql_parts)


def generate_typed_attribute_tables(context: str, attributes: list[AttributeKey]) -> str:
    """Generate CREATE TABLE statements for type-specific attribute tables."""
    # Group by type
    by_type: dict[str, list[AttributeKey]] = {}
    for attr in attributes:
        if should_promote_to_typed_table(attr):
            type_suffix = map_jsonb_type_to_table_suffix(attr.value_type)
            if type_suffix:
                by_type.setdefault(type_suffix, []).append(attr)

    sql_parts = [f"-- Type-specific attribute tables for {context}"]

    # Create tables for each type
    for type_suffix, attrs in sorted(by_type.items()):
        table_name = f"{context}_attrs_{type_suffix}"
        sql_type = map_jsonb_type_to_sql(attrs[0].value_type)

        sql_parts.append("")
        sql_parts.append(f"CREATE TABLE {table_name} (")
        sql_parts.append(f"  {context}_id BIGINT NOT NULL,")
        sql_parts.append("  key_id INT NOT NULL REFERENCES attribute_keys(key_id),")
        sql_parts.append(f"  value {sql_type} NOT NULL,")
        sql_parts.append(f"  PRIMARY KEY ({context}_id, key_id)")
        sql_parts.append(");")
        sql_parts.append("")
        sql_parts.append("-- Index for value lookups")
        sql_parts.append(f"CREATE INDEX idx_{table_name}_value ON {table_name}(key_id, value);")

    # Create catch-all JSONB table
    sql_parts.append("")
    sql_parts.append("-- Catch-all for unpromoted attributes")
    sql_parts.append(f"CREATE TABLE {context}_attrs_other (")
    sql_parts.append(f"  {context}_id BIGINT PRIMARY KEY,")
    sql_parts.append("  attributes JSONB NOT NULL DEFAULT '{}'")
    sql_parts.append(");")
    sql_parts.append("")
    sql_parts.append(f"CREATE INDEX idx_{context}_attrs_other_gin ON {context}_attrs_other USING GIN(attributes);")
    sql_parts.append("")

    return "\n".join(sql_parts)


def generate_migration_script(
    context: str, attributes: list[AttributeKey], source_table: str, source_column: str
) -> str:
    """Generate migration SQL to move data from JSONB to typed tables."""
    promoted = [a for a in attributes if should_promote_to_typed_table(a)]
    by_type: dict[str, list[AttributeKey]] = {}
    for attr in promoted:
        type_suffix = map_jsonb_type_to_table_suffix(attr.value_type)
        if type_suffix:
            by_type.setdefault(type_suffix, []).append(attr)

    sql_parts = [f"-- Migrate {context} attributes from {source_table}.{source_column}", ""]

    # Generate migration for each type
    for type_suffix, attrs in sorted(by_type.items()):
        table_name = f"{context}_attrs_{type_suffix}"
        keys = [f"'{a.key}'" for a in attrs]

        sql_parts.append(f"-- Migrate {type_suffix} attributes")
        sql_parts.append(f"INSERT INTO {table_name} ({context}_id, key_id, value)")
        sql_parts.append("SELECT")
        sql_parts.append(f"  s.id as {context}_id,")
        sql_parts.append("  ak.key_id,")

        # Type-specific value extraction
        if type_suffix == "string":
            sql_parts.append("  attr.value #>> '{}' as value")
        elif type_suffix == "double":
            sql_parts.append("  (attr.value #>> '{}')::double precision as value")
        elif type_suffix == "bool":
            sql_parts.append("  (attr.value #>> '{}')::boolean as value")

        sql_parts.append(f"FROM {source_table} s,")
        sql_parts.append(f"  LATERAL jsonb_each(s.{source_column}) as attr(key, value)")
        sql_parts.append("  JOIN attribute_keys ak ON ak.key = attr.key")
        sql_parts.append(f"WHERE s.{source_column} IS NOT NULL")
        sql_parts.append(f"  AND attr.key IN ({', '.join(keys)})")
        sql_parts.append(f"  AND jsonb_typeof(attr.value) = '{attrs[0].value_type}'")
        sql_parts.append(f"ON CONFLICT ({context}_id, key_id) DO UPDATE SET value = EXCLUDED.value;")
        sql_parts.append("")

    # Generate catch-all migration
    sql_parts.append("-- Migrate remaining attributes to catch-all JSONB table")
    promoted_keys = [f"'{a.key}'" for a in promoted]

    sql_parts.append(f"INSERT INTO {context}_attrs_other ({context}_id, attributes)")
    sql_parts.append("SELECT")
    sql_parts.append(f"  id as {context}_id,")

    if promoted_keys:
        # Remove promoted keys from JSONB
        sql_parts.append(f"  ({source_column} - ARRAY[{', '.join(promoted_keys)}]) as attributes")
    else:
        sql_parts.append(f"  {source_column} as attributes")

    sql_parts.append(f"FROM {source_table}")
    sql_parts.append(f"WHERE {source_column} IS NOT NULL")
    sql_parts.append(f"  AND {source_column} != '{{}}'::jsonb")
    sql_parts.append(f"ON CONFLICT ({context}_id) DO UPDATE SET attributes = EXCLUDED.attributes;")
    sql_parts.append("")

    return "\n".join(sql_parts)


def main():
    parser = argparse.ArgumentParser(description="Generate attribute schema from analysis results")
    parser.add_argument(
        "--occurrence-threshold",
        type=int,
        default=1000,
        help="Minimum occurrences to promote to typed table (default: 1000)",
    )
    parser.add_argument(
        "--output",
        default="generated-attribute-schema.sql",
        help="Output SQL file (default: generated-attribute-schema.sql)",
    )

    args = parser.parse_args()

    # For now, generate example schema based on common OTEL semantic conventions
    # In production, this would read from analysis results

    common_resource_attrs = [
        AttributeKey("service.name", "string", 50000, 50, {"resource"}, True, True),
        AttributeKey("service.namespace", "string", 50000, 10, {"resource"}, True, True),
        AttributeKey("service.version", "string", 50000, 100, {"resource"}, True, False),
        AttributeKey("service.instance.id", "string", 50000, 500, {"resource"}, True, True),
        AttributeKey("deployment.environment", "string", 50000, 5, {"resource"}, True, True),
        AttributeKey("host.name", "string", 30000, 100, {"resource"}, True, True),
        AttributeKey("host.arch", "string", 30000, 5, {"resource"}, True, False),
        AttributeKey("process.pid", "number", 30000, 5000, {"resource"}, False, False),
        AttributeKey("telemetry.sdk.name", "string", 50000, 5, {"resource"}, False, False),
        AttributeKey("telemetry.sdk.language", "string", 50000, 10, {"resource"}, False, False),
        AttributeKey("telemetry.sdk.version", "string", 50000, 20, {"resource"}, False, False),
    ]

    common_span_attrs = [
        AttributeKey("http.method", "string", 100000, 10, {"span"}, True, True),
        AttributeKey("http.status_code", "number", 100000, 100, {"span"}, True, True),
        AttributeKey("http.url", "string", 100000, 50000, {"span"}, False, True),
        AttributeKey("http.target", "string", 100000, 50000, {"span"}, False, True),
        AttributeKey("db.system", "string", 50000, 10, {"span"}, True, True),
        AttributeKey("db.name", "string", 50000, 50, {"span"}, True, True),
        AttributeKey("db.statement", "string", 50000, 10000, {"span"}, False, True),
        AttributeKey("messaging.system", "string", 30000, 5, {"span"}, True, True),
        AttributeKey("messaging.destination", "string", 30000, 100, {"span"}, True, True),
        AttributeKey("error", "boolean", 20000, 2, {"span"}, True, True),
    ]

    # Generate output
    with Path(args.output).open("w") as f:
        f.write("-- Generated Attribute Schema\n")
        f.write("-- This file was generated from attribute key analysis\n")
        f.write("--\n")
        f.write(f"-- Occurrence threshold: {args.occurrence_threshold}\n")
        f.write("--\n\n")

        # Create attribute_keys table
        f.write("-- =====================================================\n")
        f.write("-- Attribute Keys Registry\n")
        f.write("-- =====================================================\n\n")

        f.write("CREATE TABLE attribute_keys (\n")
        f.write("  key_id SERIAL PRIMARY KEY,\n")
        f.write("  key TEXT UNIQUE NOT NULL,\n")
        f.write("  description TEXT,\n")
        f.write("  value_type TEXT NOT NULL,\n")
        f.write("  is_indexed BOOLEAN DEFAULT false,\n")
        f.write("  is_searchable BOOLEAN DEFAULT false,\n")
        f.write("  created_at TIMESTAMPTZ DEFAULT NOW()\n")
        f.write(");\n\n")

        # Populate attribute_keys
        f.write(generate_attribute_keys_inserts(common_resource_attrs + common_span_attrs, promoted_only=True))
        f.write("\n\n")

        # Generate typed tables for each context
        for context in ["resource", "scope", "span", "log", "metric"]:
            f.write("-- =====================================================\n")
            f.write(f"-- {context.upper()} Attribute Tables\n")
            f.write("-- =====================================================\n\n")

            # Use appropriate attribute list
            if context == "resource":
                attrs = common_resource_attrs
            elif context == "span":
                attrs = common_span_attrs
            else:
                attrs = []  # Would be populated from analysis

            f.write(generate_typed_attribute_tables(context, attrs))
            f.write("\n\n")

        # Generate example migration for spans
        f.write("-- =====================================================\n")
        f.write("-- Migration Example: Span Attributes\n")
        f.write("-- =====================================================\n\n")
        f.write(generate_migration_script("span", common_span_attrs, "spans_fact", "attributes"))

    print(f"Generated schema written to {args.output}")
    print("\nSummary:")
    print(
        f"  Resource attributes promoted: {sum(1 for a in common_resource_attrs if should_promote_to_typed_table(a))}"
    )
    print(f"  Span attributes promoted: {sum(1 for a in common_span_attrs if should_promote_to_typed_table(a))}")
    print("\nNext steps:")
    print(f"  1. Review {args.output}")
    print("  2. Adjust attribute promotion decisions as needed")
    print("  3. Run against development database to test")
    print("  4. Create Alembic migration for production")


if __name__ == "__main__":
    main()

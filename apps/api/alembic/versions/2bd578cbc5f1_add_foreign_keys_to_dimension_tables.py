"""add foreign keys to dimension tables

Revision ID: 2bd578cbc5f1
Revises: c846417c2785
Create Date: 2026-02-04 15:44:33.652423

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bd578cbc5f1'
down_revision: Union[str, Sequence[str], None] = 'c846417c2785'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add foreign key constraints from fact tables to dimension tables.

    These foreign keys enforce referential integrity between:
    - Fact tables and their associated resources (resources_dim)
    - Fact tables and their instrumentation scopes (scopes_dim)
    - Metrics data points and metric metadata (metrics_dim)
    """

    # ========== SPANS_FACT FOREIGN KEYS ==========
    
    op.execute("""
        ALTER TABLE spans_fact 
        ADD CONSTRAINT fk_spans_resource 
        FOREIGN KEY (resource_id) 
        REFERENCES resources_dim(resource_id)
    """)
    
    op.execute("""
        ALTER TABLE spans_fact 
        ADD CONSTRAINT fk_spans_scope 
        FOREIGN KEY (scope_id) 
        REFERENCES scopes_dim(scope_id)
    """)

    # ========== LOGS_FACT FOREIGN KEYS ==========
    
    op.execute("""
        ALTER TABLE logs_fact 
        ADD CONSTRAINT fk_logs_resource 
        FOREIGN KEY (resource_id) 
        REFERENCES resources_dim(resource_id)
    """)
    
    op.execute("""
        ALTER TABLE logs_fact 
        ADD CONSTRAINT fk_logs_scope 
        FOREIGN KEY (scope_id) 
        REFERENCES scopes_dim(scope_id)
    """)

    # ========== METRICS DATA POINTS FOREIGN KEYS ==========
    
    # Number data points
    op.execute("""
        ALTER TABLE metrics_data_points_number 
        ADD CONSTRAINT fk_metrics_number_metric 
        FOREIGN KEY (metric_id) 
        REFERENCES metrics_dim(metric_id)
    """)
    
    op.execute("""
        ALTER TABLE metrics_data_points_number 
        ADD CONSTRAINT fk_metrics_number_resource 
        FOREIGN KEY (resource_id) 
        REFERENCES resources_dim(resource_id)
    """)
    
    op.execute("""
        ALTER TABLE metrics_data_points_number 
        ADD CONSTRAINT fk_metrics_number_scope 
        FOREIGN KEY (scope_id) 
        REFERENCES scopes_dim(scope_id)
    """)
    
    # Histogram data points
    op.execute("""
        ALTER TABLE metrics_data_points_histogram 
        ADD CONSTRAINT fk_metrics_histogram_metric 
        FOREIGN KEY (metric_id) 
        REFERENCES metrics_dim(metric_id)
    """)
    
    op.execute("""
        ALTER TABLE metrics_data_points_histogram 
        ADD CONSTRAINT fk_metrics_histogram_resource 
        FOREIGN KEY (resource_id) 
        REFERENCES resources_dim(resource_id)
    """)
    
    op.execute("""
        ALTER TABLE metrics_data_points_histogram 
        ADD CONSTRAINT fk_metrics_histogram_scope 
        FOREIGN KEY (scope_id) 
        REFERENCES scopes_dim(scope_id)
    """)
    
    # Exponential histogram data points
    op.execute("""
        ALTER TABLE metrics_data_points_exp_histogram 
        ADD CONSTRAINT fk_metrics_exp_histogram_metric 
        FOREIGN KEY (metric_id) 
        REFERENCES metrics_dim(metric_id)
    """)
    
    op.execute("""
        ALTER TABLE metrics_data_points_exp_histogram 
        ADD CONSTRAINT fk_metrics_exp_histogram_resource 
        FOREIGN KEY (resource_id) 
        REFERENCES resources_dim(resource_id)
    """)
    
    op.execute("""
        ALTER TABLE metrics_data_points_exp_histogram 
        ADD CONSTRAINT fk_metrics_exp_histogram_scope 
        FOREIGN KEY (scope_id) 
        REFERENCES scopes_dim(scope_id)
    """)
    
    # Summary data points
    op.execute("""
        ALTER TABLE metrics_data_points_summary 
        ADD CONSTRAINT fk_metrics_summary_metric 
        FOREIGN KEY (metric_id) 
        REFERENCES metrics_dim(metric_id)
    """)
    
    op.execute("""
        ALTER TABLE metrics_data_points_summary 
        ADD CONSTRAINT fk_metrics_summary_resource 
        FOREIGN KEY (resource_id) 
        REFERENCES resources_dim(resource_id)
    """)
    
    op.execute("""
        ALTER TABLE metrics_data_points_summary 
        ADD CONSTRAINT fk_metrics_summary_scope 
        FOREIGN KEY (scope_id) 
        REFERENCES scopes_dim(scope_id)
    """)


def downgrade() -> None:
    """Drop foreign key constraints to dimension tables."""
    
    # Spans
    op.execute("ALTER TABLE spans_fact DROP CONSTRAINT IF EXISTS fk_spans_scope")
    op.execute("ALTER TABLE spans_fact DROP CONSTRAINT IF EXISTS fk_spans_resource")
    
    # Logs
    op.execute("ALTER TABLE logs_fact DROP CONSTRAINT IF EXISTS fk_logs_scope")
    op.execute("ALTER TABLE logs_fact DROP CONSTRAINT IF EXISTS fk_logs_resource")
    
    # Metrics - Number
    op.execute("ALTER TABLE metrics_data_points_number DROP CONSTRAINT IF EXISTS fk_metrics_number_scope")
    op.execute("ALTER TABLE metrics_data_points_number DROP CONSTRAINT IF EXISTS fk_metrics_number_resource")
    op.execute("ALTER TABLE metrics_data_points_number DROP CONSTRAINT IF EXISTS fk_metrics_number_metric")
    
    # Metrics - Histogram
    op.execute("ALTER TABLE metrics_data_points_histogram DROP CONSTRAINT IF EXISTS fk_metrics_histogram_scope")
    op.execute("ALTER TABLE metrics_data_points_histogram DROP CONSTRAINT IF EXISTS fk_metrics_histogram_resource")
    op.execute("ALTER TABLE metrics_data_points_histogram DROP CONSTRAINT IF EXISTS fk_metrics_histogram_metric")
    
    # Metrics - Exponential Histogram
    op.execute("ALTER TABLE metrics_data_points_exp_histogram DROP CONSTRAINT IF EXISTS fk_metrics_exp_histogram_scope")
    op.execute("ALTER TABLE metrics_data_points_exp_histogram DROP CONSTRAINT IF EXISTS fk_metrics_exp_histogram_resource")
    op.execute("ALTER TABLE metrics_data_points_exp_histogram DROP CONSTRAINT IF EXISTS fk_metrics_exp_histogram_metric")
    
    # Metrics - Summary
    op.execute("ALTER TABLE metrics_data_points_summary DROP CONSTRAINT IF EXISTS fk_metrics_summary_scope")
    op.execute("ALTER TABLE metrics_data_points_summary DROP CONSTRAINT IF EXISTS fk_metrics_summary_resource")
    op.execute("ALTER TABLE metrics_data_points_summary DROP CONSTRAINT IF EXISTS fk_metrics_summary_metric")

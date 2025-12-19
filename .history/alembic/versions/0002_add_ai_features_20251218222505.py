"""Add AI embedding fields to media_items table

Revision ID: 0002_add_ai_features
Revises: 0001_initial_schema
Create Date: 2025-12-18 18:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_add_ai_features"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add AI/embedding columns to media_items table
    op.add_column(
        "media_items",
        sa.Column("semantic_embedding", sa.LargeBinary(), nullable=True),
    )
    op.add_column(
        "media_items",
        sa.Column("embedding_version", sa.String(64), nullable=True),
    )
    op.add_column(
        "media_items",
        sa.Column("ai_tags", sa.JSON(), nullable=True),
    )
    op.add_column(
        "media_items",
        sa.Column("visual_description", sa.String(1024), nullable=True),
    )
    op.add_column(
        "media_items",
        sa.Column(
            "embedding_processed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    
    # Create index on embedding_processed_at for efficient querying
    op.create_index(
        "ix_media_items_embedding_processed_at",
        "media_items",
        ["embedding_processed_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop the index
    op.drop_index(
        "ix_media_items_embedding_processed_at", table_name="media_items"
    )
    
    # Drop all AI/embedding columns
    op.drop_column("media_items", "embedding_processed_at")
    op.drop_column("media_items", "visual_description")
    op.drop_column("media_items", "ai_tags")
    op.drop_column("media_items", "embedding_version")
    op.drop_column("media_items", "semantic_embedding")

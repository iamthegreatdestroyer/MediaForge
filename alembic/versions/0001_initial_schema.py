"""Initial MediaForge database schema.

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2025-11-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:  # pragma: no cover - migration code
    op.create_table(
        "media_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("file_path", sa.String(), nullable=False, unique=True),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("file_hash", sa.String(length=128), nullable=False, unique=True),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column(
            "media_type",
            sa.Enum("video", "audio", "image", "document", "other", name="mediatype"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("modified_at", sa.DateTime(), nullable=False),
        sa.Column("file_created_at", sa.DateTime(), nullable=True),
        sa.Column("file_modified_at", sa.DateTime(), nullable=True),
        sa.Column("last_scanned_at", sa.DateTime(), nullable=True),
        sa.Column("is_processed", sa.Boolean(), nullable=False),
        sa.Column("is_compressed", sa.Boolean(), nullable=False),
        sa.Column("compression_ratio", sa.Float(), nullable=True),
    )
    op.create_index("ix_media_items_file_path", "media_items", ["file_path"], unique=True)
    op.create_index("ix_media_items_file_hash", "media_items", ["file_hash"], unique=True)
    op.create_index("ix_media_items_media_type", "media_items", ["media_type"], unique=False)
    op.create_index(
        "ix_media_items_media_type_created_at",
        "media_items",
        ["media_type", "created_at"],
        unique=False,
    )
    op.create_index("ix_media_items_created_at", "media_items", ["created_at"], unique=False)
    op.create_index("ix_media_items_is_processed", "media_items", ["is_processed"], unique=False)
    op.create_index("ix_media_items_mime_type", "media_items", ["mime_type"], unique=False)

    op.create_table(
        "tags",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("color", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("modified_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_tags_name", "tags", ["name"], unique=True)
    op.create_index("ix_tags_created_at", "tags", ["created_at"], unique=False)

    op.create_table(
        "collections",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("modified_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_collections_name", "collections", ["name"], unique=True)

    op.create_table(
        "media_metadata",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("media_item_id", sa.String(length=36), sa.ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("fps", sa.Float(), nullable=True),
        sa.Column("video_codec", sa.String(length=64), nullable=True),
        sa.Column("audio_codec", sa.String(length=64), nullable=True),
        sa.Column("bitrate", sa.Integer(), nullable=True),
        sa.Column("sample_rate", sa.Integer(), nullable=True),
        sa.Column("channels", sa.Integer(), nullable=True),
        sa.Column("artist", sa.String(length=256), nullable=True),
        sa.Column("album", sa.String(length=256), nullable=True),
        sa.Column("title", sa.String(length=256), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("genre", sa.String(length=128), nullable=True),
        sa.Column("camera_make", sa.String(length=128), nullable=True),
        sa.Column("camera_model", sa.String(length=128), nullable=True),
        sa.Column("iso", sa.Integer(), nullable=True),
        sa.Column("aperture", sa.Float(), nullable=True),
        sa.Column("shutter_speed", sa.String(length=32), nullable=True),
        sa.Column("focal_length", sa.Float(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("location_name", sa.String(length=256), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("modified_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_media_metadata_media_item_id", "media_metadata", ["media_item_id"], unique=False)
    op.create_index("ix_media_metadata_artist", "media_metadata", ["artist"], unique=False)
    op.create_index("ix_media_metadata_album", "media_metadata", ["album"], unique=False)
    op.create_index("ix_media_metadata_title", "media_metadata", ["title"], unique=False)
    op.create_index("ix_media_metadata_genre", "media_metadata", ["genre"], unique=False)

    op.create_table(
        "media_tags",
        sa.Column("media_item_id", sa.String(length=36), sa.ForeignKey("media_items.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.String(length=36), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "collection_items",
        sa.Column("collection_id", sa.String(length=36), sa.ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("media_item_id", sa.String(length=36), sa.ForeignKey("media_items.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("added_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:  # pragma: no cover - migration code
    op.drop_table("collection_items")
    op.drop_table("media_tags")
    op.drop_index("ix_media_metadata_genre", table_name="media_metadata")
    op.drop_index("ix_media_metadata_title", table_name="media_metadata")
    op.drop_index("ix_media_metadata_album", table_name="media_metadata")
    op.drop_index("ix_media_metadata_artist", table_name="media_metadata")
    op.drop_index("ix_media_metadata_media_item_id", table_name="media_metadata")
    op.drop_table("media_metadata")
    op.drop_index("ix_collections_name", table_name="collections")
    op.drop_table("collections")
    op.drop_index("ix_tags_created_at", table_name="tags")
    op.drop_index("ix_tags_name", table_name="tags")
    op.drop_table("tags")
    op.drop_index("ix_media_items_mime_type", table_name="media_items")
    op.drop_index("ix_media_items_is_processed", table_name="media_items")
    op.drop_index("ix_media_items_created_at", table_name="media_items")
    op.drop_index("ix_media_items_media_type_created_at", table_name="media_items")
    op.drop_index("ix_media_items_media_type", table_name="media_items")
    op.drop_index("ix_media_items_file_hash", table_name="media_items")
    op.drop_index("ix_media_items_file_path", table_name="media_items")
    op.drop_table("media_items")
    op.execute("DROP TABLE IF EXISTS alembic_version")  # optional cleanup
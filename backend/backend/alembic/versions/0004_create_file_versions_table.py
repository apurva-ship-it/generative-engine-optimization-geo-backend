"""Create file_versions table to store individual file versions metadata.

Revision ID: 0004_create_file_versions_table
Revises: 0003_create_files_table
Create Date: 2026-05-10 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import datetime

# revision identifiers, used by Alembic.
revision = "0004_create_file_versions_table"
down_revision = "0003_create_files_table"
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Create the file_versions table.

    Columns:
        - id: UUID primary key (stored as string UUID)
        - file_id: UUID foreign key to files.id
        - version_number: Integer, starts at 1
        - s3_key: string, location of the file version in S3
        - size: BigInteger, size in bytes
        - created_at: timestamp with timezone
    """
    op.create_table(
        "file_versions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("file_id", sa.String(length=36), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("s3_key", sa.String(length=512), nullable=False),
        sa.Column("size", sa.BigInteger, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            default=datetime.datetime.utcnow,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
    )
    # Indexes for fast look‑up
    op.create_index("ix_file_versions_file_id", "file_versions", ["file_id"])
    op.create_index("ix_file_versions_file_id_version", "file_versions", ["file_id", "version_number"], unique=True)

def downgrade() -> None:
    """Drop the file_versions table and its indexes."""
    op.drop_index("ix_file_versions_file_id_version", table_name="file_versions")
    op.drop_index("ix_file_versions_file_id", table_name="file_versions")
    op.drop_table("file_versions")

"""add_api_keys_and_mcp_logs

Revision ID: a1b2c3d4e5f6
Revises: 5ceea5ee0c9d
Create Date: 2026-01-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5ceea5ee0c9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('key_prefix', sa.String(8), nullable=False),  # "mn_live_" for identification
        sa.Column('key_hash', sa.String(64), nullable=False),  # SHA-256 hash
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('scopes', sa.String(50), nullable=False, server_default='read'),  # "read" or "read,write"
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),  # null = never
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),  # null = active
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('key_hash', name='uq_api_keys_hash'),
    )

    # Index for finding keys by user_id
    op.create_index('idx_api_keys_user_id', 'api_keys', ['user_id'])

    # Create mcp_logs table
    op.create_table(
        'mcp_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('api_key_id', sa.UUID(), nullable=True),  # nullable for SET NULL on delete
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),  # "list_projects", "search_knowledge", "send_message"
        sa.Column('project_id', sa.UUID(), nullable=True),  # null for list_projects
        sa.Column('request_data', JSONB, nullable=True),  # query, message, etc.
        sa.Column('response_summary', sa.String(500), nullable=True),  # brief result summary
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Indexes for mcp_logs
    op.create_index('idx_mcp_logs_user_id', 'mcp_logs', ['user_id'])
    op.create_index('idx_mcp_logs_api_key_id', 'mcp_logs', ['api_key_id'])


def downgrade() -> None:
    op.drop_index('idx_mcp_logs_api_key_id')
    op.drop_index('idx_mcp_logs_user_id')
    op.drop_table('mcp_logs')

    op.drop_index('idx_api_keys_user_id')
    op.drop_table('api_keys')

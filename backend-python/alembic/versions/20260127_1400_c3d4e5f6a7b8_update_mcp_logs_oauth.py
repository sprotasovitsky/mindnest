"""update_mcp_logs_oauth

Replace api_key_id with oauth_client_id in mcp_logs table.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-01-27 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop foreign key constraint and index for api_key_id
    op.drop_constraint('mcp_logs_api_key_id_fkey', 'mcp_logs', type_='foreignkey')
    op.drop_index('idx_mcp_logs_api_key_id', 'mcp_logs')

    # Drop api_key_id column
    op.drop_column('mcp_logs', 'api_key_id')

    # Add oauth_client_id column (no foreign key - clients are dynamic)
    op.add_column('mcp_logs', sa.Column('oauth_client_id', sa.String(255), nullable=True))

    # Add index for oauth_client_id
    op.create_index('idx_mcp_logs_oauth_client_id', 'mcp_logs', ['oauth_client_id'])


def downgrade() -> None:
    # Drop oauth_client_id index and column
    op.drop_index('idx_mcp_logs_oauth_client_id', 'mcp_logs')
    op.drop_column('mcp_logs', 'oauth_client_id')

    # Restore api_key_id column with foreign key
    op.add_column('mcp_logs', sa.Column('api_key_id', sa.UUID(), nullable=True))
    op.create_index('idx_mcp_logs_api_key_id', 'mcp_logs', ['api_key_id'])
    op.create_foreign_key(
        'mcp_logs_api_key_id_fkey',
        'mcp_logs',
        'api_keys',
        ['api_key_id'],
        ['id'],
        ondelete='SET NULL'
    )

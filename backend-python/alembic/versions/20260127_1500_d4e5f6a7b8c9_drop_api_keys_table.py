"""drop_api_keys_table

Drop the api_keys table after migration to OAuth2.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-01-27 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the api_keys table (no longer needed after OAuth2 migration)
    op.drop_index('idx_api_keys_user_id', 'api_keys')
    op.drop_constraint('uq_api_keys_hash', 'api_keys', type_='unique')
    op.drop_table('api_keys')


def downgrade() -> None:
    # Recreate api_keys table if needed for rollback
    op.create_table(
        'api_keys',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('key_prefix', sa.String(8), nullable=False),
        sa.Column('key_hash', sa.String(64), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('scopes', sa.String(50), nullable=False, server_default='read'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('key_hash', name='uq_api_keys_hash'),
    )
    op.create_index('idx_api_keys_user_id', 'api_keys', ['user_id'])

"""add_password_reset_codes

Revision ID: 847b1da43a0d
Revises: f23bcdd55fd3
Create Date: 2026-01-14 15:28:15.446712

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '847b1da43a0d'
down_revision: Union[str, None] = 'f23bcdd55fd3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create password_reset_codes table
    op.create_table(
        'password_reset_codes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('code_hash', sa.String(64), nullable=False),  # SHA-256 hash
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Index for finding codes by user_id (for cleanup and rate limiting)
    op.create_index('idx_password_reset_codes_user_id', 'password_reset_codes', ['user_id'])

    # Index for expired codes cleanup
    op.create_index('idx_password_reset_codes_expires_at', 'password_reset_codes', ['expires_at'])


def downgrade() -> None:
    op.drop_index('idx_password_reset_codes_expires_at')
    op.drop_index('idx_password_reset_codes_user_id')
    op.drop_table('password_reset_codes')

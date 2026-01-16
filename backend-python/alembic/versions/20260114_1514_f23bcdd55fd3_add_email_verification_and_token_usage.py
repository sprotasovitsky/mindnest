"""add_email_verification_and_token_usage

Revision ID: f23bcdd55fd3
Revises: 134980c2279b
Create Date: 2026-01-14 15:14:42.037528

Adds email verification fields and token usage tracking to users table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f23bcdd55fd3'
down_revision: Union[str, None] = '134980c2279b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email verification fields
    op.add_column('users', sa.Column('email_verified', sa.Boolean(),
                  nullable=False, server_default='false'))
    op.add_column('users', sa.Column('email_verification_token', sa.String(64),
                  nullable=True))
    op.add_column('users', sa.Column('email_verification_sent_at',
                  sa.DateTime(timezone=True), nullable=True))

    # Add token usage tracking (for unverified user limits)
    op.add_column('users', sa.Column('tokens_used', sa.BigInteger(),
                  nullable=False, server_default='0'))

    # Add index for verification token lookups
    op.create_index('idx_users_verification_token', 'users',
                    ['email_verification_token'], unique=True,
                    postgresql_where=sa.text('email_verification_token IS NOT NULL'))


def downgrade() -> None:
    op.drop_index('idx_users_verification_token', table_name='users')
    op.drop_column('users', 'tokens_used')
    op.drop_column('users', 'email_verification_sent_at')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'email_verified')

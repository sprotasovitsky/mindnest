"""add_social_auth_providers

Revision ID: 5ceea5ee0c9d
Revises: 847b1da43a0d
Create Date: 2026-01-14 15:34:09.495181

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ceea5ee0c9d'
down_revision: Union[str, None] = '847b1da43a0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make password_hash nullable for social-only users
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(255),
                    nullable=True)

    # Create social_auth_providers table
    op.create_table(
        'social_auth_providers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.String(20), nullable=False),  # 'google', 'apple'
        sa.Column('provider_user_id', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),  # May be relay email for Apple
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('provider', 'provider_user_id', name='uq_social_provider_user'),
    )

    # Index for finding providers by user_id
    op.create_index('idx_social_auth_providers_user_id', 'social_auth_providers', ['user_id'])


def downgrade() -> None:
    op.drop_index('idx_social_auth_providers_user_id')
    op.drop_table('social_auth_providers')

    # Make password_hash required again (note: this may fail if there are social-only users)
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(255),
                    nullable=False)

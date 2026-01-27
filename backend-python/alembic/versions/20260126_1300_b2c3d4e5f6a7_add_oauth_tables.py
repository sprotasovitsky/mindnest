"""add_oauth_tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-26 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create oauth_clients table
    op.create_table(
        'oauth_clients',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('client_secret_hash', sa.String(64), nullable=True),  # SHA-256, null for public clients
        sa.Column('client_name', sa.String(255), nullable=False),
        sa.Column('redirect_uris', ARRAY(sa.String()), nullable=False),
        sa.Column('grant_types', ARRAY(sa.String()), nullable=False),
        sa.Column('response_types', ARRAY(sa.String()), nullable=False),
        sa.Column('token_endpoint_auth_method', sa.String(50), nullable=False, server_default='none'),
        sa.Column('is_dynamic', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metadata_uri', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id', name='uq_oauth_clients_client_id'),
    )

    # Create oauth_authorization_codes table
    op.create_table(
        'oauth_authorization_codes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code_hash', sa.String(64), nullable=False),  # SHA-256
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('redirect_uri', sa.String(500), nullable=False),
        sa.Column('scope', sa.String(255), nullable=False, server_default='read'),
        sa.Column('code_challenge', sa.String(128), nullable=False),
        sa.Column('code_challenge_method', sa.String(10), nullable=False, server_default='S256'),
        sa.Column('state', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('code_hash', name='uq_oauth_codes_hash'),
    )
    op.create_index('idx_oauth_codes_client_id', 'oauth_authorization_codes', ['client_id'])
    op.create_index('idx_oauth_codes_user_id', 'oauth_authorization_codes', ['user_id'])

    # Create oauth_refresh_tokens table
    op.create_table(
        'oauth_refresh_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False),  # SHA-256
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('scope', sa.String(255), nullable=False, server_default='read'),
        sa.Column('family_id', sa.UUID(), nullable=False),  # For rotation detection
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('token_hash', name='uq_oauth_refresh_tokens_hash'),
    )
    op.create_index('idx_oauth_refresh_tokens_client_id', 'oauth_refresh_tokens', ['client_id'])
    op.create_index('idx_oauth_refresh_tokens_user_id', 'oauth_refresh_tokens', ['user_id'])
    op.create_index('idx_oauth_refresh_tokens_family_id', 'oauth_refresh_tokens', ['family_id'])

    # Create oauth_consents table
    op.create_table(
        'oauth_consents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('scope', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'client_id', name='uq_oauth_consent_user_client'),
    )
    op.create_index('idx_oauth_consents_user_id', 'oauth_consents', ['user_id'])


def downgrade() -> None:
    op.drop_index('idx_oauth_consents_user_id')
    op.drop_table('oauth_consents')

    op.drop_index('idx_oauth_refresh_tokens_family_id')
    op.drop_index('idx_oauth_refresh_tokens_user_id')
    op.drop_index('idx_oauth_refresh_tokens_client_id')
    op.drop_table('oauth_refresh_tokens')

    op.drop_index('idx_oauth_codes_user_id')
    op.drop_index('idx_oauth_codes_client_id')
    op.drop_table('oauth_authorization_codes')

    op.drop_table('oauth_clients')

"""Add chat_messages table

Revision ID: 9d9037c7825c
Revises: 001
Create Date: 2026-01-07 00:42:48.259987

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9d9037c7825c'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('chat_messages',
        sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('project_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('user_message', sa.Text(), nullable=False),
        sa.Column('assistant_reply', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chat_messages_project', 'chat_messages', ['project_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_chat_messages_project', table_name='chat_messages')
    op.drop_table('chat_messages')

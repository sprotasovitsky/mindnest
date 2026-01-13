"""clear_users_for_bcrypt_migration

Revision ID: 134980c2279b
Revises: 9d9037c7825c
Create Date: 2026-01-13 13:41:08.633059

This migration clears all users due to password hash format change
from SHA-256 to bcrypt. Related data (projects, members, chat messages)
will be cascade deleted via foreign key constraints.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '134980c2279b'
down_revision: Union[str, None] = '9d9037c7825c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Delete all users - cascade will handle related records
    # (project_members, chat_messages, projects)
    op.execute("DELETE FROM users")


def downgrade() -> None:
    # Cannot restore deleted users
    pass

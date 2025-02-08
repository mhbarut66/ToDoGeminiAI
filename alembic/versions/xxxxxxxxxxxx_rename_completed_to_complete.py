"""rename_completed_to_complete

Revision ID: xxxxxxxxxxxx
Revises: previous_revision_id
Create Date: YYYY-MM-DD HH:MM:SS

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'xxxxxxxxxxxx'  # Bu otomatik oluşturulacak
down_revision: Union[str, None] = 'previous_revision_id'  # Önceki revision ID'si
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # SQLite alternatif yaklaşım gerektirir
    with op.batch_alter_table('todos') as batch_op:
        batch_op.alter_column('completed',
                            new_column_name='complete',
                            existing_type=sa.Boolean())

def downgrade() -> None:
    # Geri alma işlemi için
    with op.batch_alter_table('todos') as batch_op:
        batch_op.alter_column('complete',
                            new_column_name='completed',
                            existing_type=sa.Boolean()) 
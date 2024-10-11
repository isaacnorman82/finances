"""added amex csv ingest type

Revision ID: bf03f8f87e3e
Revises: c92ab66621a5
Create Date: 2024-10-11 15:04:06.253130

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bf03f8f87e3e"
down_revision: Union[str, None] = "c92ab66621a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(f"ALTER TYPE ingesttype ADD VALUE 'amex_csv';")


def downgrade() -> None:
    # apparently there's no way to alter an enum to remove a value
    pass

"""add thumbnail link

Revision ID: 23eb8c93fd16
Revises: 96289458c4f9
Create Date: 2024-04-20 01:14:42.187826

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "23eb8c93fd16"
down_revision: str | None = "96289458c4f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("video", sa.Column("thumbnail", sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("video", "thumbnail")
    # ### end Alembic commands ###

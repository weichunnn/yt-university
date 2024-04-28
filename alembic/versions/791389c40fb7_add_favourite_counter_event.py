"""add favourite counter event

Revision ID: 791389c40fb7
Revises: 1af9f050b6bc
Create Date: 2024-04-28 16:54:00.612308

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "791389c40fb7"
down_revision: str | None = "1af9f050b6bc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "video",
        sa.Column("favorite_count", sa.Integer(), server_default="0", nullable=False),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("video", "favorite_count")
    # ### end Alembic commands ###

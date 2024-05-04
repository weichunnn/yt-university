"""add user fields

Revision ID: ed52319e3b33
Revises: d7a089944eb3
Create Date: 2024-05-04 23:47:18.367791

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ed52319e3b33"
down_revision: str | None = "d7a089944eb3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("user", sa.Column("username", sa.String(), nullable=True))
    op.add_column("user", sa.Column("first_name", sa.String(), nullable=True))
    op.add_column("user", sa.Column("last_name", sa.String(), nullable=True))
    op.add_column(
        "user", sa.Column("primary_email_address_id", sa.String(), nullable=True)
    )
    op.add_column("user", sa.Column("email_addresses", sa.JSON(), nullable=True))
    op.create_unique_constraint(None, "user", ["username"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "user", type_="unique")
    op.drop_column("user", "email_addresses")
    op.drop_column("user", "primary_email_address_id")
    op.drop_column("user", "last_name")
    op.drop_column("user", "first_name")
    op.drop_column("user", "username")
    # ### end Alembic commands ###

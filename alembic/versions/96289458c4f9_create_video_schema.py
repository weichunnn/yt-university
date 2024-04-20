"""create video schema

Revision ID: 96289458c4f9
Revises:
Create Date: 2024-04-19 00:33:13.931555

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "96289458c4f9"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "video",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("channel", sa.String(), nullable=True),
        sa.Column("channel_id", sa.String(), nullable=True),
        sa.Column("uploaded_at", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column(
            "transcription", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_video_id"), "video", ["id"], unique=False)
    op.create_index(op.f("ix_video_url"), "video", ["url"], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_video_url"), table_name="video")
    op.drop_index(op.f("ix_video_id"), table_name="video")
    op.drop_table("video")
    # ### end Alembic commands ###
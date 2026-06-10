"""Change borrow issue_date and return_date from TIMESTAMP to DATE

Revision ID: 003_borrow_dates_to_date
Revises: 002_add_user_id_to_borrow
Create Date: 2026-06-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '003_borrow_dates_to_date'
down_revision = '002_add_user_id_to_borrow'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'borrows', 'issue_date',
        type_=sa.Date(),
        existing_type=sa.DateTime(timezone=True),
        postgresql_using='issue_date::date',
        server_default=sa.text('CURRENT_DATE'),
        existing_nullable=False,
    )
    op.alter_column(
        'borrows', 'return_date',
        type_=sa.Date(),
        existing_type=sa.DateTime(),
        postgresql_using='return_date::date',
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        'borrows', 'return_date',
        type_=sa.DateTime(),
        existing_type=sa.Date(),
        existing_nullable=True,
    )
    op.alter_column(
        'borrows', 'issue_date',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.Date(),
        server_default=sa.text('now()'),
        existing_nullable=False,
    )

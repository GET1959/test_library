"""Remove unique constraint from books.title

Revision ID: 004_remove_book_title_unique
Revises: 003_borrow_dates_to_date
Create Date: 2026-06-09 00:00:00.000000

"""
from alembic import op


revision = '004_remove_book_title_unique'
down_revision = '003_borrow_dates_to_date'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('books_title_key', 'books', type_='unique')


def downgrade():
    op.create_unique_constraint('books_title_key', 'books', ['title'])

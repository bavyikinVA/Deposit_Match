"""add customer segments to base rates

Revision ID: 20260521_02
Revises: c59a25ec6482
Create Date: 2026-05-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260521_02"
down_revision: Union[str, Sequence[str], None] = "c59a25ec6482"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customer_segments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["bank_id"], ["banks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bank_id", "code", name="uq_customer_segment_bank_code"),
    )
    op.create_index(op.f("ix_customer_segments_bank_id"), "customer_segments", ["bank_id"])
    op.create_index(op.f("ix_customer_segments_code"), "customer_segments", ["code"])

    op.add_column(
        "deposit_base_rates",
        sa.Column("customer_segment_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_deposit_base_rates_customer_segment_id_customer_segments",
        "deposit_base_rates",
        "customer_segments",
        ["customer_segment_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_deposit_base_rates_customer_segment_id"),
        "deposit_base_rates",
        ["customer_segment_id"],
    )

    # Старый уникальный срез не учитывал сегмент клиента.
    op.drop_constraint("uq_base_rate_slice", "deposit_base_rates", type_="unique")
    op.create_unique_constraint(
        "uq_base_rate_slice",
        "deposit_base_rates",
        [
            "variant_id",
            "interest_scheme_id",
            "open_method_id",
            "customer_segment_id",
            "amount_from",
            "amount_to",
            "term_from_days",
            "term_to_days",
            "effective_from",
        ],
    )

    op.drop_index("ix_base_rates_lookup", table_name="deposit_base_rates")
    op.create_index(
        "ix_base_rates_lookup",
        "deposit_base_rates",
        [
            "variant_id",
            "interest_scheme_id",
            "open_method_id",
            "customer_segment_id",
            "amount_from",
            "amount_to",
            "term_from_days",
            "term_to_days",
            "effective_from",
            "effective_to",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_base_rates_lookup", table_name="deposit_base_rates")
    op.create_index(
        "ix_base_rates_lookup",
        "deposit_base_rates",
        [
            "variant_id",
            "interest_scheme_id",
            "open_method_id",
            "amount_from",
            "amount_to",
            "term_from_days",
            "term_to_days",
            "effective_from",
            "effective_to",
        ],
        unique=False,
    )

    op.drop_constraint("uq_base_rate_slice", "deposit_base_rates", type_="unique")
    op.create_unique_constraint(
        "uq_base_rate_slice",
        "deposit_base_rates",
        [
            "variant_id",
            "interest_scheme_id",
            "open_method_id",
            "amount_from",
            "amount_to",
            "term_from_days",
            "term_to_days",
            "effective_from",
        ],
    )

    op.drop_index(op.f("ix_deposit_base_rates_customer_segment_id"), table_name="deposit_base_rates")
    op.drop_constraint(
        "fk_deposit_base_rates_customer_segment_id_customer_segments",
        "deposit_base_rates",
        type_="foreignkey",
    )
    op.drop_column("deposit_base_rates", "customer_segment_id")

    op.drop_index(op.f("ix_customer_segments_code"), table_name="customer_segments")
    op.drop_index(op.f("ix_customer_segments_bank_id"), table_name="customer_segments")
    op.drop_table("customer_segments")

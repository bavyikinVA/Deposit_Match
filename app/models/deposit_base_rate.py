from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
if TYPE_CHECKING:
    from app.models.deposit_variant import DepositVariant
    from app.models.deposit_interest_scheme import DepositInterestScheme
    from app.models.open_method import DepositOpenMethod
    from app.models.customer_segment import CustomerSegment

class DepositBaseRate(Base):
    __tablename__ = "deposit_base_rates"
    __table_args__ = (
        CheckConstraint("amount_from >= 0", name="ck_base_rate_amount_from_non_negative"),
        CheckConstraint(
            "amount_to IS NULL OR amount_to >= amount_from",
            name="ck_base_rate_amount_to_gte_amount_from",
        ),
        CheckConstraint("term_from_days > 0", name="ck_base_rate_term_from_positive"),
        CheckConstraint(
            "term_to_days >= term_from_days",
            name="ck_base_rate_term_to_gte_term_from",
        ),
        CheckConstraint("nominal_rate >= 0", name="ck_nominal_rate_non_negative"),
        CheckConstraint(
            "effective_rate IS NULL OR effective_rate >= 0",
            name="ck_effective_rate_non_negative",
        ),
        UniqueConstraint(
            "variant_id",
            "interest_scheme_id",
            "open_method_id",
            "customer_segment_id",
            "amount_from",
            "amount_to",
            "term_from_days",
            "term_to_days",
            "effective_from",
            name="uq_base_rate_slice",
        ),
        Index(
            "ix_base_rates_lookup",
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
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    variant_id: Mapped[int] = mapped_column(
        ForeignKey("deposit_variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    interest_scheme_id: Mapped[int | None] = mapped_column(
        ForeignKey("deposit_interest_schemes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    open_method_id: Mapped[int | None] = mapped_column(
        ForeignKey("deposit_open_methods.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    customer_segment_id: Mapped[int | None] = mapped_column(
        ForeignKey("customer_segments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    amount_from: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    amount_to: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)

    term_from_days: Mapped[int] = mapped_column(nullable=False)
    term_to_days: Mapped[int] = mapped_column(nullable=False)

    nominal_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    effective_rate: Mapped[Decimal | None] = mapped_column(Numeric(7, 4), nullable=True)

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    variant: Mapped["DepositVariant"] = relationship(back_populates="base_rates")
    interest_scheme: Mapped["DepositInterestScheme | None"] = relationship(back_populates="base_rates")
    open_method: Mapped["DepositOpenMethod | None"] = relationship(back_populates="base_rates")
    customer_segment: Mapped["CustomerSegment | None"] = relationship(back_populates="base_rates")

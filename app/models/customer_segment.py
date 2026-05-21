from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.bank import Bank
    from app.models.deposit_base_rate import DepositBaseRate


class CustomerSegment(Base):
    """
    Универсальный клиентский сегмент банка.

    Примеры:
    - common: обычный клиент;
    - bank_client: действующий клиент банка;
    - alfa_only: Alfa Only;
    - a_club: А-Клуб;
    - t_pro: T-Pro;
    - pension_client: пенсионный клиент.

    Сегмент хранится отдельно от продукта и варианта вклада, потому что
    это параметр выбора ставки, а не отдельный банковский продукт.
    """

    __tablename__ = "customer_segments"
    __table_args__ = (
        UniqueConstraint("bank_id", "code", name="uq_customer_segment_bank_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    bank_id: Mapped[int] = mapped_column(
        ForeignKey("banks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Чем выше priority, тем «сильнее» сегмент при автоподборе/сортировке.
    # Например: common=0, alfa_only=50, a_club=100.
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    bank: Mapped["Bank"] = relationship(back_populates="customer_segments")
    base_rates: Mapped[list["DepositBaseRate"]] = relationship(
        back_populates="customer_segment"
    )

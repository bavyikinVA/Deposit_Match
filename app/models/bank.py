from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.deposit_product import DepositProduct
    from app.models.customer_segment import CustomerSegment


class Bank(Base):
    __tablename__ = "banks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    deposit_products: Mapped[list["DepositProduct"]] = relationship(
        back_populates="bank",
        cascade="all, delete-orphan",
    )

    customer_segments: Mapped[list["CustomerSegment"]] = relationship(
        back_populates="bank",
        cascade="all, delete-orphan",
    )
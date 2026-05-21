from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BankOut(ORMBase):
    id: int
    name: str
    slug: str


class DepositProductOut(ORMBase):
    id: int
    name: str
    currency: str


class OpenMethodOut(ORMBase):
    code: str
    name: str


class CustomerSegmentOut(ORMBase):
    id: int
    code: str
    name: str
    description: str | None = None
    priority: int = 0


class InterestSchemeOut(ORMBase):
    id: int
    code: str
    name: str
    payout_type: str
    payout_frequency: str | None = None
    capitalization_enabled: bool
    capitalization_frequency: str | None = None
    nominal_rate_only: bool
    effective_rate_supported: bool


class AppliedBonusOut(ORMBase):
    id: int
    name: str
    bonus_type: str
    bonus_value: Decimal
    is_percent_points: bool
    stackable: bool
    priority: int
    description: str | None = None


class RateMatchOut(ORMBase):
    base_rate_id: int
    interest_scheme_id: int | None = None
    interest_scheme_code: str | None = None
    open_method_id: int | None = None
    open_method_code: str | None = None
    customer_segment_id: int | None = None
    customer_segment_code: str | None = None
    customer_segment_name: str | None = None
    nominal_rate: Decimal
    effective_rate: Decimal | None = None
    effective_from: date
    effective_to: date | None = None


class DepositVariantOut(ORMBase):
    id: int
    code: str
    name: str
    description: str | None = None

    allow_topup: bool
    allow_partial_withdraw: bool
    auto_prolongation: bool

    min_amount: Decimal
    max_amount: Decimal | None = None
    min_term_days: int
    max_term_days: int | None = None

    bank: BankOut
    product: DepositProductOut

    open_methods: list[OpenMethodOut] = Field(default_factory=list)
    interest_schemes: list[InterestSchemeOut] = Field(default_factory=list)

    matched_rate: RateMatchOut | None = None
    matched_final_nominal_rate: Decimal | None = None
    matched_applied_bonuses: list[AppliedBonusOut] = Field(default_factory=list)


class CalculatorOptionOut(BaseModel):
    code: str
    name: str


class CalculatorTermOptionOut(BaseModel):
    days: int
    label: str


class CalculatorConditionOut(BaseModel):
    code: str
    name: str
    type: str = "checkbox"
    description: str | None = None


class CalculatorOptionsOut(BaseModel):
    terms: list[CalculatorTermOptionOut] = Field(default_factory=list)
    open_methods: list[CalculatorOptionOut] = Field(default_factory=list)
    interest_schemes: list[CalculatorOptionOut] = Field(default_factory=list)
    customer_segments: list[CalculatorOptionOut] = Field(default_factory=list)
    conditions: list[CalculatorConditionOut] = Field(default_factory=list)


class DepositsPage(ORMBase):
    items: list[DepositVariantOut]
    total: int
    page: int
    page_size: int

class DepositsStatsOut(ORMBase):
    total_offers: int
    total_banks: int
    topup_offers: int
    capitalization_offers: int

class DepositSearchParams(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    term_days: int | None = Field(default=None, gt=0)

    currency: str | None = Field(default=None, min_length=3, max_length=3)
    bank_ids: list[int] | None = None

    open_method_codes: list[str] | None = None
    interest_scheme_code: str | None = None
    customer_segment_code: str | None = None
    payout_type: str | None = None
    capitalization_enabled: bool | None = None

    allow_topup: bool | None = None
    allow_partial_withdraw: bool | None = None
    auto_prolongation: bool | None = None

    as_of: date = Field(default_factory=date.today)

    has_subscription: bool | None = None
    is_salary_client: bool | None = None
    is_pension_client: bool | None = None
    monthly_spend: Decimal | None = None
    savings_balance: Decimal | None = None
    has_premium_package: bool | None = None
    promo_code: str | None = None

    # Новая универсальная модель условий.
    # Примеры: {"is_new_money": true, "has_t_pro": true, "monthly_spend": 10000}
    conditions: dict[str, Any] = Field(default_factory=dict)

    # Старое поле оставляем временно для обратной совместимости.
    extra_context: dict[str, Any] = Field(default_factory=dict)

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else value

    @field_validator("open_method_codes")
    @classmethod
    def normalize_open_method_codes(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        return [item.strip() for item in value if item and item.strip()]


class DepositCalculationRequest(BaseModel):
    variant_id: int = Field(gt=0)

    amount: Decimal = Field(gt=0)
    term_days: int = Field(gt=0)

    open_method_code: str | None = None
    interest_scheme_code: str | None = None
    customer_segment_code: str | None = None
    as_of: date = Field(default_factory=date.today)

    has_subscription: bool | None = None
    is_salary_client: bool | None = None
    is_pension_client: bool | None = None
    monthly_spend: Decimal | None = None
    savings_balance: Decimal | None = None
    has_premium_package: bool | None = None
    promo_code: str | None = None
    conditions: dict[str, Any] = Field(default_factory=dict)

    extra_context: dict[str, Any] = Field(default_factory=dict)


class DepositCalculationResult(ORMBase):
    variant_id: int
    variant_name: str

    amount: Decimal
    term_days: int

    selected_open_method_code: str | None = None
    selected_interest_scheme_code: str | None = None
    selected_customer_segment_code: str | None = None
    selected_customer_segment_name: str | None = None

    base_nominal_rate: Decimal
    final_nominal_rate: Decimal
    effective_rate: Decimal | None = None

    total_bonus_rate: Decimal
    applied_bonuses: list[AppliedBonusOut] = Field(default_factory=list)

    total_interest: Decimal
    final_amount: Decimal

    payout_type: str
    capitalization_enabled: bool
    capitalization_frequency: str | None = None
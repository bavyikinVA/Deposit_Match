from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import DepositVariant, DepositProduct, DepositInterestScheme, CustomerSegment, Bank
from app.schemas.deposit import (
    DepositSearchParams,
    DepositsPage,
    DepositCalculationRequest,
    DepositCalculationResult,
    DepositsStatsOut,
    CalculatorOptionsOut,
    CalculatorOptionOut,
    CalculatorTermOptionOut,
    CalculatorConditionOut, BankOut,
)

from app.services.deposit_calculator import (
    CalculationContext,
    DepositCalculationError,
    calculate_variant_result,
)
from app.services.deposits import get_variant_or_404, search_deposit_variants

router = APIRouter(prefix="/api/deposits", tags=["deposits"])


@router.get("", response_model=DepositsPage)
async def list_deposits(
    amount: Decimal | None = Query(default=None, gt=0),
    term_days: int | None = Query(default=None, gt=0),
    currency: str | None = Query(default=None, min_length=3, max_length=3),
    bank_ids: list[int] | None = Query(default=None),
    open_method_codes: list[str] | None = Query(default=None),
    interest_scheme_code: str | None = Query(default=None),
    payout_type: str | None = Query(default=None),
    capitalization_enabled: bool | None = Query(default=None),
    allow_topup: bool | None = Query(default=None),
    allow_partial_withdraw: bool | None = Query(default=None),
    auto_prolongation: bool | None = Query(default=None),
    as_of: date = Query(default_factory=date.today),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    params = DepositSearchParams(
        amount=amount,
        term_days=term_days,
        currency=currency,
        bank_ids=bank_ids,
        open_method_codes=open_method_codes,
        interest_scheme_code=interest_scheme_code,
        payout_type=payout_type,
        capitalization_enabled=capitalization_enabled,
        allow_topup=allow_topup,
        allow_partial_withdraw=allow_partial_withdraw,
        auto_prolongation=auto_prolongation,
        as_of=as_of,
        page=page,
        page_size=page_size,
    )
    return await search_deposit_variants(session, params)


@router.post("/search", response_model=DepositsPage)
async def search_deposits(
    payload: DepositSearchParams,
    session: AsyncSession = Depends(get_session),
):
    return await search_deposit_variants(session, payload)


@router.post("/calculate", response_model=DepositCalculationResult)
async def calculate_deposit(
    payload: DepositCalculationRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        variant = await get_variant_or_404(session, payload.variant_id)

        ctx = CalculationContext(
            amount=payload.amount,
            term_days=payload.term_days,
            as_of=payload.as_of,
            open_method_code=payload.open_method_code,
            interest_scheme_code=payload.interest_scheme_code,
            customer_segment_code=payload.customer_segment_code,
            conditions=payload.conditions,
            has_subscription=payload.has_subscription,
            is_salary_client=payload.is_salary_client,
            is_pension_client=payload.is_pension_client,
            monthly_spend=payload.monthly_spend,
            savings_balance=payload.savings_balance,
            has_premium_package=payload.has_premium_package,
            promo_code=payload.promo_code,
            extra_context=payload.extra_context,
        )

        return calculate_variant_result(variant, ctx)

    except DepositCalculationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


async def get_deposits_stats(session: AsyncSession) -> DepositsStatsOut:
    total_offers_query = (
        select(func.count(DepositVariant.id))
        .where(DepositVariant.is_active.is_(True))
    )

    total_banks_query = (
        select(func.count(distinct(DepositProduct.bank_id)))
        .select_from(DepositVariant)
        .join(DepositProduct, DepositProduct.id == DepositVariant.product_id)
        .where(
            DepositVariant.is_active.is_(True),
            DepositProduct.is_active.is_(True),
        )
    )

    topup_offers_query = (
        select(func.count(DepositVariant.id))
        .where(
            DepositVariant.is_active.is_(True),
            DepositVariant.allow_topup.is_(True),
        )
    )

    capitalization_offers_query = (
        select(func.count(distinct(DepositInterestScheme.variant_id)))
        .where(
            DepositInterestScheme.is_active.is_(True),
            DepositInterestScheme.capitalization_enabled.is_(True),
        )
    )

    total_offers = (await session.execute(total_offers_query)).scalar_one()
    total_banks = (await session.execute(total_banks_query)).scalar_one()
    topup_offers = (await session.execute(topup_offers_query)).scalar_one()
    capitalization_offers = (await session.execute(capitalization_offers_query)).scalar_one()

    return DepositsStatsOut(
        total_offers=total_offers,
        total_banks=total_banks,
        topup_offers=topup_offers,
        capitalization_offers=capitalization_offers,
    )


@router.get("/stats", response_model=DepositsStatsOut)
async def deposits_stats(
    session: AsyncSession = Depends(get_session),
):
    return await get_deposits_stats(session)

def _format_days_label(days: int) -> str:
    known = {
        30: "1 месяц",
        31: "1 месяц",
        60: "2 месяца",
        61: "2 месяца",
        62: "2 месяца",
        90: "3 месяца",
        91: "3 месяца",
        92: "93 месяца",
        120: "4 месяца",
        123: "4 месяца",
        180: "6 месяцев",
        181: "6 месяцев",
        184: "6 месяцев",
        276: "9 месяцев",
        365: "1 год",
        367: "1 год",
        548: "1,5 года",
        730: "2 года",
        731: "2 года",
        1095: "3 года",
    }
    return known.get(days, f"{days} дн.")


def _condition_name(field_name: str) -> str:
    mapping = {
        "is_new_money": "Новые деньги",
        "has_subscription": "Есть подписка",
        "is_salary_client": "Зарплатный клиент",
        "is_pension_client": "Пенсионный клиент",
        "has_premium_package": "Премиум-пакет",
        "has_t_pro": "T-Pro",
        "monthly_spend": "Оборот по карте",
        "savings_balance": "Остаток на счёте",
        "promo_code": "Промокод",
    }
    return mapping.get(field_name, field_name)


@router.get("/{variant_id}/calculator-options", response_model=CalculatorOptionsOut)
async def get_calculator_options(
    variant_id: int,
    session: AsyncSession = Depends(get_session),
):
    variant = await get_variant_or_404(session, variant_id)

    terms_seen: set[tuple[int, int]] = set()
    terms: list[CalculatorTermOptionOut] = []
    for rate in sorted(variant.base_rates, key=lambda r: (r.term_from_days, r.term_to_days)):
        key = (rate.term_from_days, rate.term_to_days)
        if key in terms_seen:
            continue
        terms_seen.add(key)
        label = (
            f"{_format_days_label(rate.term_from_days)} ({rate.term_from_days} дн.)"
            if rate.term_from_days == rate.term_to_days
            else f"{_format_days_label(rate.term_from_days)} — {_format_days_label(rate.term_to_days)} "
                 f"({rate.term_from_days}–{rate.term_to_days} дн.)"
        )
        terms.append(CalculatorTermOptionOut(days=rate.term_from_days, label=label))

    open_methods = [
        CalculatorOptionOut(code=item.open_method.code, name=item.open_method.name)
        for item in variant.open_methods
        if getattr(item, "open_method", None) and item.open_method.is_active
    ]

    interest_schemes = [
        CalculatorOptionOut(code=scheme.code, name=scheme.name)
        for scheme in variant.interest_schemes
        if scheme.is_active
    ]

    bank_segments = getattr(variant.product.bank, "customer_segments", [])
    segment_codes_in_rates = {
        rate.customer_segment.code
        for rate in variant.base_rates
        if getattr(rate, "customer_segment", None) is not None
    }
    customer_segments = [
        CalculatorOptionOut(code="", name="Обычный клиент")
    ]
    customer_segments.extend(
        CalculatorOptionOut(code=segment.code, name=segment.name)
        for segment in sorted(bank_segments, key=lambda s: (s.priority, s.name))
        if segment.is_active and segment.code in segment_codes_in_rates and segment.code != "common"
    )

    condition_fields = {
        condition.field_name
        for bonus in variant.bonuses
        for condition in bonus.conditions
    }
    conditions = [
        CalculatorConditionOut(code=field_name, name=_condition_name(field_name))
        for field_name in sorted(condition_fields)
        if field_name not in {"amount", "term_days", "open_method_code", "interest_scheme_code", "customer_segment_code"}
    ]

    return CalculatorOptionsOut(
        terms=terms,
        open_methods=open_methods,
        interest_schemes=interest_schemes,
        customer_segments=customer_segments,
        conditions=conditions,
    )

@router.get("/banks")
async def deposits_banks(
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(Bank)
        .where(Bank.is_active.is_(True))
        .order_by(Bank.name)
    )

    result = await session.scalars(stmt)
    banks = result.all()

    return [
        {
            "id": bank.id,
            "name": bank.name,
            "slug": bank.slug,
        }
        for bank in banks
    ]

@router.get("/{variant_id}")
async def get_deposit_variant(
    variant_id: int,
    session: AsyncSession = Depends(get_session),
):
    variant = await get_variant_or_404(session, variant_id)

    return {
        "id": variant.id,
        "product_id": variant.product_id,
        "name": variant.name,
        "code": variant.code,
        "description": variant.description,
        "allow_topup": variant.allow_topup,
        "allow_partial_withdraw": variant.allow_partial_withdraw,
        "auto_prolongation": variant.auto_prolongation,
        "min_amount": float(variant.min_amount) if variant.min_amount is not None else None,
        "max_amount": float(variant.max_amount) if variant.max_amount is not None else None,
        "min_term_days": variant.min_term_days,
        "max_term_days": variant.max_term_days,
        "is_active": variant.is_active,

        "product": {
            "id": variant.product.id if variant.product else None,
            "name": getattr(variant.product, "name", None),
            "currency": getattr(variant.product, "currency", None),
            "bank": {
                "id": variant.product.bank.id if variant.product and getattr(variant.product, "bank", None) else None,
                "name": variant.product.bank.name if variant.product and getattr(variant.product, "bank", None) else None,
            } if variant.product and getattr(variant.product, "bank", None) else None,
        } if variant.product else None,

        "open_methods": [
            {
                "id": item.open_method.id if getattr(item, "open_method", None) else None,
                "code": item.open_method.code if getattr(item, "open_method", None) else None,
                "name": item.open_method.name if getattr(item, "open_method", None) else None,
            }
            for item in (variant.open_methods or [])
            if getattr(item, "open_method", None)
        ],

        "interest_schemes": [
            {
                "id": scheme.id,
                "code": scheme.code,
                "name": scheme.name,
                "description": scheme.description,
                "payout_type": scheme.payout_type,
                "payout_frequency": scheme.payout_frequency,
                "capitalization_enabled": scheme.capitalization_enabled,
                "capitalization_frequency": scheme.capitalization_frequency,
                "interest_to_separate_account": scheme.interest_to_separate_account,
                "interest_to_deposit_body": scheme.interest_to_deposit_body,
                "nominal_rate_only": scheme.nominal_rate_only,
                "effective_rate_supported": scheme.effective_rate_supported,
                "is_active": scheme.is_active,
            }
            for scheme in (variant.interest_schemes or [])
        ],

        "base_rates": [
            {
                "id": rate.id,
                "variant_id": rate.variant_id,
                "interest_scheme_id": rate.interest_scheme_id,
                "open_method_id": rate.open_method_id,
                "customer_segment_id": rate.customer_segment_id,
                "customer_segment": {
                    "id": rate.customer_segment.id,
                    "code": rate.customer_segment.code,
                    "name": rate.customer_segment.name,
                } if getattr(rate, "customer_segment", None) else None,
                "amount_from": float(rate.amount_from) if rate.amount_from is not None else None,
                "amount_to": float(rate.amount_to) if rate.amount_to is not None else None,
                "term_from_days": rate.term_from_days,
                "term_to_days": rate.term_to_days,
                "nominal_rate": float(rate.nominal_rate) if rate.nominal_rate is not None else None,
                "effective_rate": float(rate.effective_rate) if rate.effective_rate is not None else None,
                "effective_from": rate.effective_from.isoformat() if rate.effective_from else None,
                "effective_to": rate.effective_to.isoformat() if rate.effective_to else None,
                "open_method": {
                    "id": rate.open_method.id,
                    "code": rate.open_method.code,
                    "name": rate.open_method.name,
                } if getattr(rate, "open_method", None) else None,
                "interest_scheme": {
                    "id": rate.interest_scheme.id,
                    "code": rate.interest_scheme.code,
                    "name": rate.interest_scheme.name,
                } if getattr(rate, "interest_scheme", None) else None,
            }
            for rate in (variant.base_rates or [])
        ],
    }
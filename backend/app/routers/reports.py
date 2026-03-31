from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.ad import AdData
from app.models.product import Product
from app.models.sales import SalesSummary
from app.schemas.report import PlatformProfit, ProfitByProduct, UnmatchedSummary
from app.services.profit_calculator import ProfitCalculator

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/profit", response_model=ProfitByProduct)
async def profit_by_product(
    product_id: int = Query(...),
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    calc = ProfitCalculator(db)
    results = await calc.calculate(product_id, period_start, period_end)

    product = (
        await db.execute(select(Product).where(Product.id == product_id))
    ).scalar_one()

    platforms = [
        PlatformProfit(
            platform_name=r.platform_name,
            platform_id=r.platform_id,
            revenue=r.revenue,
            cost_of_goods=r.cost_of_goods,
            platform_fee=r.platform_fee,
            coupon_cost=r.coupon_cost,
            refund_shipping_cost=r.refund_shipping_cost,
            ad_cost=r.ad_cost,
            marketing_cost=r.marketing_cost,
            variable_cost=r.variable_cost,
            net_profit=r.net_profit,
            profit_rate=r.profit_rate,
        )
        for r in results
    ]

    total_revenue = sum(p.revenue for p in platforms)
    total_net = sum(p.net_profit for p in platforms)
    total_rate = (
        (total_net / total_revenue * 100) if total_revenue else Decimal("0")
    )

    return ProfitByProduct(
        product_id=product.id,
        product_name=product.name,
        sku=product.sku,
        platforms=platforms,
        total_revenue=total_revenue,
        total_net_profit=total_net,
        total_profit_rate=round(total_rate, 1),
    )


@router.get("/profit/all", response_model=list[ProfitByProduct])
async def profit_all_products(
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    products = (await db.execute(select(Product))).scalars().all()
    calc = ProfitCalculator(db)
    output = []
    for product in products:
        results = await calc.calculate(product.id, period_start, period_end)
        if not results:
            continue
        platforms = [
            PlatformProfit(
                platform_name=r.platform_name,
                platform_id=r.platform_id,
                revenue=r.revenue,
                cost_of_goods=r.cost_of_goods,
                platform_fee=r.platform_fee,
                coupon_cost=r.coupon_cost,
                refund_shipping_cost=r.refund_shipping_cost,
                ad_cost=r.ad_cost,
                marketing_cost=r.marketing_cost,
                variable_cost=r.variable_cost,
                net_profit=r.net_profit,
                profit_rate=r.profit_rate,
            )
            for r in results
        ]
        total_revenue = sum(p.revenue for p in platforms)
        total_net = sum(p.net_profit for p in platforms)
        total_rate = (
            (total_net / total_revenue * 100)
            if total_revenue
            else Decimal("0")
        )
        output.append(
            ProfitByProduct(
                product_id=product.id,
                product_name=product.name,
                sku=product.sku,
                platforms=platforms,
                total_revenue=total_revenue,
                total_net_profit=total_net,
                total_profit_rate=round(total_rate, 1),
            )
        )
    return output


@router.get("/unmatched-summary", response_model=UnmatchedSummary)
async def unmatched_summary(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    # Unmatched sales: SalesSummary rows with no platform_product match
    # (platform_product_id is required, so we count rows where the
    # platform_product has no product_id — but in our schema platform_product
    # always has product_id. Instead count sales with platform_product_id
    # pointing to unmatched products is N/A. We'll count ad_data with
    # platform_product_id IS NULL as unmatched.)
    unmatched_ads_result = await db.execute(
        select(func.count(AdData.id)).where(
            AdData.platform_product_id.is_(None)
        )
    )
    unmatched_ads = unmatched_ads_result.scalar() or 0

    unmatched_ad_spend_result = await db.execute(
        select(func.coalesce(func.sum(AdData.spend), 0)).where(
            AdData.platform_product_id.is_(None)
        )
    )
    unmatched_ad_spend = unmatched_ad_spend_result.scalar() or Decimal("0")

    # For unmatched sales, count 0 since all sales require platform_product_id
    return UnmatchedSummary(
        unmatched_sales=0,
        unmatched_ads=unmatched_ads,
        unmatched_ad_spend=unmatched_ad_spend,
    )

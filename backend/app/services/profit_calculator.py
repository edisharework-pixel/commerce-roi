from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import AdData
from app.models.cost import MarketingCost, VariableCost
from app.models.platform import Platform
from app.models.product import PlatformProduct, Product
from app.models.sales import Order, SalesSummary


@dataclass
class ProfitResult:
    platform_name: str
    platform_id: int
    revenue: Decimal
    cost_of_goods: Decimal
    platform_fee: Decimal
    coupon_cost: Decimal
    refund_shipping_cost: Decimal
    ad_cost: Decimal
    marketing_cost: Decimal
    variable_cost: Decimal
    net_profit: Decimal
    profit_rate: Decimal


class ProfitCalculator:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def calculate(
        self, product_id: int, period_start: date, period_end: date
    ) -> list[ProfitResult]:
        product = (
            await self.session.execute(
                select(Product).where(Product.id == product_id)
            )
        ).scalar_one()

        platform_products = (
            await self.session.execute(
                select(PlatformProduct).where(
                    PlatformProduct.product_id == product_id
                )
            )
        ).scalars().all()

        results = []
        for pp in platform_products:
            platform = (
                await self.session.execute(
                    select(Platform).where(Platform.id == pp.platform_id)
                )
            ).scalar_one()
            result = await self._calc_for_platform(
                product, pp, platform, period_start, period_end
            )
            if result:
                results.append(result)
        return results

    async def _calc_for_platform(
        self, product, pp, platform, period_start, period_end
    ):
        # Get sales (sales_summary)
        sales = (
            await self.session.execute(
                select(SalesSummary).where(
                    SalesSummary.platform_product_id == pp.id,
                    SalesSummary.period_start >= period_start,
                    SalesSummary.period_end <= period_end,
                )
            )
        ).scalars().all()

        # Get orders (gmarket/auction)
        orders = (
            await self.session.execute(
                select(Order).where(
                    Order.platform_product_id == pp.id,
                    Order.order_date >= period_start,
                    Order.order_date <= period_end,
                )
            )
        ).scalars().all()

        if not sales and not orders:
            return None

        fee_rate = (
            Decimal(str(pp.platform_fee_rate or platform.fee_rate or 0)) / 100
        )

        # Get ad cost for this platform_product
        ad_cost_result = await self.session.execute(
            select(AdData).where(
                AdData.platform_product_id == pp.id,
                AdData.ad_date >= period_start,
                AdData.ad_date <= period_end,
            )
        )
        ad_cost = sum(a.spend for a in ad_cost_result.scalars().all())

        # Get variable costs
        vc_result = await self.session.execute(
            select(VariableCost).where(
                VariableCost.product_id == product.id,
                VariableCost.period_start <= period_end,
                VariableCost.period_end >= period_start,
            )
        )
        var_cost = sum(v.amount for v in vc_result.scalars().all())

        # Get marketing costs
        mc_result = await self.session.execute(
            select(MarketingCost).where(
                MarketingCost.product_id == product.id,
                MarketingCost.cost_date >= period_start,
                MarketingCost.cost_date <= period_end,
            )
        )
        mkt_cost = sum(m.amount for m in mc_result.scalars().all())

        if platform.name.startswith("네이버"):
            return self._calc_naver(
                platform, pp, product, sales, fee_rate, ad_cost, mkt_cost, var_cost
            )
        elif platform.name.startswith("쿠팡"):
            return self._calc_coupang(
                platform, pp, product, sales, fee_rate, ad_cost, mkt_cost, var_cost
            )
        elif platform.name.startswith("지마켓") or platform.name.startswith("옥션"):
            return self._calc_gmarket(
                platform, pp, product, orders, fee_rate, ad_cost, mkt_cost, var_cost
            )
        return None

    def _calc_naver(
        self, platform, pp, product, sales, fee_rate, ad_cost, mkt_cost, var_cost
    ):
        revenue = sum(s.net_revenue or 0 for s in sales)
        quantity = sum(s.quantity or 0 for s in sales)
        refund_count = sum(s.refund_count or 0 for s in sales)
        coupon = sum(
            (s.coupon_seller or 0) + (s.coupon_order or 0) for s in sales
        )
        return_fee = Decimal(str(pp.return_shipping_fee or 0)) * refund_count
        cogs = product.base_cost * (quantity - refund_count)
        platform_fee = revenue * fee_rate
        net = (
            revenue
            - cogs
            - platform_fee
            - coupon
            - return_fee
            - ad_cost
            - mkt_cost
            - var_cost
        )
        rate = (net / revenue * 100) if revenue else Decimal("0")
        return ProfitResult(
            platform_name=platform.name,
            platform_id=platform.id,
            revenue=revenue,
            cost_of_goods=cogs,
            platform_fee=platform_fee,
            coupon_cost=coupon,
            refund_shipping_cost=return_fee,
            ad_cost=ad_cost,
            marketing_cost=mkt_cost,
            variable_cost=var_cost,
            net_profit=net,
            profit_rate=round(rate, 1),
        )

    def _calc_coupang(
        self, platform, pp, product, sales, fee_rate, ad_cost, mkt_cost, var_cost
    ):
        revenue = sum(s.net_revenue or 0 for s in sales)
        quantity = sum(s.quantity or 0 for s in sales)
        cogs = product.base_cost * quantity
        platform_fee = revenue * fee_rate
        net = revenue - cogs - platform_fee - ad_cost - mkt_cost - var_cost
        rate = (net / revenue * 100) if revenue else Decimal("0")
        return ProfitResult(
            platform_name=platform.name,
            platform_id=platform.id,
            revenue=revenue,
            cost_of_goods=cogs,
            platform_fee=platform_fee,
            coupon_cost=Decimal("0"),
            refund_shipping_cost=Decimal("0"),
            ad_cost=ad_cost,
            marketing_cost=mkt_cost,
            variable_cost=var_cost,
            net_profit=net,
            profit_rate=round(rate, 1),
        )

    def _calc_gmarket(
        self, platform, pp, product, orders, fee_rate, ad_cost, mkt_cost, var_cost
    ):
        normal_statuses = {"송금완료", "배송완료"}
        normal = [o for o in orders if o.status in normal_statuses]
        cancel = [o for o in orders if o.status not in normal_statuses]
        revenue = sum(o.sale_price * o.quantity for o in normal)
        cancel_amount = sum(o.sale_price * o.quantity for o in cancel)
        normal_qty = sum(o.quantity for o in normal)
        cogs = product.base_cost * normal_qty
        platform_fee = revenue * fee_rate
        net = (
            revenue
            - cancel_amount
            - cogs
            - platform_fee
            - ad_cost
            - mkt_cost
            - var_cost
        )
        rate = (net / revenue * 100) if revenue else Decimal("0")
        return ProfitResult(
            platform_name=platform.name,
            platform_id=platform.id,
            revenue=revenue,
            cost_of_goods=cogs,
            platform_fee=platform_fee,
            coupon_cost=Decimal("0"),
            refund_shipping_cost=Decimal("0"),
            ad_cost=ad_cost,
            marketing_cost=mkt_cost,
            variable_cost=var_cost,
            net_profit=net,
            profit_rate=round(rate, 1),
        )

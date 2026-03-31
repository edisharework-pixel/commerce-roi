from decimal import Decimal

from pydantic import BaseModel


class PlatformProfit(BaseModel):
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


class ProfitByProduct(BaseModel):
    product_id: int
    product_name: str
    sku: str
    platforms: list[PlatformProfit]
    total_revenue: Decimal
    total_net_profit: Decimal
    total_profit_rate: Decimal


class UnmatchedSummary(BaseModel):
    unmatched_sales: int
    unmatched_ads: int
    unmatched_ad_spend: Decimal

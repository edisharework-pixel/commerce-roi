from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import BinaryIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.matching.product_matcher import ProductMatcher
from app.models.ad import AdData
from app.models.platform import Platform
from app.models.sales import Order, SalesSummary
from app.models.upload import MatchingLog, UploadHistory
from app.parsers.adapters.base import BaseAdapter
from app.parsers.adapters.coupang_ad import CoupangAdAdapter
from app.parsers.adapters.coupang_sales import CoupangSalesAdapter
from app.parsers.adapters.gmarket_ad import GmarketAdAdapter
from app.parsers.adapters.gmarket_order import GmarketOrderAdapter
from app.parsers.adapters.naver_ad import NaverAdAdapter
from app.parsers.adapters.naver_sales import NaverSalesAdapter
from app.parsers.pipeline import run_parse_pipeline

ADAPTER_MAP: dict[tuple[str, str], type[BaseAdapter]] = {
    ("네이버", "sales_summary"): NaverSalesAdapter,
    ("네이버", "ad"): NaverAdAdapter,
    ("쿠팡", "sales_summary"): CoupangSalesAdapter,
    ("쿠팡", "ad"): CoupangAdAdapter,
    ("지마켓", "order"): GmarketOrderAdapter,
    ("옥션", "order"): GmarketOrderAdapter,
    ("지마켓", "ad"): GmarketAdAdapter,
    ("옥션", "ad"): GmarketAdAdapter,
}


@dataclass
class UploadResult:
    record_count: int
    matched_count: int
    unmatched_count: int
    upload_id: int


def _get_adapter(platform_name: str, data_type: str) -> BaseAdapter:
    for (prefix, dtype), adapter_cls in ADAPTER_MAP.items():
        if platform_name.startswith(prefix) and dtype == data_type:
            return adapter_cls()
    raise ValueError(
        f"No adapter for platform={platform_name}, data_type={data_type}"
    )


def _safe_decimal(val, default="0") -> Decimal:
    try:
        v = val if val is not None and str(val) != "nan" else default
        return Decimal(str(v))
    except Exception:
        return Decimal(default)


def _safe_int(val, default=0) -> int:
    try:
        v = val if val is not None and str(val) != "nan" else default
        return int(float(str(v)))
    except Exception:
        return default


class UploadService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.matcher = ProductMatcher(session)

    async def process_upload(
        self,
        file: BinaryIO,
        file_type: str,
        platform_id: int,
        data_type: str,
        period_start: date,
        period_end: date,
        file_name: str,
        password: str | None = None,
    ) -> UploadResult:
        platform = (
            await self.session.execute(
                select(Platform).where(Platform.id == platform_id)
            )
        ).scalar_one()
        adapter = _get_adapter(platform.name, data_type)
        parse_result = run_parse_pipeline(
            file=file, file_type=file_type, adapter=adapter, password=password
        )

        # Create upload history first to get ID
        upload = UploadHistory(
            platform_id=platform_id,
            data_type=data_type,
            file_name=file_name,
            record_count=parse_result.row_count,
            matched_count=0,
            unmatched_count=0,
            period_start=period_start,
            period_end=period_end,
        )
        self.session.add(upload)
        await self.session.flush()  # get upload.id

        matched, unmatched = 0, 0
        for _, row in parse_result.data.iterrows():
            pid = str(row.get("product_id", ""))
            pname = str(row.get("product_name", ""))
            match_result = await self.matcher.match(
                platform_id=platform_id,
                platform_product_id=pid,
                product_name=pname,
                seller_product_code=row.get("seller_product_code"),
            )
            if match_result.matched:
                matched += 1
            else:
                unmatched += 1

            self.session.add(
                MatchingLog(
                    platform_product_name=pname,
                    matched_product_id=match_result.product_id,
                    method=match_result.method,
                    confidence=match_result.confidence,
                )
            )

            if match_result.matched:
                pp_id = match_result.platform_product_id
                if data_type == "sales_summary":
                    self.session.add(
                        SalesSummary(
                            platform_product_id=pp_id,
                            period_start=period_start,
                            period_end=period_end,
                            gross_revenue=_safe_decimal(
                                row.get(
                                    "gross_revenue",
                                    row.get("net_revenue"),
                                )
                            ),
                            net_revenue=_safe_decimal(row.get("net_revenue")),
                            quantity=_safe_int(row.get("quantity")),
                            cancel_amount=_safe_decimal(
                                row.get("cancel_amount")
                            )
                            or None,
                            cancel_quantity=_safe_int(
                                row.get("cancel_quantity")
                            )
                            or None,
                            refund_amount=_safe_decimal(
                                row.get("refund_amount")
                            )
                            or None,
                            refund_count=_safe_int(row.get("refund_count"))
                            or None,
                            coupon_seller=_safe_decimal(
                                row.get("coupon_seller")
                            )
                            or None,
                            coupon_order=_safe_decimal(row.get("coupon_order"))
                            or None,
                            visitors=_safe_int(row.get("visitors")) or None,
                            page_views=_safe_int(row.get("page_views"))
                            or None,
                            cart_count=_safe_int(row.get("cart_count"))
                            or None,
                            upload_id=upload.id,
                        )
                    )
                elif data_type == "order":
                    self.session.add(
                        Order(
                            platform_product_id=pp_id,
                            order_date=row["order_date"],
                            order_number=str(row["order_number"]),
                            quantity=_safe_int(row.get("quantity")),
                            sale_price=_safe_decimal(row.get("sale_price")),
                            status=str(row.get("status", "")),
                            site=row.get("site"),
                            upload_id=upload.id,
                        )
                    )
                elif data_type == "ad":
                    self.session.add(
                        AdData(
                            platform_id=platform_id,
                            platform_product_id=pp_id,
                            option_id=str(row.get("option_id", "")) or None,
                            campaign_name=str(row.get("campaign_name", "")),
                            ad_group=row.get("ad_group"),
                            keyword=row.get("keyword"),
                            ad_type=row.get("ad_type"),
                            exposure_area=row.get("exposure_area"),
                            spend=_safe_decimal(row.get("spend")),
                            impressions=_safe_int(row.get("impressions")),
                            clicks=_safe_int(row.get("clicks")),
                            direct_conversions=_safe_int(
                                row.get("direct_conversions")
                            )
                            or None,
                            indirect_conversions=_safe_int(
                                row.get("indirect_conversions")
                            )
                            or None,
                            direct_revenue=_safe_decimal(
                                row.get("direct_revenue")
                            )
                            or None,
                            indirect_revenue=_safe_decimal(
                                row.get("indirect_revenue")
                            )
                            or None,
                            attribution_window=row.get("attribution_window"),
                            avg_rank=_safe_decimal(row.get("avg_rank"))
                            or None,
                            site=row.get("site"),
                            ad_date=row.get("ad_date", date.today()),
                            match_status="matched",
                        )
                    )

        upload.matched_count = matched
        upload.unmatched_count = unmatched
        await self.session.commit()

        return UploadResult(
            record_count=parse_result.row_count,
            matched_count=matched,
            unmatched_count=unmatched,
            upload_id=upload.id,
        )

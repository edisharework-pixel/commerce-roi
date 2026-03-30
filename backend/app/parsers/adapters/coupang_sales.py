import pandas as pd
from app.parsers.adapters.base import BaseAdapter
from app.parsers.column_mapper import apply_column_mapping


class CoupangSalesAdapter(BaseAdapter):
    platform_name = "쿠팡"
    data_type = "sales_summary"

    def get_column_mapping(self):
        return {
            "option_id": "옵션 ID", "product_id": "등록상품 ID",
            "product_name": "노출상품명", "option_name": "옵션명: 옵션값",
            "net_revenue": "매출(원)", "gross_revenue": "총 매출(원)",
            "cancel_amount": "총 취소 금액(원)", "cancel_quantity": "총 취소된 상품수",
            "quantity": "판매량", "visitors": "방문자",
            "page_views": "조회", "cart_count": "장바구니",
        }

    def get_parsing_rules(self):
        return {"skip_rows": 0, "period_from_upload": True}

    def transform(self, df):
        df = apply_column_mapping(df, self.get_column_mapping())
        df["option_id"] = df["option_id"].astype(str)
        df["product_id"] = df["product_id"].astype(str)
        for col in ["net_revenue", "gross_revenue", "cancel_amount", "cancel_quantity", "quantity", "visitors", "page_views", "cart_count"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df

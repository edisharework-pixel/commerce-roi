import pandas as pd
from app.parsers.adapters.base import BaseAdapter
from app.parsers.column_mapper import apply_column_mapping


class NaverSalesAdapter(BaseAdapter):
    platform_name = "네이버 스마트스토어"
    data_type = "sales_summary"

    def get_column_mapping(self):
        return {
            "product_id": "상품번호", "product_name": "상품명",
            "quantity": "결제상품수량", "net_revenue": "결제금액",
            "refund_amount": "환불금액", "refund_count": "환불수량",
            "coupon_seller": "상품쿠폰합계", "coupon_order": "주문쿠폰합계",
        }

    def get_parsing_rules(self):
        return {"skip_rows": 0, "period_from_filename": True}

    def transform(self, df):
        df = apply_column_mapping(df, self.get_column_mapping())
        df["product_id"] = df["product_id"].astype(str)
        for col in ["quantity", "net_revenue", "refund_amount", "refund_count", "coupon_seller", "coupon_order"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df

import pandas as pd
from app.parsers.adapters.base import BaseAdapter
from app.parsers.column_mapper import apply_column_mapping, parse_date_column

SITE_MAP = {"지마켓(itholic)": "G", "옥션(itemholic)": "A"}


class GmarketOrderAdapter(BaseAdapter):
    platform_name = "지마켓"
    data_type = "order"

    def get_column_mapping(self):
        return {
            "order_date": "결제일", "order_number": "주문번호",
            "product_id": "상품번호", "product_name": "상품명",
            "quantity": "수량", "sale_price": "구매금액", "status": "진행상태",
        }

    def transform(self, df):
        if "판매아이디" in df.columns:
            df["site"] = df["판매아이디"].map(SITE_MAP)
        df = apply_column_mapping(df, self.get_column_mapping())
        df = parse_date_column(df, "order_date")
        df["product_id"] = df["product_id"].astype(str)
        for col in ["quantity", "sale_price"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df

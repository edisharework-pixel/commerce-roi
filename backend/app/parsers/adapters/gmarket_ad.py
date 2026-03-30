import pandas as pd
from app.parsers.adapters.base import BaseAdapter
from app.parsers.column_mapper import apply_column_mapping


class GmarketAdAdapter(BaseAdapter):
    platform_name = "지마켓/옥션 광고"
    data_type = "ad"

    def get_column_mapping(self):
        return {
            "site": "사이트", "product_id": "광고상품번호",
            "impressions": "노출수", "clicks": "클릭수", "spend": "총비용",
            "direct_conversions": "구매수", "direct_revenue": "구매금액",
            "avg_rank": "평균노출순위", "exposure_area": "영역명",
        }

    def transform(self, df):
        df = apply_column_mapping(df, self.get_column_mapping())
        df["product_id"] = df["product_id"].astype(str)
        for col in ["impressions", "clicks", "spend", "direct_conversions", "direct_revenue", "avg_rank"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df

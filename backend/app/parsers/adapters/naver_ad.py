import pandas as pd
from app.parsers.adapters.base import BaseAdapter
from app.parsers.column_mapper import apply_column_mapping, apply_null_values, parse_date_column


class NaverAdAdapter(BaseAdapter):
    platform_name = "네이버 검색광고"
    data_type = "ad"

    def get_column_mapping(self):
        return {
            "ad_date": "일별", "campaign_name": "캠페인", "ad_group": "광고그룹",
            "keyword": "키워드", "ad_type": "캠페인유형",
            "spend": "총비용(VAT포함,원)", "clicks": "클릭수", "impressions": "노출수",
            "direct_conversions": "직접전환수", "indirect_conversions": "간접전환수",
            "direct_revenue": "전환매출액(원)",
        }

    def get_parsing_rules(self):
        return {"skip_rows": 1, "date_format": "YYYY.MM.DD.", "vat_included": True, "null_values": ["-"]}

    def transform(self, df):
        df = apply_column_mapping(df, self.get_column_mapping())
        df = apply_null_values(df, ["-"])
        df = parse_date_column(df, "ad_date", date_format="YYYY.MM.DD.")
        for col in ["spend", "clicks", "impressions", "direct_conversions", "indirect_conversions", "direct_revenue"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df

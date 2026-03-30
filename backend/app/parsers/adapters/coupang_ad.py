import pandas as pd
from app.parsers.adapters.base import BaseAdapter
from app.parsers.column_mapper import apply_column_mapping


class CoupangAdAdapter(BaseAdapter):
    platform_name = "쿠팡 광고"
    data_type = "ad"

    _base_mapping = {
        "campaign_name": "캠페인 이름", "ad_group": "광고명",
        "ad_type": "광고 유형", "exposure_area": "노출 영역",
        "option_id": "광고 집행 옵션 ID", "spend": "광고비(원)",
        "impressions": "노출수", "clicks": "클릭수",
    }
    _attribution_mappings = {
        "1d": {
            "direct_conversions": "직접주문수(1일)", "indirect_conversions": "간접주문수(1일)",
            "direct_revenue": "직접매출(1일)", "indirect_revenue": "간접매출(1일)",
        },
        "14d": {
            "direct_conversions": "직접주문수(14일)", "indirect_conversions": "간접주문수(14일)",
            "direct_revenue": "직접매출(14일)", "indirect_revenue": "간접매출(14일)",
        },
    }

    def get_parsing_rules(self):
        return {"skip_rows": 0, "attribution_windows": ["1d", "14d"], "split_by_attribution": True}

    def transform(self, df):
        base_df = apply_column_mapping(df, self._base_mapping)
        rows = []
        for window, attr_mapping in self._attribution_mappings.items():
            window_df = base_df.copy()
            for target, source in attr_mapping.items():
                if source in df.columns:
                    window_df[target] = pd.to_numeric(df[source], errors="coerce").fillna(0)
            window_df["attribution_window"] = window
            rows.append(window_df)
        result = pd.concat(rows, ignore_index=True)
        for col in ["spend", "impressions", "clicks"]:
            if col in result.columns:
                result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0)
        result["option_id"] = result["option_id"].astype(str)
        return result

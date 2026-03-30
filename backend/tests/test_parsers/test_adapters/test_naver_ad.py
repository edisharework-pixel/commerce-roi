import pandas as pd
from app.parsers.adapters.naver_ad import NaverAdAdapter


class TestNaverAdAdapter:
    def test_data_type(self):
        adapter = NaverAdAdapter()
        assert adapter.data_type == "ad"
        assert adapter.platform_name == "네이버 검색광고"

    def test_transform_date_and_nulls(self):
        adapter = NaverAdAdapter()
        df = pd.DataFrame({
            "일별": ["2026.03.15."],
            "캠페인": ["브랜드캠페인"],
            "광고그룹": ["메인그룹"],
            "키워드": ["-"],
            "캠페인유형": ["파워링크"],
            "총비용(VAT포함,원)": ["15000"],
            "클릭수": ["50"],
            "노출수": ["1000"],
            "직접전환수": ["3"],
            "간접전환수": ["-"],
            "전환매출액(원)": ["90000"],
        })
        result = adapter.transform(df)
        assert result["ad_date"].iloc[0] == pd.Timestamp("2026-03-15")
        assert pd.isna(result["keyword"].iloc[0])
        assert result["spend"].iloc[0] == 15000
        assert result["clicks"].iloc[0] == 50
        assert result["indirect_conversions"].iloc[0] == 0  # "-" -> NaN -> 0

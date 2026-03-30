import pandas as pd
from app.parsers.adapters.coupang_ad import CoupangAdAdapter


class TestCoupangAdAdapter:
    def test_data_type(self):
        adapter = CoupangAdAdapter()
        assert adapter.data_type == "ad"
        assert adapter.platform_name == "쿠팡 광고"

    def test_attribution_split(self):
        adapter = CoupangAdAdapter()
        df = pd.DataFrame({
            "캠페인 이름": ["캠페인A"],
            "광고명": ["광고그룹1"],
            "광고 유형": ["CPC"],
            "노출 영역": ["검색"],
            "광고 집행 옵션 ID": [12345],
            "광고비(원)": ["5000"],
            "노출수": ["1000"],
            "클릭수": ["50"],
            "직접주문수(1일)": ["3"],
            "간접주문수(1일)": ["1"],
            "직접매출(1일)": ["90000"],
            "간접매출(1일)": ["30000"],
            "직접주문수(14일)": ["5"],
            "간접주문수(14일)": ["2"],
            "직접매출(14일)": ["150000"],
            "간접매출(14일)": ["60000"],
        })
        result = adapter.transform(df)
        # 1 input row should produce 2 output rows
        assert len(result) == 2
        row_1d = result[result["attribution_window"] == "1d"].iloc[0]
        row_14d = result[result["attribution_window"] == "14d"].iloc[0]
        # Both share the same spend
        assert row_1d["spend"] == 5000
        assert row_14d["spend"] == 5000
        # 1d attribution values
        assert row_1d["direct_conversions"] == 3
        assert row_1d["direct_revenue"] == 90000
        # 14d attribution values
        assert row_14d["direct_conversions"] == 5
        assert row_14d["indirect_revenue"] == 60000
        # option_id is string
        assert pd.api.types.is_string_dtype(result["option_id"])

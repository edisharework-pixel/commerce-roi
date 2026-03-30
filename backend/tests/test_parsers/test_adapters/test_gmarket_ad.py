import pandas as pd
from app.parsers.adapters.gmarket_ad import GmarketAdAdapter


class TestGmarketAdAdapter:
    def test_data_type(self):
        adapter = GmarketAdAdapter()
        assert adapter.data_type == "ad"
        assert adapter.platform_name == "지마켓/옥션 광고"

    def test_transform(self):
        adapter = GmarketAdAdapter()
        df = pd.DataFrame({
            "사이트": ["G마켓", "옥션"],
            "광고상품번호": [11111, 22222],
            "노출수": ["500", "1000"],
            "클릭수": ["25", "50"],
            "총비용": ["10000", "20000"],
            "구매수": ["2", "5"],
            "구매금액": ["60000", "150000"],
            "평균노출순위": ["3.5", "2.1"],
            "영역명": ["키워드검색", "키워드검색"],
        })
        result = adapter.transform(df)
        assert result["site"].iloc[0] == "G마켓"
        assert pd.api.types.is_string_dtype(result["product_id"])
        assert result["impressions"].iloc[0] == 500
        assert result["spend"].iloc[1] == 20000
        assert result["direct_conversions"].iloc[1] == 5
        assert result["avg_rank"].iloc[0] == 3.5

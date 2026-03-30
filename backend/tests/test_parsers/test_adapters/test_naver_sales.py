import pandas as pd
from app.parsers.adapters.naver_sales import NaverSalesAdapter


class TestNaverSalesAdapter:
    def test_data_type(self):
        adapter = NaverSalesAdapter()
        assert adapter.data_type == "sales_summary"
        assert adapter.platform_name == "네이버 스마트스토어"

    def test_transform(self):
        adapter = NaverSalesAdapter()
        df = pd.DataFrame({
            "상품번호": [12345, 67890],
            "상품명": ["테스트상품A", "테스트상품B"],
            "결제상품수량": ["10", "20"],
            "결제금액": ["50000", "100000"],
            "환불금액": ["0", "5000"],
            "환불수량": ["0", "1"],
            "상품쿠폰합계": ["1000", "2000"],
            "주문쿠폰합계": ["500", "0"],
        })
        result = adapter.transform(df)
        assert "product_id" in result.columns
        assert "product_name" in result.columns
        assert "net_revenue" in result.columns
        assert pd.api.types.is_string_dtype(result["product_id"])
        assert result["quantity"].iloc[0] == 10
        assert result["net_revenue"].iloc[1] == 100000
        assert result["refund_amount"].iloc[1] == 5000
        assert result["coupon_seller"].iloc[0] == 1000

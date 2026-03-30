import pandas as pd
from app.parsers.adapters.coupang_sales import CoupangSalesAdapter


class TestCoupangSalesAdapter:
    def test_data_type(self):
        adapter = CoupangSalesAdapter()
        assert adapter.data_type == "sales_summary"
        assert adapter.platform_name == "쿠팡"

    def test_transform(self):
        adapter = CoupangSalesAdapter()
        df = pd.DataFrame({
            "옵션 ID": [111222, 333444],
            "등록상품 ID": [55555, 66666],
            "노출상품명": ["상품A", "상품B"],
            "옵션명: 옵션값": ["색상: 빨강", "색상: 파랑"],
            "매출(원)": ["100000", "200000"],
            "총 매출(원)": ["120000", "230000"],
            "총 취소 금액(원)": ["0", "10000"],
            "총 취소된 상품수": ["0", "1"],
            "판매량": ["5", "10"],
            "방문자": ["100", "200"],
            "조회": ["150", "300"],
            "장바구니": ["20", "40"],
        })
        result = adapter.transform(df)
        assert pd.api.types.is_string_dtype(result["option_id"])
        assert pd.api.types.is_string_dtype(result["product_id"])
        assert result["net_revenue"].iloc[0] == 100000
        assert result["quantity"].iloc[1] == 10
        assert result["visitors"].iloc[0] == 100

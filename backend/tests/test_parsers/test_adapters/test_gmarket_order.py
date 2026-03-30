import pandas as pd
from app.parsers.adapters.gmarket_order import GmarketOrderAdapter


class TestGmarketOrderAdapter:
    def test_data_type(self):
        adapter = GmarketOrderAdapter()
        assert adapter.data_type == "order"
        assert adapter.platform_name == "지마켓"

    def test_site_mapping_and_date(self):
        adapter = GmarketOrderAdapter()
        df = pd.DataFrame({
            "판매아이디": ["지마켓(itholic)", "옥션(itemholic)"],
            "결제일": ["2026-03-15", "2026-03-16"],
            "주문번호": ["ORD001", "ORD002"],
            "상품번호": [12345, 67890],
            "상품명": ["상품A", "상품B"],
            "수량": ["2", "3"],
            "구매금액": ["50000", "75000"],
            "진행상태": ["배송완료", "배송중"],
        })
        result = adapter.transform(df)
        assert result["site"].iloc[0] == "G"
        assert result["site"].iloc[1] == "A"
        assert result["order_date"].iloc[0] == pd.Timestamp("2026-03-15")
        assert pd.api.types.is_string_dtype(result["product_id"])
        assert result["quantity"].iloc[0] == 2
        assert result["sale_price"].iloc[1] == 75000

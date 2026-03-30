import pandas as pd
import pytest
from app.parsers.column_mapper import apply_column_mapping, apply_null_values, parse_date_column

def test_apply_column_mapping():
    df = pd.DataFrame({"상품번호": [123], "결제금액": [50000]})
    mapping = {"product_id": "상품번호", "net_revenue": "결제금액"}
    result = apply_column_mapping(df, mapping)
    assert "product_id" in result.columns
    assert result.iloc[0]["net_revenue"] == 50000

def test_apply_column_mapping_missing_column():
    df = pd.DataFrame({"상품번호": [123]})
    mapping = {"product_id": "상품번호", "net_revenue": "결제금액"}
    result = apply_column_mapping(df, mapping)
    assert "product_id" in result.columns
    assert "net_revenue" not in result.columns

def test_apply_null_values():
    df = pd.DataFrame({"keyword": ["-", "바디트리머", "-"]})
    result = apply_null_values(df, null_values=["-"])
    assert pd.isna(result.iloc[0]["keyword"])
    assert result.iloc[1]["keyword"] == "바디트리머"

def test_parse_date_column_dot_format():
    df = pd.DataFrame({"ad_date": ["2026.03.15.", "2026.03.16."]})
    result = parse_date_column(df, "ad_date", date_format="YYYY.MM.DD.")
    assert str(result.iloc[0]["ad_date"].date()) == "2026-03-15"

def test_parse_date_column_standard():
    df = pd.DataFrame({"order_date": ["2026-03-15", "2026-03-16"]})
    result = parse_date_column(df, "order_date")
    assert str(result.iloc[0]["order_date"].date()) == "2026-03-15"

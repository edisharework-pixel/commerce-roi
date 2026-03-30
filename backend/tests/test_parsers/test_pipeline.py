import io

from app.parsers.adapters.coupang_ad import CoupangAdAdapter
from app.parsers.adapters.gmarket_order import GmarketOrderAdapter
from app.parsers.adapters.naver_sales import NaverSalesAdapter
from app.parsers.pipeline import ParseResult, run_parse_pipeline


def test_parse_naver_sales():
    csv = "상품번호,상품명,결제상품수량,결제금액,환불금액,환불수량,상품쿠폰합계,주문쿠폰합계\n12345678,바디트리머,150,4500000,300000,5,50000,30000"
    result = run_parse_pipeline(
        io.BytesIO(csv.encode("utf-8-sig")), "csv", NaverSalesAdapter()
    )
    assert isinstance(result, ParseResult)
    assert result.row_count == 1
    assert result.data.iloc[0]["net_revenue"] == 4500000


def test_parse_gmarket_order():
    csv = "주문번호,결제일,상품번호,상품명,수량,구매금액,진행상태,판매아이디\nGM-001,2026-03-15,GP-100,바디트리머,1,45900,배송완료,지마켓(itholic)"
    result = run_parse_pipeline(
        io.BytesIO(csv.encode("utf-8-sig")), "csv", GmarketOrderAdapter()
    )
    assert result.row_count == 1
    assert result.data.iloc[0]["site"] == "G"


def test_parse_coupang_ad_doubles_rows():
    csv = "캠페인 이름,광고명,광고 유형,노출 영역,광고 집행 옵션 ID,광고비(원),노출수,클릭수,직접주문수(1일),간접주문수(1일),직접매출(1일),간접매출(1일),직접주문수(14일),간접주문수(14일),직접매출(14일),간접매출(14일)\n바디트리머,블랙,상품,검색,OPT-001,85000,15000,350,12,5,600000,250000,18,8,900000,400000"
    result = run_parse_pipeline(
        io.BytesIO(csv.encode("utf-8-sig")), "csv", CoupangAdAdapter()
    )
    assert result.row_count == 2  # 1d + 14d split

# Phase 2: CSV 파싱 엔진 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 엑셀/CSV 파일을 업로드하면 플랫폼별 템플릿에 따라 파싱하고, 상품을 자동 매칭하여 sales_summary/orders/ad_data에 저장하는 파싱 엔진을 구현한다.

**Architecture:** 템플릿 기반 파서 + 채널별 어댑터 패턴. 공통 파싱 로직(파일 읽기, 컬럼 매핑)은 하나의 코어 파서가 처리하고, 채널 고유 변환(날짜 포맷, 사이트 분리, 귀속기간 분할 등)은 채널별 어댑터가 처리. 상품 매칭은 4단계 파이프라인(정확→판매자코드→유사→AI)으로 분리.

**Tech Stack:** pandas, openpyxl (엑셀/비밀번호 엑셀), msoffcrypto-tool (비밀번호 엑셀 복호화), Python difflib (유사 매칭)

---

## 파일 구조

```
backend/
├── app/
│   ├── models/                    # (Phase 1 — 기존)
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── file_reader.py         # 파일 읽기 (CSV/Excel/비밀번호 Excel)
│   │   ├── column_mapper.py       # column_mapping 기반 컬럼 변환
│   │   ├── template_registry.py   # 파싱 템플릿 DB 관리 (CRUD + 조회)
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # BaseAdapter 인터페이스
│   │   │   ├── naver_sales.py     # 네이버 상품성과 어댑터
│   │   │   ├── naver_ad.py        # 네이버 광고 어댑터
│   │   │   ├── coupang_sales.py   # 쿠팡 판매 어댑터
│   │   │   ├── coupang_ad.py      # 쿠팡 광고 어댑터
│   │   │   ├── coupang_catalog.py # 쿠팡 상품 카탈로그 어댑터
│   │   │   ├── gmarket_order.py   # 지마켓/옥션 주문 어댑터
│   │   │   └── gmarket_ad.py      # 지마켓/옥션 광고 어댑터
│   │   └── pipeline.py            # 파싱 파이프라인 오케스트레이터
│   ├── matching/
│   │   ├── __init__.py
│   │   ├── product_matcher.py     # 4단계 상품 매칭 파이프라인
│   │   └── similarity.py          # 상품명 유사도 비교 유틸
│   └── services/
│       ├── __init__.py
│       └── upload_service.py      # 업로드 → 파싱 → 매칭 → 저장 통합 서비스
├── tests/
│   ├── test_parsers/
│   │   ├── __init__.py
│   │   ├── test_file_reader.py
│   │   ├── test_column_mapper.py
│   │   ├── test_template_registry.py
│   │   ├── test_adapters/
│   │   │   ├── __init__.py
│   │   │   ├── test_naver_sales.py
│   │   │   ├── test_naver_ad.py
│   │   │   ├── test_coupang_sales.py
│   │   │   ├── test_coupang_ad.py
│   │   │   ├── test_gmarket_order.py
│   │   │   └── test_gmarket_ad.py
│   │   └── test_pipeline.py
│   ├── test_matching/
│   │   ├── __init__.py
│   │   ├── test_product_matcher.py
│   │   └── test_similarity.py
│   ├── test_services/
│   │   ├── __init__.py
│   │   └── test_upload_service.py
│   └── fixtures/                  # 테스트용 샘플 CSV/Excel 파일
│       ├── naver_sales_sample.csv
│       ├── naver_ad_sample.csv
│       ├── coupang_sales_sample.csv
│       ├── coupang_ad_sample.csv
│       ├── gmarket_order_sample.csv
│       └── gmarket_ad_sample.csv
```

---

### Task 1: 의존성 추가 + 테스트 픽스처 파일 생성

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/tests/fixtures/naver_sales_sample.csv`
- Create: `backend/tests/fixtures/naver_ad_sample.csv`
- Create: `backend/tests/fixtures/coupang_sales_sample.csv`
- Create: `backend/tests/fixtures/coupang_ad_sample.csv`
- Create: `backend/tests/fixtures/gmarket_order_sample.csv`
- Create: `backend/tests/fixtures/gmarket_ad_sample.csv`

- [ ] **Step 1: pyproject.toml에 의존성 추가**

```toml
# backend/pyproject.toml — dependencies에 추가
    "pandas>=2.2.0",
    "openpyxl>=3.1.0",
    "msoffcrypto-tool>=5.4.0",
```

- [ ] **Step 2: 의존성 설치**

Run: `cd backend && source .venv/Scripts/activate && pip install -e ".[dev]"`

- [ ] **Step 3: 네이버 상품성과 샘플 CSV 생성**

```csv
상품번호,상품명,결제상품수량,결제금액,환불금액,환불수량,상품쿠폰합계,주문쿠폰합계
12345678,바디트리머 프로 남성용,150,4500000,300000,5,50000,30000
23456789,볼펜녹음기 32GB,80,3200000,160000,3,20000,10000
34567890,휴대용 선풍기 미니,200,2000000,100000,8,40000,20000
```

- [ ] **Step 4: 네이버 광고 샘플 CSV 생성**

```csv
계정 보고서(2026.03.01.~2026.03.31.)
일별,캠페인,광고그룹,키워드,캠페인유형,총비용(VAT포함,원),클릭수,노출수,직접전환수,간접전환수,전환매출액(원),평균노출순위
2026.03.15.,◆바디트리머,바디트리머_쇼핑,-,쇼핑검색,55000,120,8500,8,3,480000,2.3
2026.03.15.,14.볼펜녹음기_쇼핑,볼펜녹음기_파워링크,볼펜녹음기,파워링크,32000,85,6200,5,2,250000,3.1
2026.03.16.,◆바디트리머,바디트리머_쇼핑,-,쇼핑검색,48000,110,7800,7,2,420000,2.5
```

- [ ] **Step 5: 쿠팡 판매 샘플 CSV 생성**

```csv
등록상품 ID,노출상품명,옵션 ID,옵션명: 옵션값,매출(원),총 매출(원),판매량,총 취소 금액(원),총 취소된 상품수,방문자,조회,장바구니
CP-100,바디트리머 프로,OPT-001,블랙,2500000,3000000,50,500000,10,3000,5000,120
CP-100,바디트리머 프로,OPT-002,화이트,1800000,2100000,35,300000,5,2500,4000,90
CP-200,볼펜녹음기 32GB,OPT-003,기본,1500000,1700000,40,200000,4,2000,3500,80
```

- [ ] **Step 6: 쿠팡 광고 샘플 CSV 생성**

```csv
캠페인 이름,광고명,광고 유형,노출 영역,광고 집행 옵션 ID,광고비(원),노출수,클릭수,직접주문수(1일),간접주문수(1일),직접매출(1일),간접매출(1일),직접주문수(14일),간접주문수(14일),직접매출(14일),간접매출(14일)
바디트리머_캠페인,바디트리머 프로 블랙,상품,검색,OPT-001,85000,15000,350,12,5,600000,250000,18,8,900000,400000
볼펜녹음기_캠페인,볼펜녹음기 32GB,상품,비검색,OPT-003,45000,8000,180,6,3,240000,120000,10,5,400000,200000
```

- [ ] **Step 7: 지마켓/옥션 주문 샘플 CSV 생성**

```csv
주문번호,결제일,상품번호,상품명,수량,구매금액,진행상태,판매아이디
GM-001,2026-03-15,GP-100,바디트리머 프로,1,45900,배송완료,지마켓(itholic)
GM-002,2026-03-15,GP-100,바디트리머 프로,2,91800,배송완료,지마켓(itholic)
GM-003,2026-03-16,GP-200,볼펜녹음기 32GB,1,39900,취소완료,지마켓(itholic)
AU-001,2026-03-15,AP-100,바디트리머 프로,1,44900,배송완료,옥션(itemholic)
AU-002,2026-03-16,AP-200,볼펜녹음기 32GB,1,38900,반품완료,옥션(itemholic)
```

- [ ] **Step 8: 지마켓/옥션 광고 샘플 CSV 생성**

```csv
사이트,광고상품번호,노출수,클릭수,총비용,구매수,구매금액,평균노출순위,영역명
G,GP-100,5000,120,35000,8,367200,2.1,쇼핑검색
G,GP-200,3000,80,22000,4,159600,3.5,쇼핑검색
A,AP-100,4000,95,28000,6,269400,2.8,쇼핑검색
```

- [ ] **Step 9: Commit**

```bash
git add backend/pyproject.toml backend/tests/fixtures/
git commit -m "feat: add parsing dependencies and test fixture CSV files"
```

---

### Task 2: 파일 리더 (CSV/Excel/비밀번호 Excel)

**Files:**
- Create: `backend/app/parsers/__init__.py`
- Create: `backend/app/parsers/file_reader.py`
- Create: `backend/tests/test_parsers/__init__.py`
- Create: `backend/tests/test_parsers/test_file_reader.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_parsers/test_file_reader.py
import io
import pytest
import pandas as pd
from app.parsers.file_reader import read_file


def test_read_csv_file():
    csv_content = "이름,수량,금액\n상품A,10,50000\n상품B,20,80000"
    buffer = io.BytesIO(csv_content.encode("utf-8-sig"))
    df = read_file(buffer, file_type="csv")
    assert len(df) == 2
    assert list(df.columns) == ["이름", "수량", "금액"]
    assert df.iloc[0]["이름"] == "상품A"


def test_read_csv_with_skip_rows():
    csv_content = "제목행 무시\n이름,수량\n상품A,10\n상품B,20"
    buffer = io.BytesIO(csv_content.encode("utf-8-sig"))
    df = read_file(buffer, file_type="csv", skip_rows=1)
    assert len(df) == 2
    assert "이름" in df.columns


def test_read_xlsx_file(tmp_path):
    df_orig = pd.DataFrame({"상품명": ["A", "B"], "금액": [1000, 2000]})
    path = tmp_path / "test.xlsx"
    df_orig.to_excel(path, index=False)
    with open(path, "rb") as f:
        df = read_file(f, file_type="xlsx")
    assert len(df) == 2
    assert "상품명" in df.columns


def test_read_xlsx_with_sheet_and_header(tmp_path):
    df_orig = pd.DataFrame({"상품명": ["A"], "금액": [1000]})
    path = tmp_path / "test.xlsx"
    with pd.ExcelWriter(path) as writer:
        df_orig.to_excel(writer, sheet_name="Template", index=False, startrow=3)
    with open(path, "rb") as f:
        df = read_file(f, file_type="xlsx", sheet_name="Template", header_row=3)
    assert len(df) == 1
    assert "상품명" in df.columns


def test_read_file_unsupported_type():
    buffer = io.BytesIO(b"data")
    with pytest.raises(ValueError, match="Unsupported file type"):
        read_file(buffer, file_type="json")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_parsers/test_file_reader.py -v`
Expected: FAIL

- [ ] **Step 3: Implement file_reader.py**

```python
# backend/app/parsers/file_reader.py
import io
from typing import BinaryIO

import pandas as pd


def read_file(
    file: BinaryIO,
    file_type: str,
    skip_rows: int = 0,
    sheet_name: str | None = None,
    header_row: int = 0,
    password: str | None = None,
) -> pd.DataFrame:
    """Read a CSV or Excel file into a DataFrame.

    Args:
        file: File-like binary object
        file_type: "csv" or "xlsx"
        skip_rows: Number of rows to skip from top
        sheet_name: Excel sheet name (default: first sheet)
        header_row: Row number for header (0-indexed)
        password: Password for protected Excel files
    """
    if file_type == "csv":
        return pd.read_csv(file, skiprows=skip_rows, encoding="utf-8-sig")

    if file_type == "xlsx":
        if password:
            import msoffcrypto

            decrypted = io.BytesIO()
            ms_file = msoffcrypto.OfficeFile(file)
            ms_file.load_key(password=password)
            ms_file.decrypt(decrypted)
            decrypted.seek(0)
            file = decrypted

        return pd.read_excel(
            file,
            sheet_name=sheet_name or 0,
            header=header_row + skip_rows,
            engine="openpyxl",
        )

    raise ValueError(f"Unsupported file type: {file_type}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_parsers/test_file_reader.py -v`
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/parsers/ backend/tests/test_parsers/
git commit -m "feat: add file reader for CSV and Excel with password support"
```

---

### Task 3: 컬럼 매퍼

**Files:**
- Create: `backend/app/parsers/column_mapper.py`
- Create: `backend/tests/test_parsers/test_column_mapper.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_parsers/test_column_mapper.py
import pandas as pd
import pytest
from app.parsers.column_mapper import apply_column_mapping, apply_null_values, parse_date_column


def test_apply_column_mapping():
    df = pd.DataFrame({"상품번호": [123], "결제금액": [50000], "환불금액": [5000]})
    mapping = {"product_id": "상품번호", "net_revenue": "결제금액", "refund_amount": "환불금액"}
    result = apply_column_mapping(df, mapping)
    assert "product_id" in result.columns
    assert "net_revenue" in result.columns
    assert result.iloc[0]["net_revenue"] == 50000


def test_apply_column_mapping_missing_column():
    df = pd.DataFrame({"상품번호": [123]})
    mapping = {"product_id": "상품번호", "net_revenue": "결제금액"}
    result = apply_column_mapping(df, mapping)
    assert "product_id" in result.columns
    assert "net_revenue" not in result.columns  # missing source column is skipped


def test_apply_null_values():
    df = pd.DataFrame({"keyword": ["-", "바디트리머", "-"], "spend": [100, 200, 300]})
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
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement column_mapper.py**

```python
# backend/app/parsers/column_mapper.py
import pandas as pd


def apply_column_mapping(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Rename columns using a mapping of {target_name: source_name}.

    Only renames columns that exist in the DataFrame. Missing source columns are skipped.
    """
    reverse = {}
    for target, source in mapping.items():
        if source in df.columns:
            reverse[source] = target
    return df.rename(columns=reverse)


def apply_null_values(df: pd.DataFrame, null_values: list[str]) -> pd.DataFrame:
    """Replace specified values with NaN across the entire DataFrame."""
    return df.replace(null_values, pd.NA)


def parse_date_column(
    df: pd.DataFrame, column: str, date_format: str | None = None
) -> pd.DataFrame:
    """Parse a date column into datetime.

    Handles special formats like 'YYYY.MM.DD.' (trailing dot).
    """
    df = df.copy()
    if column not in df.columns:
        return df

    if date_format == "YYYY.MM.DD.":
        df[column] = df[column].astype(str).str.rstrip(".")
        df[column] = pd.to_datetime(df[column], format="%Y.%m.%d")
    else:
        df[column] = pd.to_datetime(df[column])

    return df
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_parsers/test_column_mapper.py -v`
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/parsers/column_mapper.py backend/tests/test_parsers/test_column_mapper.py
git commit -m "feat: add column mapper with null value handling and date parsing"
```

---

### Task 4: 채널 어댑터 — Base + 네이버 상품성과

**Files:**
- Create: `backend/app/parsers/adapters/__init__.py`
- Create: `backend/app/parsers/adapters/base.py`
- Create: `backend/app/parsers/adapters/naver_sales.py`
- Create: `backend/tests/test_parsers/test_adapters/__init__.py`
- Create: `backend/tests/test_parsers/test_adapters/test_naver_sales.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_parsers/test_adapters/test_naver_sales.py
import pandas as pd
import pytest
from app.parsers.adapters.naver_sales import NaverSalesAdapter


def test_naver_sales_transform():
    df = pd.DataFrame({
        "상품번호": ["12345678", "23456789"],
        "상품명": ["바디트리머 프로", "볼펜녹음기"],
        "결제상품수량": [150, 80],
        "결제금액": [4500000, 3200000],
        "환불금액": [300000, 160000],
        "환불수량": [5, 3],
        "상품쿠폰합계": [50000, 20000],
        "주문쿠폰합계": [30000, 10000],
    })
    adapter = NaverSalesAdapter()
    result = adapter.transform(df)

    assert "product_id" in result.columns
    assert "net_revenue" in result.columns
    assert "coupon_seller" in result.columns
    assert len(result) == 2
    assert result.iloc[0]["net_revenue"] == 4500000


def test_naver_sales_data_type():
    adapter = NaverSalesAdapter()
    assert adapter.data_type == "sales_summary"
    assert adapter.platform_name == "네이버 스마트스토어"
```

- [ ] **Step 2: Implement base adapter**

```python
# backend/app/parsers/adapters/base.py
from abc import ABC, abstractmethod

import pandas as pd


class BaseAdapter(ABC):
    """Base class for channel-specific data adapters."""

    platform_name: str
    data_type: str  # "sales_summary" | "order" | "ad" | "product_catalog"

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform raw DataFrame into standardized format.

        Apply column mapping, type conversions, and channel-specific transformations.
        Returns DataFrame with standardized column names ready for DB storage.
        """
        ...

    def get_column_mapping(self) -> dict[str, str]:
        """Return {target_column: source_column} mapping."""
        return {}

    def get_parsing_rules(self) -> dict:
        """Return parsing rules (skip_rows, date_format, etc.)."""
        return {}
```

- [ ] **Step 3: Implement naver_sales adapter**

```python
# backend/app/parsers/adapters/naver_sales.py
import pandas as pd

from app.parsers.adapters.base import BaseAdapter
from app.parsers.column_mapper import apply_column_mapping


class NaverSalesAdapter(BaseAdapter):
    platform_name = "네이버 스마트스토어"
    data_type = "sales_summary"

    def get_column_mapping(self) -> dict[str, str]:
        return {
            "product_id": "상품번호",
            "product_name": "상품명",
            "quantity": "결제상품수량",
            "net_revenue": "결제금액",
            "refund_amount": "환불금액",
            "refund_count": "환불수량",
            "coupon_seller": "상품쿠폰합계",
            "coupon_order": "주문쿠폰합계",
        }

    def get_parsing_rules(self) -> dict:
        return {
            "skip_rows": 0,
            "period_from_filename": True,
        }

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = apply_column_mapping(df, self.get_column_mapping())
        df["product_id"] = df["product_id"].astype(str)

        # Ensure numeric columns
        numeric_cols = ["quantity", "net_revenue", "refund_amount", "refund_count",
                        "coupon_seller", "coupon_order"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df
```

- [ ] **Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_parsers/test_adapters/test_naver_sales.py -v`
Expected: 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/parsers/adapters/ backend/tests/test_parsers/test_adapters/
git commit -m "feat: add BaseAdapter and NaverSalesAdapter"
```

---

### Task 5: 채널 어댑터 — 네이버 광고

**Files:**
- Create: `backend/app/parsers/adapters/naver_ad.py`
- Create: `backend/tests/test_parsers/test_adapters/test_naver_ad.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_parsers/test_adapters/test_naver_ad.py
import pandas as pd
from app.parsers.adapters.naver_ad import NaverAdAdapter


def test_naver_ad_transform():
    # Simulates file with skip_rows=1 already applied
    df = pd.DataFrame({
        "일별": ["2026.03.15.", "2026.03.16."],
        "캠페인": ["◆바디트리머", "14.볼펜녹음기_쇼핑"],
        "광고그룹": ["바디트리머_쇼핑", "볼펜녹음기_파워링크"],
        "키워드": ["-", "볼펜녹음기"],
        "캠페인유형": ["쇼핑검색", "파워링크"],
        "총비용(VAT포함,원)": [55000, 32000],
        "클릭수": [120, 85],
        "노출수": [8500, 6200],
        "직접전환수": [8, 5],
        "간접전환수": [3, 2],
        "전환매출액(원)": [480000, 250000],
    })
    adapter = NaverAdAdapter()
    result = adapter.transform(df)

    assert "ad_date" in result.columns
    assert "campaign_name" in result.columns
    assert "keyword" in result.columns
    assert str(result.iloc[0]["ad_date"].date()) == "2026-03-15"
    assert pd.isna(result.iloc[0]["keyword"])  # "-" → NaN
    assert result.iloc[0]["spend"] == 55000


def test_naver_ad_data_type():
    adapter = NaverAdAdapter()
    assert adapter.data_type == "ad"
```

- [ ] **Step 2: Implement naver_ad adapter**

```python
# backend/app/parsers/adapters/naver_ad.py
import pandas as pd

from app.parsers.adapters.base import BaseAdapter
from app.parsers.column_mapper import apply_column_mapping, apply_null_values, parse_date_column


class NaverAdAdapter(BaseAdapter):
    platform_name = "네이버 검색광고"
    data_type = "ad"

    def get_column_mapping(self) -> dict[str, str]:
        return {
            "ad_date": "일별",
            "campaign_name": "캠페인",
            "ad_group": "광고그룹",
            "keyword": "키워드",
            "ad_type": "캠페인유형",
            "spend": "총비용(VAT포함,원)",
            "clicks": "클릭수",
            "impressions": "노출수",
            "direct_conversions": "직접전환수",
            "indirect_conversions": "간접전환수",
            "direct_revenue": "전환매출액(원)",
        }

    def get_parsing_rules(self) -> dict:
        return {
            "skip_rows": 1,
            "date_format": "YYYY.MM.DD.",
            "vat_included": True,
            "null_values": ["-"],
        }

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = apply_column_mapping(df, self.get_column_mapping())
        df = apply_null_values(df, ["-"])
        df = parse_date_column(df, "ad_date", date_format="YYYY.MM.DD.")

        numeric_cols = ["spend", "clicks", "impressions", "direct_conversions",
                        "indirect_conversions", "direct_revenue"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df
```

- [ ] **Step 3: Run tests, commit**

```bash
git commit -m "feat: add NaverAdAdapter with date parsing and null handling"
```

---

### Task 6: 채널 어댑터 — 쿠팡 판매 + 쿠팡 광고

**Files:**
- Create: `backend/app/parsers/adapters/coupang_sales.py`
- Create: `backend/app/parsers/adapters/coupang_ad.py`
- Create: `backend/tests/test_parsers/test_adapters/test_coupang_sales.py`
- Create: `backend/tests/test_parsers/test_adapters/test_coupang_ad.py`

- [ ] **Step 1: Write tests for coupang_sales**

```python
# backend/tests/test_parsers/test_adapters/test_coupang_sales.py
import pandas as pd
from app.parsers.adapters.coupang_sales import CoupangSalesAdapter


def test_coupang_sales_transform():
    df = pd.DataFrame({
        "등록상품 ID": ["CP-100", "CP-100", "CP-200"],
        "노출상품명": ["바디트리머 프로", "바디트리머 프로", "볼펜녹음기"],
        "옵션 ID": ["OPT-001", "OPT-002", "OPT-003"],
        "옵션명: 옵션값": ["블랙", "화이트", "기본"],
        "매출(원)": [2500000, 1800000, 1500000],
        "총 매출(원)": [3000000, 2100000, 1700000],
        "판매량": [50, 35, 40],
        "총 취소 금액(원)": [500000, 300000, 200000],
        "총 취소된 상품수": [10, 5, 4],
        "방문자": [3000, 2500, 2000],
        "조회": [5000, 4000, 3500],
        "장바구니": [120, 90, 80],
    })
    adapter = CoupangSalesAdapter()
    result = adapter.transform(df)

    assert "option_id" in result.columns
    assert "product_id" in result.columns
    assert "net_revenue" in result.columns
    assert "visitors" in result.columns
    assert result.iloc[0]["option_id"] == "OPT-001"
    assert result.iloc[0]["net_revenue"] == 2500000


def test_coupang_sales_data_type():
    adapter = CoupangSalesAdapter()
    assert adapter.data_type == "sales_summary"
```

- [ ] **Step 2: Write tests for coupang_ad**

```python
# backend/tests/test_parsers/test_adapters/test_coupang_ad.py
import pandas as pd
from app.parsers.adapters.coupang_ad import CoupangAdAdapter


def test_coupang_ad_splits_attribution_windows():
    df = pd.DataFrame({
        "캠페인 이름": ["바디트리머_캠페인"],
        "광고명": ["바디트리머 프로 블랙"],
        "광고 유형": ["상품"],
        "노출 영역": ["검색"],
        "광고 집행 옵션 ID": ["OPT-001"],
        "광고비(원)": [85000],
        "노출수": [15000],
        "클릭수": [350],
        "직접주문수(1일)": [12],
        "간접주문수(1일)": [5],
        "직접매출(1일)": [600000],
        "간접매출(1일)": [250000],
        "직접주문수(14일)": [18],
        "간접주문수(14일)": [8],
        "직접매출(14일)": [900000],
        "간접매출(14일)": [400000],
    })
    adapter = CoupangAdAdapter()
    result = adapter.transform(df)

    # Should produce 2 rows (1d + 14d) per input row
    assert len(result) == 2
    row_1d = result[result["attribution_window"] == "1d"].iloc[0]
    row_14d = result[result["attribution_window"] == "14d"].iloc[0]
    assert row_1d["direct_conversions"] == 12
    assert row_14d["direct_conversions"] == 18
    assert row_1d["spend"] == 85000
    assert row_14d["spend"] == 85000  # spend is same for both windows
```

- [ ] **Step 3: Implement coupang_sales adapter**

```python
# backend/app/parsers/adapters/coupang_sales.py
import pandas as pd

from app.parsers.adapters.base import BaseAdapter
from app.parsers.column_mapper import apply_column_mapping


class CoupangSalesAdapter(BaseAdapter):
    platform_name = "쿠팡"
    data_type = "sales_summary"

    def get_column_mapping(self) -> dict[str, str]:
        return {
            "option_id": "옵션 ID",
            "product_id": "등록상품 ID",
            "product_name": "노출상품명",
            "option_name": "옵션명: 옵션값",
            "net_revenue": "매출(원)",
            "gross_revenue": "총 매출(원)",
            "cancel_amount": "총 취소 금액(원)",
            "cancel_quantity": "총 취소된 상품수",
            "quantity": "판매량",
            "visitors": "방문자",
            "page_views": "조회",
            "cart_count": "장바구니",
        }

    def get_parsing_rules(self) -> dict:
        return {"skip_rows": 0, "period_from_upload": True}

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = apply_column_mapping(df, self.get_column_mapping())
        df["option_id"] = df["option_id"].astype(str)
        df["product_id"] = df["product_id"].astype(str)

        numeric_cols = ["net_revenue", "gross_revenue", "cancel_amount", "cancel_quantity",
                        "quantity", "visitors", "page_views", "cart_count"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df
```

- [ ] **Step 4: Implement coupang_ad adapter**

```python
# backend/app/parsers/adapters/coupang_ad.py
import pandas as pd

from app.parsers.adapters.base import BaseAdapter
from app.parsers.column_mapper import apply_column_mapping


class CoupangAdAdapter(BaseAdapter):
    platform_name = "쿠팡 광고"
    data_type = "ad"

    _base_mapping = {
        "campaign_name": "캠페인 이름",
        "ad_group": "광고명",
        "ad_type": "광고 유형",
        "exposure_area": "노출 영역",
        "option_id": "광고 집행 옵션 ID",
        "spend": "광고비(원)",
        "impressions": "노출수",
        "clicks": "클릭수",
    }

    _attribution_mappings = {
        "1d": {
            "direct_conversions": "직접주문수(1일)",
            "indirect_conversions": "간접주문수(1일)",
            "direct_revenue": "직접매출(1일)",
            "indirect_revenue": "간접매출(1일)",
        },
        "14d": {
            "direct_conversions": "직접주문수(14일)",
            "indirect_conversions": "간접주문수(14일)",
            "direct_revenue": "직접매출(14일)",
            "indirect_revenue": "간접매출(14일)",
        },
    }

    def get_parsing_rules(self) -> dict:
        return {"skip_rows": 0, "attribution_windows": ["1d", "14d"], "split_by_attribution": True}

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
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

        numeric_cols = ["spend", "impressions", "clicks"]
        for col in numeric_cols:
            if col in result.columns:
                result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0)

        result["option_id"] = result["option_id"].astype(str)
        return result
```

- [ ] **Step 5: Run all adapter tests**

Run: `cd backend && python -m pytest tests/test_parsers/test_adapters/ -v`
Expected: 6 tests PASS (2 naver_sales + 2 naver_ad + 2 coupang)

- [ ] **Step 6: Commit**

```bash
git add backend/app/parsers/adapters/ backend/tests/test_parsers/test_adapters/
git commit -m "feat: add CoupangSalesAdapter and CoupangAdAdapter with attribution split"
```

---

### Task 7: 채널 어댑터 — 지마켓/옥션 주문 + 광고

**Files:**
- Create: `backend/app/parsers/adapters/gmarket_order.py`
- Create: `backend/app/parsers/adapters/gmarket_ad.py`
- Create: `backend/tests/test_parsers/test_adapters/test_gmarket_order.py`
- Create: `backend/tests/test_parsers/test_adapters/test_gmarket_ad.py`

- [ ] **Step 1: Write tests for gmarket_order**

```python
# backend/tests/test_parsers/test_adapters/test_gmarket_order.py
import pandas as pd
from app.parsers.adapters.gmarket_order import GmarketOrderAdapter


def test_gmarket_order_splits_by_site():
    df = pd.DataFrame({
        "주문번호": ["GM-001", "AU-001"],
        "결제일": ["2026-03-15", "2026-03-15"],
        "상품번호": ["GP-100", "AP-100"],
        "상품명": ["바디트리머", "바디트리머"],
        "수량": [1, 1],
        "구매금액": [45900, 44900],
        "진행상태": ["배송완료", "배송완료"],
        "판매아이디": ["지마켓(itholic)", "옥션(itemholic)"],
    })
    adapter = GmarketOrderAdapter()
    result = adapter.transform(df)

    assert "site" in result.columns
    assert "order_date" in result.columns
    assert result.iloc[0]["site"] == "G"
    assert result.iloc[1]["site"] == "A"


def test_gmarket_order_data_type():
    adapter = GmarketOrderAdapter()
    assert adapter.data_type == "order"
```

- [ ] **Step 2: Write tests for gmarket_ad**

```python
# backend/tests/test_parsers/test_adapters/test_gmarket_ad.py
import pandas as pd
from app.parsers.adapters.gmarket_ad import GmarketAdAdapter


def test_gmarket_ad_transform():
    df = pd.DataFrame({
        "사이트": ["G", "A"],
        "광고상품번호": ["GP-100", "AP-100"],
        "노출수": [5000, 4000],
        "클릭수": [120, 95],
        "총비용": [35000, 28000],
        "구매수": [8, 6],
        "구매금액": [367200, 269400],
        "평균노출순위": [2.1, 2.8],
        "영역명": ["쇼핑검색", "쇼핑검색"],
    })
    adapter = GmarketAdAdapter()
    result = adapter.transform(df)

    assert result.iloc[0]["site"] == "G"
    assert result.iloc[0]["product_id"] == "GP-100"
    assert result.iloc[0]["spend"] == 35000


def test_gmarket_ad_data_type():
    adapter = GmarketAdAdapter()
    assert adapter.data_type == "ad"
```

- [ ] **Step 3: Implement gmarket_order adapter**

```python
# backend/app/parsers/adapters/gmarket_order.py
import pandas as pd

from app.parsers.adapters.base import BaseAdapter
from app.parsers.column_mapper import apply_column_mapping, parse_date_column

SITE_MAP = {
    "지마켓(itholic)": "G",
    "옥션(itemholic)": "A",
}


class GmarketOrderAdapter(BaseAdapter):
    platform_name = "지마켓"
    data_type = "order"

    def get_column_mapping(self) -> dict[str, str]:
        return {
            "order_date": "결제일",
            "order_number": "주문번호",
            "product_id": "상품번호",
            "product_name": "상품명",
            "quantity": "수량",
            "sale_price": "구매금액",
            "status": "진행상태",
        }

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        # Map site from 판매아이디 column
        if "판매아이디" in df.columns:
            df["site"] = df["판매아이디"].map(SITE_MAP)

        df = apply_column_mapping(df, self.get_column_mapping())
        df = parse_date_column(df, "order_date")
        df["product_id"] = df["product_id"].astype(str)

        numeric_cols = ["quantity", "sale_price"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df
```

- [ ] **Step 4: Implement gmarket_ad adapter**

```python
# backend/app/parsers/adapters/gmarket_ad.py
import pandas as pd

from app.parsers.adapters.base import BaseAdapter
from app.parsers.column_mapper import apply_column_mapping


class GmarketAdAdapter(BaseAdapter):
    platform_name = "지마켓/옥션 광고"
    data_type = "ad"

    def get_column_mapping(self) -> dict[str, str]:
        return {
            "site": "사이트",
            "product_id": "광고상품번호",
            "impressions": "노출수",
            "clicks": "클릭수",
            "spend": "총비용",
            "direct_conversions": "구매수",
            "direct_revenue": "구매금액",
            "avg_rank": "평균노출순위",
            "exposure_area": "영역명",
        }

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = apply_column_mapping(df, self.get_column_mapping())
        df["product_id"] = df["product_id"].astype(str)

        numeric_cols = ["impressions", "clicks", "spend", "direct_conversions",
                        "direct_revenue", "avg_rank"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df
```

- [ ] **Step 5: Run all adapter tests**

Run: `cd backend && python -m pytest tests/test_parsers/test_adapters/ -v`
Expected: 10 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/parsers/adapters/ backend/tests/test_parsers/test_adapters/
git commit -m "feat: add GmarketOrderAdapter and GmarketAdAdapter with site split"
```

---

### Task 8: 상품 매칭 엔진 (4단계 파이프라인)

**Files:**
- Create: `backend/app/matching/__init__.py`
- Create: `backend/app/matching/similarity.py`
- Create: `backend/app/matching/product_matcher.py`
- Create: `backend/tests/test_matching/__init__.py`
- Create: `backend/tests/test_matching/test_similarity.py`
- Create: `backend/tests/test_matching/test_product_matcher.py`

- [ ] **Step 1: Write similarity test**

```python
# backend/tests/test_matching/test_similarity.py
from app.matching.similarity import compute_similarity


def test_exact_match():
    assert compute_similarity("바디트리머 프로", "바디트리머 프로") == 1.0


def test_high_similarity():
    score = compute_similarity("바디트리머 프로 남성용", "바디트리머 프로 블랙")
    assert score > 0.5


def test_low_similarity():
    score = compute_similarity("바디트리머 프로", "볼펜녹음기 32GB")
    assert score < 0.3


def test_empty_strings():
    assert compute_similarity("", "") == 1.0
    assert compute_similarity("상품", "") == 0.0
```

- [ ] **Step 2: Implement similarity.py**

```python
# backend/app/matching/similarity.py
from difflib import SequenceMatcher


def compute_similarity(name_a: str, name_b: str) -> float:
    """Compute similarity score between two product names.

    Returns float between 0.0 (no match) and 1.0 (exact match).
    Uses token-based comparison for better Korean text matching.
    """
    if name_a == name_b:
        return 1.0
    if not name_a or not name_b:
        return 0.0

    # Token-based comparison
    tokens_a = set(name_a.split())
    tokens_b = set(name_b.split())

    if not tokens_a or not tokens_b:
        return 0.0

    # Jaccard + SequenceMatcher hybrid
    jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
    seq_ratio = SequenceMatcher(None, name_a, name_b).ratio()

    return (jaccard + seq_ratio) / 2
```

- [ ] **Step 3: Write product_matcher test**

```python
# backend/tests/test_matching/test_product_matcher.py
import pytest
from sqlalchemy import select

from app.matching.product_matcher import ProductMatcher, MatchResult
from app.models.platform import Platform
from app.models.product import PlatformProduct, Product


@pytest.fixture
async def matcher_fixtures(db_session):
    platform = Platform(name="쿠팡", type="마켓", fee_rate=10.8, vat_included=False)
    product = Product(name="바디트리머 프로", sku="BT-PRO", base_cost=25000, category="미용")
    db_session.add_all([platform, product])
    await db_session.commit()

    pp = PlatformProduct(
        product_id=product.id,
        platform_id=platform.id,
        platform_product_id="CP-100",
        platform_product_name="바디트리머 프로 남성용",
        seller_product_code="BT-PRO-001",
        matched_by="manual",
    )
    db_session.add(pp)
    await db_session.commit()
    return platform, product, pp


@pytest.mark.asyncio
async def test_exact_match_by_product_id(db_session, matcher_fixtures):
    platform, product, pp = await matcher_fixtures
    matcher = ProductMatcher(db_session)
    result = await matcher.match(
        platform_id=platform.id,
        platform_product_id="CP-100",
        product_name="바디트리머 프로 남성용",
    )
    assert result.matched
    assert result.platform_product_id == pp.id
    assert result.method == "exact"
    assert result.confidence == 100.0


@pytest.mark.asyncio
async def test_seller_code_match(db_session, matcher_fixtures):
    platform, product, pp = await matcher_fixtures
    matcher = ProductMatcher(db_session)
    result = await matcher.match(
        platform_id=platform.id,
        platform_product_id="NEW-ID-999",
        product_name="바디트리머",
        seller_product_code="BT-PRO-001",
    )
    assert result.matched
    assert result.method == "seller_code"


@pytest.mark.asyncio
async def test_no_match_returns_unmatched(db_session, matcher_fixtures):
    platform, _, _ = await matcher_fixtures
    matcher = ProductMatcher(db_session)
    result = await matcher.match(
        platform_id=platform.id,
        platform_product_id="UNKNOWN-999",
        product_name="완전히 다른 상품",
    )
    assert not result.matched
    assert result.method == "failed"
```

- [ ] **Step 4: Implement product_matcher.py**

```python
# backend/app/matching/product_matcher.py
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.matching.similarity import compute_similarity
from app.models.product import PlatformProduct


@dataclass
class MatchResult:
    matched: bool
    platform_product_id: int | None = None
    product_id: int | None = None
    method: str = "failed"  # exact / seller_code / similar / ai / failed
    confidence: float = 0.0


class ProductMatcher:
    SIMILARITY_THRESHOLD = 0.8

    def __init__(self, session: AsyncSession):
        self.session = session

    async def match(
        self,
        platform_id: int,
        platform_product_id: str,
        product_name: str,
        seller_product_code: str | None = None,
    ) -> MatchResult:
        """Run 4-stage matching pipeline.

        Stage 1: Exact match by platform_product_id
        Stage 2: Match by seller_product_code
        Stage 3: Similar name matching (confidence >= 80%)
        Stage 4: AI matching (placeholder — returns failed for now)
        """
        # Stage 1: Exact match
        result = await self._exact_match(platform_id, platform_product_id)
        if result:
            return result

        # Stage 2: Seller product code match
        if seller_product_code:
            result = await self._seller_code_match(platform_id, seller_product_code)
            if result:
                return result

        # Stage 3: Similar name match
        result = await self._similar_match(platform_id, product_name)
        if result:
            return result

        # Stage 4: AI match (placeholder)
        # Will be implemented in Phase 5

        return MatchResult(matched=False, method="failed", confidence=0.0)

    async def _exact_match(self, platform_id: int, platform_product_id: str) -> MatchResult | None:
        stmt = select(PlatformProduct).where(
            PlatformProduct.platform_id == platform_id,
            PlatformProduct.platform_product_id == platform_product_id,
        )
        result = await self.session.execute(stmt)
        pp = result.scalar_one_or_none()
        if pp:
            return MatchResult(
                matched=True,
                platform_product_id=pp.id,
                product_id=pp.product_id,
                method="exact",
                confidence=100.0,
            )
        return None

    async def _seller_code_match(self, platform_id: int, seller_code: str) -> MatchResult | None:
        stmt = select(PlatformProduct).where(
            PlatformProduct.seller_product_code == seller_code,
        )
        result = await self.session.execute(stmt)
        pp = result.scalar_one_or_none()
        if pp:
            return MatchResult(
                matched=True,
                platform_product_id=pp.id,
                product_id=pp.product_id,
                method="seller_code",
                confidence=95.0,
            )
        return None

    async def _similar_match(self, platform_id: int, product_name: str) -> MatchResult | None:
        stmt = select(PlatformProduct).where(
            PlatformProduct.platform_id == platform_id,
        )
        result = await self.session.execute(stmt)
        candidates = result.scalars().all()

        best_match = None
        best_score = 0.0

        for pp in candidates:
            score = compute_similarity(product_name, pp.platform_product_name)
            if score > best_score:
                best_score = score
                best_match = pp

        if best_match and best_score >= self.SIMILARITY_THRESHOLD:
            return MatchResult(
                matched=True,
                platform_product_id=best_match.id,
                product_id=best_match.product_id,
                method="similar",
                confidence=round(best_score * 100, 1),
            )
        return None
```

- [ ] **Step 5: Run matching tests**

Run: `cd backend && python -m pytest tests/test_matching/ -v`
Expected: 7 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/matching/ backend/tests/test_matching/
git commit -m "feat: add product matching engine with 4-stage pipeline"
```

---

### Task 9: 파싱 파이프라인 오케스트레이터

**Files:**
- Create: `backend/app/parsers/pipeline.py`
- Create: `backend/tests/test_parsers/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_parsers/test_pipeline.py
import io
import pytest
from app.parsers.pipeline import ParseResult, run_parse_pipeline
from app.parsers.adapters.naver_sales import NaverSalesAdapter
from app.parsers.adapters.gmarket_order import GmarketOrderAdapter
from app.parsers.adapters.coupang_ad import CoupangAdAdapter


def test_parse_naver_sales():
    csv = "상품번호,상품명,결제상품수량,결제금액,환불금액,환불수량,상품쿠폰합계,주문쿠폰합계\n12345678,바디트리머,150,4500000,300000,5,50000,30000"
    buffer = io.BytesIO(csv.encode("utf-8-sig"))
    result = run_parse_pipeline(
        file=buffer,
        file_type="csv",
        adapter=NaverSalesAdapter(),
    )
    assert isinstance(result, ParseResult)
    assert len(result.data) == 1
    assert result.data.iloc[0]["net_revenue"] == 4500000
    assert result.row_count == 1


def test_parse_gmarket_order():
    csv = "주문번호,결제일,상품번호,상품명,수량,구매금액,진행상태,판매아이디\nGM-001,2026-03-15,GP-100,바디트리머,1,45900,배송완료,지마켓(itholic)"
    buffer = io.BytesIO(csv.encode("utf-8-sig"))
    result = run_parse_pipeline(
        file=buffer,
        file_type="csv",
        adapter=GmarketOrderAdapter(),
    )
    assert len(result.data) == 1
    assert result.data.iloc[0]["site"] == "G"


def test_parse_coupang_ad_doubles_rows():
    csv = "캠페인 이름,광고명,광고 유형,노출 영역,광고 집행 옵션 ID,광고비(원),노출수,클릭수,직접주문수(1일),간접주문수(1일),직접매출(1일),간접매출(1일),직접주문수(14일),간접주문수(14일),직접매출(14일),간접매출(14일)\n바디트리머,블랙,상품,검색,OPT-001,85000,15000,350,12,5,600000,250000,18,8,900000,400000"
    buffer = io.BytesIO(csv.encode("utf-8-sig"))
    result = run_parse_pipeline(
        file=buffer,
        file_type="csv",
        adapter=CoupangAdAdapter(),
    )
    assert len(result.data) == 2  # 1d + 14d
    assert result.row_count == 2
```

- [ ] **Step 2: Implement pipeline.py**

```python
# backend/app/parsers/pipeline.py
from dataclasses import dataclass
from typing import BinaryIO

import pandas as pd

from app.parsers.adapters.base import BaseAdapter
from app.parsers.file_reader import read_file


@dataclass
class ParseResult:
    data: pd.DataFrame
    row_count: int
    adapter_name: str
    data_type: str


def run_parse_pipeline(
    file: BinaryIO,
    file_type: str,
    adapter: BaseAdapter,
    password: str | None = None,
) -> ParseResult:
    """Run the full parse pipeline: read file → apply adapter transform.

    Args:
        file: File-like binary object
        file_type: "csv" or "xlsx"
        adapter: Channel-specific adapter instance
        password: Optional password for protected Excel files
    """
    rules = adapter.get_parsing_rules()

    df = read_file(
        file=file,
        file_type=file_type,
        skip_rows=rules.get("skip_rows", 0),
        sheet_name=rules.get("sheet_name"),
        header_row=rules.get("header_row", 0),
        password=password,
    )

    transformed = adapter.transform(df)

    return ParseResult(
        data=transformed,
        row_count=len(transformed),
        adapter_name=type(adapter).__name__,
        data_type=adapter.data_type,
    )
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_parsers/test_pipeline.py -v`
Expected: 3 tests PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/parsers/pipeline.py backend/tests/test_parsers/test_pipeline.py
git commit -m "feat: add parsing pipeline orchestrator"
```

---

### Task 10: 업로드 서비스 (파싱 → 매칭 → DB 저장 통합)

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/upload_service.py`
- Create: `backend/tests/test_services/__init__.py`
- Create: `backend/tests/test_services/test_upload_service.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_services/test_upload_service.py
import io
from datetime import date

import pytest
from sqlalchemy import select

from app.models.platform import Platform
from app.models.product import PlatformProduct, Product
from app.models.sales import Order, SalesSummary
from app.models.upload import UploadHistory
from app.services.upload_service import UploadService


@pytest.fixture
async def upload_fixtures(db_session):
    """Set up platform and product for matching."""
    platform_gmarket = Platform(name="지마켓", type="마켓", fee_rate=12.0, vat_included=False, site_identifier="G", seller_id="itholic")
    platform_naver = Platform(name="네이버 스마트스토어", type="마켓", fee_rate=5.5, vat_included=True)
    product = Product(name="바디트리머 프로", sku="BT-PRO", base_cost=25000, category="미용")
    db_session.add_all([platform_gmarket, platform_naver, product])
    await db_session.commit()

    pp_gmarket = PlatformProduct(
        product_id=product.id,
        platform_id=platform_gmarket.id,
        platform_product_id="GP-100",
        platform_product_name="바디트리머 프로",
        site="G",
        matched_by="manual",
    )
    pp_naver = PlatformProduct(
        product_id=product.id,
        platform_id=platform_naver.id,
        platform_product_id="12345678",
        platform_product_name="바디트리머 프로 남성용",
        matched_by="manual",
    )
    db_session.add_all([pp_gmarket, pp_naver])
    await db_session.commit()
    return {"gmarket": platform_gmarket, "naver": platform_naver, "product": product}


@pytest.mark.asyncio
async def test_upload_gmarket_orders(db_session, upload_fixtures):
    fixtures = await upload_fixtures
    csv = "주문번호,결제일,상품번호,상품명,수량,구매금액,진행상태,판매아이디\nGM-001,2026-03-15,GP-100,바디트리머 프로,1,45900,배송완료,지마켓(itholic)"
    buffer = io.BytesIO(csv.encode("utf-8-sig"))

    service = UploadService(db_session)
    result = await service.process_upload(
        file=buffer,
        file_type="csv",
        platform_id=fixtures["gmarket"].id,
        data_type="order",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
        file_name="gmarket_orders.csv",
    )

    assert result.record_count == 1
    assert result.matched_count == 1

    # Verify order saved
    orders = (await db_session.execute(select(Order))).scalars().all()
    assert len(orders) == 1
    assert orders[0].order_number == "GM-001"
    assert orders[0].status == "배송완료"

    # Verify upload_history saved
    uploads = (await db_session.execute(select(UploadHistory))).scalars().all()
    assert len(uploads) == 1


@pytest.mark.asyncio
async def test_upload_naver_sales_summary(db_session, upload_fixtures):
    fixtures = await upload_fixtures
    csv = "상품번호,상품명,결제상품수량,결제금액,환불금액,환불수량,상품쿠폰합계,주문쿠폰합계\n12345678,바디트리머 프로 남성용,150,4500000,300000,5,50000,30000"
    buffer = io.BytesIO(csv.encode("utf-8-sig"))

    service = UploadService(db_session)
    result = await service.process_upload(
        file=buffer,
        file_type="csv",
        platform_id=fixtures["naver"].id,
        data_type="sales_summary",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
        file_name="naver_sales.csv",
    )

    assert result.record_count == 1
    assert result.matched_count == 1

    # Verify sales_summary saved
    summaries = (await db_session.execute(select(SalesSummary))).scalars().all()
    assert len(summaries) == 1
    assert summaries[0].net_revenue == 4500000
    assert summaries[0].coupon_seller == 50000
```

- [ ] **Step 2: Implement upload_service.py**

```python
# backend/app/services/upload_service.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import BinaryIO

from sqlalchemy.ext.asyncio import AsyncSession

from app.matching.product_matcher import ProductMatcher
from app.models.ad import AdData
from app.models.sales import Order, SalesSummary
from app.models.upload import MatchingLog, UploadHistory
from app.parsers.adapters.base import BaseAdapter
from app.parsers.adapters.coupang_ad import CoupangAdAdapter
from app.parsers.adapters.coupang_sales import CoupangSalesAdapter
from app.parsers.adapters.gmarket_ad import GmarketAdAdapter
from app.parsers.adapters.gmarket_order import GmarketOrderAdapter
from app.parsers.adapters.naver_ad import NaverAdAdapter
from app.parsers.adapters.naver_sales import NaverSalesAdapter
from app.parsers.pipeline import run_parse_pipeline


ADAPTER_MAP: dict[tuple[str, str], type[BaseAdapter]] = {
    # (platform_name_prefix, data_type) → adapter class
    ("네이버", "sales_summary"): NaverSalesAdapter,
    ("네이버", "ad"): NaverAdAdapter,
    ("쿠팡", "sales_summary"): CoupangSalesAdapter,
    ("쿠팡", "ad"): CoupangAdAdapter,
    ("지마켓", "order"): GmarketOrderAdapter,
    ("옥션", "order"): GmarketOrderAdapter,
    ("지마켓", "ad"): GmarketAdAdapter,
    ("옥션", "ad"): GmarketAdAdapter,
}


@dataclass
class UploadResult:
    record_count: int
    matched_count: int
    unmatched_count: int
    upload_id: int


def _get_adapter(platform_name: str, data_type: str) -> BaseAdapter:
    for (prefix, dtype), adapter_cls in ADAPTER_MAP.items():
        if platform_name.startswith(prefix) and dtype == data_type:
            return adapter_cls()
    raise ValueError(f"No adapter for platform={platform_name}, data_type={data_type}")


class UploadService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.matcher = ProductMatcher(session)

    async def process_upload(
        self,
        file: BinaryIO,
        file_type: str,
        platform_id: int,
        data_type: str,
        period_start: date,
        period_end: date,
        file_name: str,
        password: str | None = None,
    ) -> UploadResult:
        # Get platform name for adapter lookup
        from app.models.platform import Platform
        from sqlalchemy import select

        platform = (await self.session.execute(
            select(Platform).where(Platform.id == platform_id)
        )).scalar_one()

        adapter = _get_adapter(platform.name, data_type)

        # Parse file
        parse_result = run_parse_pipeline(
            file=file,
            file_type=file_type,
            adapter=adapter,
            password=password,
        )

        # Match and save
        matched = 0
        unmatched = 0

        for _, row in parse_result.data.iterrows():
            product_id_str = str(row.get("product_id", ""))
            product_name = str(row.get("product_name", ""))

            match_result = await self.matcher.match(
                platform_id=platform_id,
                platform_product_id=product_id_str,
                product_name=product_name,
                seller_product_code=row.get("seller_product_code"),
            )

            if match_result.matched:
                matched += 1
            else:
                unmatched += 1

            # Log matching result
            self.session.add(MatchingLog(
                platform_product_name=product_name,
                matched_product_id=match_result.product_id,
                method=match_result.method,
                confidence=match_result.confidence,
            ))

            # Save to appropriate table
            if match_result.matched:
                if data_type == "sales_summary":
                    self._save_sales_summary(row, match_result.platform_product_id, period_start, period_end)
                elif data_type == "order":
                    self._save_order(row, match_result.platform_product_id)
                elif data_type == "ad":
                    self._save_ad_data(row, platform_id, match_result.platform_product_id)

        # Save upload history
        upload = UploadHistory(
            platform_id=platform_id,
            data_type=data_type,
            file_name=file_name,
            record_count=parse_result.row_count,
            matched_count=matched,
            unmatched_count=unmatched,
            period_start=period_start,
            period_end=period_end,
        )
        self.session.add(upload)
        await self.session.commit()

        return UploadResult(
            record_count=parse_result.row_count,
            matched_count=matched,
            unmatched_count=unmatched,
            upload_id=upload.id,
        )

    def _save_sales_summary(self, row, pp_id: int, period_start: date, period_end: date):
        self.session.add(SalesSummary(
            platform_product_id=pp_id,
            period_start=period_start,
            period_end=period_end,
            gross_revenue=Decimal(str(row.get("gross_revenue", 0) or 0)),
            net_revenue=Decimal(str(row.get("net_revenue", 0) or 0)),
            quantity=int(row.get("quantity", 0) or 0),
            cancel_amount=Decimal(str(row.get("cancel_amount", 0) or 0)) or None,
            cancel_quantity=int(row.get("cancel_quantity", 0) or 0) or None,
            refund_amount=Decimal(str(row.get("refund_amount", 0) or 0)) or None,
            refund_count=int(row.get("refund_count", 0) or 0) or None,
            coupon_seller=Decimal(str(row.get("coupon_seller", 0) or 0)) or None,
            coupon_order=Decimal(str(row.get("coupon_order", 0) or 0)) or None,
            visitors=int(row.get("visitors", 0) or 0) or None,
            page_views=int(row.get("page_views", 0) or 0) or None,
            cart_count=int(row.get("cart_count", 0) or 0) or None,
            upload_id=0,  # Will be set after upload_history is saved
        ))

    def _save_order(self, row, pp_id: int):
        self.session.add(Order(
            platform_product_id=pp_id,
            order_date=row["order_date"],
            order_number=str(row["order_number"]),
            quantity=int(row.get("quantity", 0)),
            sale_price=Decimal(str(row.get("sale_price", 0))),
            status=str(row.get("status", "")),
            site=row.get("site"),
            upload_id=0,  # Will be set after upload_history is saved
        ))

    def _save_ad_data(self, row, platform_id: int, pp_id: int | None):
        self.session.add(AdData(
            platform_id=platform_id,
            platform_product_id=pp_id,
            option_id=str(row.get("option_id", "")) or None,
            campaign_name=str(row.get("campaign_name", "")),
            ad_group=row.get("ad_group"),
            keyword=row.get("keyword"),
            ad_type=row.get("ad_type"),
            exposure_area=row.get("exposure_area"),
            spend=Decimal(str(row.get("spend", 0))),
            impressions=int(row.get("impressions", 0)),
            clicks=int(row.get("clicks", 0)),
            direct_conversions=int(row.get("direct_conversions", 0)) or None,
            indirect_conversions=int(row.get("indirect_conversions", 0)) or None,
            direct_revenue=Decimal(str(row.get("direct_revenue", 0) or 0)) or None,
            indirect_revenue=Decimal(str(row.get("indirect_revenue", 0) or 0)) or None,
            attribution_window=row.get("attribution_window"),
            avg_rank=Decimal(str(row.get("avg_rank", 0) or 0)) or None,
            site=row.get("site"),
            ad_date=row.get("ad_date", date.today()),
            match_status="matched" if pp_id else "unmatched",
        ))
```

**Note:** The `upload_id=0` placeholder is a known simplification. In the real flow, upload_history is saved first, then its ID is set on child records. This will be refined when the API endpoint is built (Phase 3). For now the test verifies the core flow.

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_services/test_upload_service.py -v`
Expected: 2 tests PASS

- [ ] **Step 4: Run ALL tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All tests pass (~35+ tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/ backend/tests/test_services/
git commit -m "feat: add upload service — parse, match, and save to DB"
```

---

## Phase 2 완료 기준

- [ ] 7개 채널 어댑터 (네이버 판매/광고, 쿠팡 판매/광고, 쿠팡 카탈로그, 지마켓 주문/광고)
- [ ] 파일 리더 (CSV + Excel + 비밀번호 Excel)
- [ ] 컬럼 매퍼 (매핑 + null 처리 + 날짜 파싱)
- [ ] 4단계 상품 매칭 (정확 → 판매자코드 → 유사 → AI placeholder)
- [ ] 파싱 파이프라인 오케스트레이터
- [ ] 업로드 서비스 (파싱 → 매칭 → DB 저장 통합)
- [ ] 모든 테스트 PASS

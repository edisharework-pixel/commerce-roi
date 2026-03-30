# 커머스 수익분석 프로그램 설계서

## 1. 개요

다중 판매 채널(쿠팡, 네이버 스마트스토어, 지마켓, 옥션, 11번가, 카페24 등)의 판매/광고 데이터를 통합하여 상품별 수익을 분석하고, AI를 활용한 광고 개선안을 제공하는 웹 애플리케이션.

### 사용자
- 팀/회사 내부 직원 (간단한 로그인 인증)

### 데이터 입력 방식
- 각 플랫폼에서 엑셀/CSV 파일 다운로드 후 업로드
- 비밀번호 보호 엑셀 파일은 업로드 시 비밀번호 입력하여 파싱

---

## 2. 기술 스택

| 구분 | 기술 |
|------|------|
| 프론트엔드 | React + Recharts (차트) + Ant Design (UI) |
| 백엔드 | FastAPI + pandas + SQLAlchemy ORM |
| 데이터베이스 | PostgreSQL |
| AI | Claude API (상품명 매칭 보조 + 광고 개선안 피드백) |

### 아키텍처

```
[React 프론트엔드]  <-->  [FastAPI 백엔드]  <-->  [PostgreSQL DB]
                              |
                     [pandas 데이터 처리]
                     [Claude API (매칭 + 광고분석)]
```

---

## 3. 데이터베이스 설계

### 설계 원칙

실제 3개 채널(네이버, 쿠팡, 지마켓/옥션) 데이터 분석 결과:
- **네이버/쿠팡**: 기간 합산 데이터만 제공 (개별 주문 없음) → `sales_summary` 주력
- **지마켓/옥션**: 개별 주문 데이터 제공 (PRD와 가장 호환) → `orders` 사용
- **쿠팡**: 옵션(SKU) 단위 데이터 → `platform_product_options` 필요
- **광고 구조**: 채널별 27~69개 컬럼 → 공통 핵심 필드 + 채널별 확장 JSON 패턴

### 채널별 데이터 구조 요약

| 채널 | 판매 데이터 | 옵션 구조 | 광고→상품 매칭 | 비고 |
|------|-----------|---------|--------------|------|
| 네이버 | 기간 합산 (상품ID) | 없음 | 캠페인명→수동 매핑 | 쿠폰/환불 데이터 있음 |
| 쿠팡 | 기간 합산 (옵션ID) | 있음 (최대 28개) | 옵션ID 자동 (~92%) | 취소 이미 반영된 순매출 |
| 지마켓/옥션 | 개별 주문 | 없음 | 상품번호 자동 (100%) | G+A 한 파일, 판매아이디로 구분 |

### 3.1 사용자

**users**
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| username | VARCHAR | 로그인 ID |
| password_hash | VARCHAR | 비밀번호 해시 |
| role | VARCHAR | 역할 |
| created_at | TIMESTAMP | 생성일 |

### 3.2 플랫폼 & 상품

**platforms**
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| name | VARCHAR | 플랫폼명 (쿠팡, 네이버, 지마켓, 옥션 등) |
| type | VARCHAR | 마켓 / 외부광고 |
| fee_rate | DECIMAL | 기본 수수료율 |
| vat_included | BOOLEAN | 비용 데이터 VAT 포함 여부 |
| site_identifier | VARCHAR (nullable) | 사이트 구분자 (지마켓: "G", 옥션: "A") |
| seller_id | VARCHAR (nullable) | 판매자 ID (지마켓: "itholic", 옥션: "itemholic") |

> **지마켓/옥션 처리**: 하나의 파일에 지마켓+옥션이 혼재. 판매아이디(itholic/itemholic)로 구분하여 각각 별도 platform으로 등록. 마스터상품번호로 G↔A 동일상품 자동 연결.

**products** (기준 상품 — 원가는 여기 한 곳에만 저장)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| name | VARCHAR | 기준 상품명 |
| sku | VARCHAR | 자체 SKU |
| base_cost | DECIMAL | 원가 |
| category | VARCHAR | 카테고리 |

**platform_products** (마켓별 상품 매칭 — 마켓 추가 시 행만 추가)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| product_id | FK → products | 기준 상품 연결 |
| platform_id | FK → platforms | 플랫폼 |
| platform_product_id | VARCHAR | 마켓 상품번호 |
| platform_product_name | VARCHAR | 마켓 상품명 |
| seller_product_code | VARCHAR (nullable) | 판매자관리코드/판매자상품코드 |
| selling_price | DECIMAL (nullable) | 마켓별 판매가 |
| discount_price | DECIMAL (nullable) | 할인가 (네이버) |
| platform_fee_rate | DECIMAL (nullable) | 마켓별 수수료율 |
| shipping_type | VARCHAR (nullable) | free / paid / conditional |
| shipping_fee | DECIMAL (nullable) | 기본 배송비 |
| return_shipping_fee | DECIMAL (nullable) | 반품 배송비 (네이버: 2,500~10,000) |
| exchange_shipping_fee | DECIMAL (nullable) | 교환 배송비 (네이버: 5,000~20,000) |
| sale_status | VARCHAR (nullable) | 판매중 / 품절 / 판매중지 / 판매가능 / 판매불가 |
| site | VARCHAR (nullable) | 지마켓(G) / 옥션(A) 구분 |
| master_product_id | VARCHAR (nullable) | 지마켓 마스터상품번호 (G+A 통합키) |
| matched_by | VARCHAR | 매칭 방법 (auto/ai/manual) |

> **수수료율 사용 우선순위**: 1) platform_products.platform_fee_rate → 2) platforms.fee_rate → 3) 모두 null이면 0% (경고 표시)
>
> 가격 정보가 없는 채널(쿠팡 상품수정 엑셀 등)은 판매 데이터에서 역산(매출÷판매량)하여 보완.

**platform_product_options** (옵션/SKU 단위 — 쿠팡 전용)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_product_id | FK → platform_products | 상위 상품 |
| option_id | VARCHAR | 쿠팡 옵션 ID |
| option_name | VARCHAR | 옵션명 |
| option_values | JSON (nullable) | 옵션 속성 (유형1:값1, 유형2:값2) |
| is_active | BOOLEAN | 활성 여부 |
| **UNIQUE** | | **(platform_product_id, option_id)** |

> 쿠팡은 등록상품ID 1개에 최대 28개 옵션ID. 판매/광고 데이터 모두 옵션ID 단위.
> 네이버/지마켓은 옵션 구분 없이 상품ID = 1행 → 이 테이블 미사용.

### 3.3 판매 데이터 & 정산

**이중 판매 테이블 구조:**
- `sales_summary` — 기간 합산 (네이버, 쿠팡) ← **주력**
- `orders` — 개별 주문 (지마켓/옥션, 향후 11번가 등)

**sales_summary** (기간 합산 — 네이버, 쿠팡 공통)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_product_id | FK → platform_products | 마켓 상품 연결 |
| option_id | FK → platform_product_options (nullable) | 옵션 연결 (쿠팡) |
| period_start | DATE | 집계 시작일 |
| period_end | DATE | 집계 종료일 |
| gross_revenue | DECIMAL | 총매출 (취소/환불 전) |
| net_revenue | DECIMAL | 순매출 (취소/환불 후) |
| quantity | INTEGER | 판매수량 |
| cancel_amount | DECIMAL (nullable) | 취소 금액 (쿠팡) |
| cancel_quantity | INTEGER (nullable) | 취소 수량 (쿠팡) |
| refund_amount | DECIMAL (nullable) | 환불 금액 (네이버) |
| refund_count | INTEGER (nullable) | 환불 건수 (네이버) |
| coupon_seller | DECIMAL (nullable) | 판매자 부담 쿠폰 (네이버) |
| coupon_order | DECIMAL (nullable) | 주문 쿠폰 (네이버) |
| visitors | INTEGER (nullable) | 방문자수 (쿠팡) |
| page_views | INTEGER (nullable) | 조회수 (쿠팡) |
| cart_count | INTEGER (nullable) | 장바구니 (쿠팡) |
| conversion_rate | DECIMAL (nullable) | 구매전환율 (쿠팡) |
| upload_id | FK → upload_history | 업로드 이력 연결 |

> **정합성 검증**: option_id가 있으면, 해당 옵션의 platform_product_id와 sales_summary.platform_product_id가 반드시 일치해야 함.

**orders** (개별 주문 단위 — 지마켓/옥션)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_product_id | FK → platform_products | 마켓 상품 연결 |
| option_id | FK → platform_product_options (nullable) | 옵션 연결 |
| order_date | DATE | 주문일 (결제일) |
| order_number | VARCHAR | 주문번호 (중복 방지) |
| quantity | INTEGER | 수량 |
| sale_price | DECIMAL | 구매금액 |
| shipping_fee | DECIMAL (nullable) | 배송비 |
| platform_fee | DECIMAL (nullable) | 플랫폼 수수료 |
| status | VARCHAR | 송금완료 / 배송완료 / 취소완료 / 환불완료 / 반품완료 / 교환수거완료 |
| site | VARCHAR (nullable) | 지마켓(G) / 옥션(A) 구분 |
| upload_id | FK → upload_history | 업로드 이력 연결 |

**settlements** (마켓별 정산 추적)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_id | FK → platforms | 플랫폼 |
| period_start | DATE | 정산 시작일 |
| period_end | DATE | 정산 종료일 |
| expected_amount | DECIMAL | 예상 정산액 |
| actual_amount | DECIMAL | 실제 정산액 |
| status | VARCHAR | 예정 / 완료 |

### 3.4 비용

**cost_categories** (자유 추가 가능)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| name | VARCHAR | 비용 카테고리명 |
| type | VARCHAR | 변동비 / 마케팅비 / 커스텀 |

기본 마케팅비 카테고리: 인플루언서 비용, 촬영비, 모델비, 물류비, 행사진행비, 체험단 비용

**variable_costs** (상품별 변동비)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| product_id | FK → products | 상품 |
| category_id | FK → cost_categories | 비용 카테고리 |
| amount | DECIMAL | 금액 |
| period_start | DATE | 적용 시작일 |
| period_end | DATE | 적용 종료일 |

**campaigns** (마케팅 캠페인 — 비용 배분을 위한 논리적 그룹)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| name | VARCHAR | 캠페인명 |
| start_date | DATE | 시작일 |
| end_date | DATE | 종료일 |
| allocation_method | VARCHAR | direct / equal / revenue_ratio |

> campaigns는 "마케팅 비용 배분"을 위한 논리적 그룹. 광고 플랫폼의 캠페인(ad_campaign_product_mapping)과는 별개 개념.

**campaign_products** (캠페인-상품 연결)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| campaign_id | FK → campaigns | 캠페인 |
| product_id | FK → products | 상품 |

**marketing_costs** (마케팅비)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| campaign_id | FK → campaigns (nullable) | 캠페인 연결 |
| category_id | FK → cost_categories | 비용 카테고리 |
| product_id | FK → products (nullable) | 상품 직접 연결 시 |
| amount | DECIMAL | 금액 |
| cost_date | DATE | 비용 발생일 |

> **비용 배분 규칙**:
> - product_id가 있으면 → 해당 상품에 100% 직접 배분
> - product_id가 null이고 campaign_id가 있으면 → campaigns.allocation_method에 따라 배분

### 3.5 광고

**공통 핵심 필드 + 채널별 확장** 패턴. 3개 채널의 광고 구조가 전부 다름.

**ad_data** (광고 데이터)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_id | FK → platforms | 광고 플랫폼 |
| platform_product_id | FK → platform_products (nullable) | 상품 매칭 (네이버는 null) |
| option_id | VARCHAR (nullable) | 쿠팡 옵션ID (직접 매칭) |
| campaign_name | VARCHAR | 광고 캠페인명 |
| ad_group | VARCHAR (nullable) | 광고그룹 (네이버/쿠팡) |
| keyword | VARCHAR (nullable) | 키워드 (네이버) |
| ad_type | VARCHAR (nullable) | 파워링크/쇼핑검색/파워컨텐츠/동영상/상품 |
| exposure_area | VARCHAR (nullable) | 검색/비검색/외부/그외영역/먼저둘러보세요 |
| device | VARCHAR (nullable) | PC / 모바일 (네이버) |
| spend | DECIMAL | 광고비 |
| impressions | INTEGER | 노출수 |
| clicks | INTEGER | 클릭수 |
| direct_conversions | INTEGER (nullable) | 직접 전환수 (네이버/쿠팡) |
| indirect_conversions | INTEGER (nullable) | 간접 전환수 (네이버/쿠팡) |
| direct_revenue | DECIMAL (nullable) | 직접 전환 매출 (네이버/쿠팡) |
| indirect_revenue | DECIMAL (nullable) | 간접 전환 매출 (네이버/쿠팡) |
| attribution_window | VARCHAR (nullable) | 귀속기간 1d / 14d (쿠팡) |
| avg_rank | DECIMAL (nullable) | 평균 노출 순위 (네이버/지마켓) |
| site | VARCHAR (nullable) | G / A 구분 (지마켓/옥션) |
| ad_date | DATE | 광고 집행일 |
| match_status | VARCHAR | matched / pending / unmatched |
| extended_metrics | JSON (nullable) | 채널별 확장 지표 |

> **채널별 처리**:
> - **쿠팡**: 동일 행이 attribution_window=1d, 14d 두 행으로 분리 저장
> - **네이버**: platform_product_id=null, 캠페인명으로 매핑
> - **지마켓/옥션**: platform_product_id로 100% 자동 매칭, site로 G/A 구분
>
> **광고 매출 주의**: ad_data의 revenue 필드는 "광고 플랫폼 자체 추적 매출". sales_summary/orders의 매출과 직접 대응하지 않음. 수익 계산에서 차감하는 것은 ad_data.spend(광고비)만 해당.

> extended_metrics 예시:
> - 쿠팡: `{"video_3s_views": 500, "video_25pct": 400, "video_50pct": 300, "video_75pct": 200, "video_100pct": 100, "reach": 5000, "new_customer_revenue": 150000, "new_customer_ratio": 0.35, "new_customer_cost": 2500, "exposure_frequency": 2.3}`
> - 네이버: `{"media_type": "검색", "business_channel": "네이버쇼핑"}`

**ad_campaign_product_mapping** (캠페인명 → 상품 매핑 — 네이버 등 상품번호 없는 광고용)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_id | FK → platforms | 광고 플랫폼 |
| campaign_name | VARCHAR | 광고 캠페인명 |
| product_id | FK → products | 매핑 상품 |
| allocation_method | VARCHAR | single / equal / revenue_ratio |
| created_at | TIMESTAMP | 생성일 |

> **광고 → 상품 매칭 전략**:
>
> | 채널 | 매칭 방법 | 매칭률 |
> |------|-----------|--------|
> | 쿠팡 | 광고 집행 옵션ID → platform_product_options.option_id | ~92% 자동 |
> | 네이버 | 캠페인명 → ad_campaign_product_mapping 수동 매핑 | 수동 100% |
> | 지마켓/옥션 | 광고상품번호 → platform_products.platform_product_id | 100% 자동 |
> | 메타/구글 | 캠페인명 → ad_campaign_product_mapping | 수동 100% |
>
> **배분 방식** (네이버 등 1캠페인 → 다상품):
> - `single`: 매핑 상품이 1개, 100% 배분
> - `equal`: 매핑된 상품에 균등 배분
> - `revenue_ratio`: 해당 기간 내 각 상품 매출 비율로 배분

**ad_analysis_logs** (AI 광고 개선안 저장)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| product_id | FK → products | 상품 |
| period_start | DATE | 분석 시작일 |
| period_end | DATE | 분석 종료일 |
| analysis_result | JSON | 분석 결과 (ROAS, CPC, 전환율 등) |
| suggestions | TEXT | AI 개선안 |
| created_at | TIMESTAMP | 생성일 |

### 3.6 CSV 파싱 템플릿

**platform_csv_templates**
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_id | FK → platforms | 플랫폼 |
| data_type | VARCHAR | order / sales_summary / ad / settlement / product_catalog |
| column_mapping | JSON | 컬럼 매핑 정보 |
| parsing_rules | JSON | 파싱 규칙 |
| file_type | VARCHAR | xlsx / csv |
| notes | TEXT | 비고 |

**등록할 파싱 템플릿 목록 (6건)**:

#### 네이버 광고 (data_type: ad)
```json
// column_mapping
{
  "ad_date": "일별",
  "campaign_name": "캠페인",
  "ad_group": "광고그룹",
  "keyword": "키워드",
  "ad_type": "캠페인유형",
  "spend": "총비용(VAT포함,원)",
  "clicks": "클릭수",
  "impressions": "노출수",
  "device": "PC/모바일 매체",
  "direct_conversions": "직접전환수",
  "indirect_conversions": "간접전환수",
  "direct_revenue": "전환매출액(원)"
}

// parsing_rules
{
  "skip_rows": 1,
  "date_format": "YYYY.MM.DD.",
  "vat_included": true,
  "null_values": ["-"],
  "notes": "첫 행은 제목행, 날짜 끝 마침표 제거, 쇼핑검색 키워드는 - 표시"
}
```

#### 네이버 상품성과 (data_type: sales_summary)
```json
// column_mapping
{
  "product_id": "상품번호",
  "quantity": "결제상품수량",
  "net_revenue": "결제금액",
  "refund_amount": "환불금액",
  "refund_count": "환불수량",
  "coupon_seller": "상품쿠폰합계",
  "coupon_order": "주문쿠폰합계"
}

// parsing_rules
{
  "skip_rows": 0,
  "period_from_filename": true,
  "notes": "기간 합산 데이터. 같은 상품ID에 상품명 변경 이력 가능 — 최신 상품명 우선"
}
```

#### 쿠팡 판매 (data_type: sales_summary)
```json
// column_mapping
{
  "option_id": "옵션 ID",
  "product_id": "등록상품ID",
  "product_name": "상품명",
  "option_name": "옵션명: 옵션값",
  "net_revenue": "매출(원)",
  "gross_revenue": "총 매출(원)",
  "cancel_amount": "총 취소 금액(원)",
  "cancel_quantity": "총 취소된 상품수",
  "quantity": "판매량",
  "visitors": "방문자",
  "page_views": "조회",
  "cart_count": "장바구니"
}

// parsing_rules
{
  "skip_rows": 0,
  "period_from_upload": true,
  "notes": "날짜 컬럼 없음. 업로드 시 사용자가 기간 입력. 옵션ID 단위 데이터"
}
```

#### 쿠팡 광고 (data_type: ad)
```json
// column_mapping
{
  "campaign_name": "캠페인 이름",
  "ad_group": "광고명",
  "spend": "광고비(원)",
  "clicks": "클릭수",
  "impressions": "노출수",
  "exposure_area": "노출 영역",
  "ad_type": "광고 유형",
  "option_id": "광고 집행 옵션 ID"
}

// 귀속기간별 필드 매핑
{
  "attribution_1d": {
    "direct_conversions": "직접주문수(1일)",
    "indirect_conversions": "간접주문수(1일)",
    "direct_revenue": "직접매출(1일)",
    "indirect_revenue": "간접매출(1일)"
  },
  "attribution_14d": {
    "direct_conversions": "직접주문수(14일)",
    "indirect_conversions": "간접주문수(14일)",
    "direct_revenue": "직접매출(14일)",
    "indirect_revenue": "간접매출(14일)"
  }
}

// parsing_rules
{
  "skip_rows": 0,
  "attribution_windows": ["1d", "14d"],
  "split_by_attribution": true,
  "notes": "1일/14일 귀속기간 데이터를 각각 별도 행으로 저장"
}
```

#### 쿠팡 상품 카탈로그 (data_type: product_catalog)
```json
// column_mapping
{
  "product_id": "등록상품ID",
  "product_name": "등록 상품명",
  "brand": "브랜드",
  "category": "카테고리",
  "search_tags": "검색어태그"
}

// parsing_rules
{
  "sheet_name": "Template",
  "header_row": 3,
  "notes": "상품정보 수정요청 엑셀. 가격정보 없음 — 별도 소스 필요"
}
```

#### 지마켓/옥션 주문 (data_type: order)
```json
// column_mapping
{
  "order_date": "결제일",
  "order_number": "주문번호",
  "product_id": "상품번호",
  "product_name": "상품명",
  "quantity": "수량",
  "sale_price": "구매금액",
  "status": "진행상태"
}

// parsing_rules
{
  "site_column": "판매아이디",
  "site_map": {
    "지마켓(itholic)": "G",
    "옥션(itemholic)": "A"
  },
  "notes": "한 파일에 지마켓+옥션 혼재. 판매아이디로 사이트 구분"
}
```

#### 지마켓/옥션 광고 (data_type: ad)
```json
// column_mapping
{
  "site": "사이트",
  "product_id": "광고상품번호",
  "impressions": "노출수",
  "clicks": "클릭수",
  "spend": "총비용",
  "direct_conversions": "구매수",
  "direct_revenue": "구매금액",
  "avg_rank": "평균노출순위",
  "exposure_area": "영역명"
}

// parsing_rules
{
  "site_map": {"G": "지마켓", "A": "옥션"},
  "notes": "사이트 컬럼으로 G/A 구분"
}
```

### 3.7 변경 이벤트 & 데이터 누적

**event_types** (이벤트 유형 — 기본 제공 + 사용자 추가)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| name | VARCHAR | 이벤트 유형명 |
| is_default | BOOLEAN | 기본 제공 여부 |
| created_by | FK → users | 생성자 |

기본 이벤트 유형: 쿠폰 적용, 목표 ROAS 변경, 광고 예산 변경, 판매가 수정

사용자 추가 예시: 상세페이지 변경, 키워드 변경, 프로모션 참여, 리뷰 이벤트 등

**change_events** (변경 이벤트 기록)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| event_type_id | FK → event_types | 이벤트 유형 |
| product_id | FK → products (nullable) | 특정 상품 (null이면 전체) |
| platform_id | FK → platforms (nullable) | 특정 플랫폼 (null이면 전체) |
| description | TEXT | 상세 설명 |
| change_details | JSON | 변경 내용 구조화 |
| event_date | DATE | 변경일 |
| created_at | TIMESTAMP | 기록일 |

> change_details 예시:
> - 판매가 수정: `{"field": "selling_price", "before": 59900, "after": 54900}`
> - 광고 예산: `{"field": "daily_budget", "before": 50000, "after": 100000}`

**upload_history** (업로드 이력)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_id | FK → platforms | 플랫폼 |
| data_type | VARCHAR | order / sales_summary / ad / settlement / product_catalog |
| file_name | VARCHAR | 파일명 |
| record_count | INTEGER | 처리 건수 |
| matched_count | INTEGER | 매칭 성공 건수 |
| unmatched_count | INTEGER | 매칭 실패 건수 |
| period_start | DATE | 데이터 시작일 |
| period_end | DATE | 데이터 종료일 |
| uploaded_at | TIMESTAMP | 업로드 시각 |

### 3.8 상품 매칭 로그

**matching_logs**
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_product_name | VARCHAR | 마켓 상품명 (원본) |
| matched_product_id | FK → products (nullable) | 매칭된 기준 상품 (실패 시 null) |
| method | VARCHAR | auto / ai / manual / failed |
| confidence | DECIMAL | 매칭 신뢰도 (0~100) |
| created_at | TIMESTAMP | 매칭 시각 |

### 3.9 DB 뷰 (조회 편의)

**v_product_effective_costs** (상품/옵션별 실효 원가·판매가·수수료 통합 뷰)

```sql
CREATE VIEW v_product_effective_costs AS
SELECT
  pp.id AS platform_product_id,
  ppo.id AS option_id,
  pp.platform_id,
  pp.product_id,
  COALESCE(pp.selling_price) AS effective_selling_price,
  p.base_cost AS effective_base_cost,
  COALESCE(pp.platform_fee_rate, plt.fee_rate, 0) AS effective_fee_rate,
  ppo.option_name
FROM platform_products pp
LEFT JOIN platform_product_options ppo ON pp.id = ppo.platform_product_id
JOIN products p ON pp.product_id = p.id
JOIN platforms plt ON pp.platform_id = plt.id;
```

---

## 4. 상품 매칭 로직

### 4.1 CSV 업로드 → 매칭 → 저장 전체 흐름

```
1. 채널별 CSV 업로드
   ↓
2. 파싱 (column_mapping + parsing_rules 적용)
   - 지마켓/옥션: 판매아이디 컬럼으로 G/A 분리
   ↓
3. platform_product 매칭 (아래 4단계)
   - 성공: 기존 product에 연결
   - 실패: platform_product 임시 생성 (match_status='unmatched')
   ↓
4. 옵션 매칭 (쿠팡)
   - platform_product_options 확인, 없으면 행 생성
   ↓
5. sales_summary / orders / ad_data 저장
   ↓
6. upload_history 기록 (matched_count / unmatched_count)
   ↓
7. 미매칭 항목 대시보드에 표시 → 수동 확인 요청
```

### 4.2 판매 데이터 상품 매칭 — 자동 매칭 4단계

```
1단계: 정확 매칭
  마켓 상품번호/옵션ID가 이미 등록되어 있으면 즉시 매칭
        ↓ 실패
2단계: 판매자상품코드 매칭
  seller_product_code로 크로스채널 매칭 시도
        ↓ 실패
3단계: 유사 매칭
  상품명 키워드 토큰화 + 유사도 점수 비교
        ↓ 실패 (confidence < 80%)
4단계: AI 매칭
  Claude API로 상품명 비교 요청 → 매칭 결과 + confidence 반환
        ↓ 실패 (confidence < 60%)
수동 매칭
  match_status='unmatched'로 저장, 대시보드에 매칭 대기 목록 표시
```

- 모든 매칭 결과는 matching_logs에 기록
- 최초 1회 매칭 후 platform_products에 저장 → 이후 자동 처리

### 4.3 광고 → 상품 매칭 (채널별)

| 채널 | 매칭 방법 | 매칭률 |
|------|-----------|--------|
| 쿠팡 | 광고 집행 옵션ID → platform_product_options.option_id | ~92% 자동 |
| 네이버 | 캠페인명 → ad_campaign_product_mapping 수동 매핑 | 수동 100% |
| 지마켓/옥션 | 광고상품번호 → platform_products.platform_product_id | 100% 자동 (212/212) |
| 메타/구글 | 캠페인명 → ad_campaign_product_mapping | 수동 100% |

> 지마켓은 3개 채널 중 PRD와 가장 호환이 좋음. 개별 주문 + 광고 100% 자동 매칭.

### 4.4 크로스채널 상품 매칭

동일 상품이 여러 채널에 다른 이름/코드로 등록된 경우:
- 지마켓 마스터상품번호로 G↔A 동일상품 자동 연결
- 지마켓↔네이버: 판매자코드 교집합 45건 자동 매칭
- 나머지: 키워드+가격 유사도 매칭 → AI 보조 → 수동 확인

---

## 5. 수익 계산

### 채널별 수익 계산 플러그인 패턴

채널마다 데이터 구조와 계산 방식이 다르므로, 채널별 수익 계산 로직을 플러그인으로 분리.

### 5.1 네이버 수익 계산

```
순이익 = (결제금액 - 환불금액)
       - 원가 × (결제상품수량 - 환불수량)
       - 결제금액 × 수수료율
       - 쿠폰합계 (판매자 부담분: coupon_seller + coupon_order)
       - 환불건수 × 반품배송비
       - 광고비 (캠페인→상품 배분)
       - 마케팅비
       - 커스텀비용
```

데이터 출처:
- 결제금액/환불: sales_summary.net_revenue, refund_amount, refund_count
- 원가: products.base_cost
- 수수료율: v_product_effective_costs.effective_fee_rate
- 쿠폰: sales_summary.coupon_seller + coupon_order
- 반품배송비: platform_products.return_shipping_fee × refund_count
- 광고비: ad_data.spend (ad_campaign_product_mapping으로 배분)

### 5.2 쿠팡 수익 계산

```
순이익 = 매출(원) (= net_revenue, 이미 취소 반영된 순매출)
       - 원가 × 판매량
       - 매출 × 수수료율
       - 광고비 (옵션ID 자동매칭)
       - 마케팅비
       - 커스텀비용
```

> 쿠팡 매출(원)은 이미 취소가 반영된 순매출. 별도 환불 차감 불필요.
>
> **배송비/쿠폰 데이터 보완 전략**:
> 1. 1단계 (현재): Seller Insights 기반 — 순매출, 판매량, 방문자, 전환율 등
> 2. 2단계 (향후): 정산 데이터 업로드 시 배송비/쿠폰 보완

### 5.3 지마켓/옥션 수익 계산

```
순이익 = Σ(정상주문 구매금액)
       - Σ(취소/환불/반품 구매금액)
       - 원가 × 정상수량
       - 정상매출 × 판매이용료 (9~13%)
       - 광고비 (상품번호 직접 매칭)
       - 마케팅비
       - 커스텀비용
```

> 주문 상태별 분류: status가 '송금완료'/'배송완료' = 정상, '취소완료'/'환불완료'/'반품완료' = 차감

### 5.4 공통 비용 항목

| 항목 | 출처 |
|------|------|
| 광고비 | ad_data.spend (직접매칭 + 캠페인매핑 배분) |
| 마케팅비 (직접) | marketing_costs에서 product_id 직접 연결 |
| 마케팅비 (캠페인 배분) | campaign 기간 내 상품 매출 비율 / 균등 배분 |
| 커스텀 비용 | variable_costs에서 해당 상품 + 기간 합산 |

### 5.5 리포트

- 상품별 순이익 / 수익률
- 플랫폼별 비교 (같은 상품의 채널별 수익 비교)
- 옵션별 수익 분석 (쿠팡)
- 기간별 추이 (일/주/월/자유기간)
- 문제 상품 알림 (수익률 마이너스 또는 급락)
- 미매칭 데이터 현황 (미매칭 광고비, 미매칭 판매건 합계)

---

## 6. AI 광고 분석 & 개선안

### 분석 지표

| 항목 | 내용 |
|------|------|
| 광고 효율 | ROAS (광고비 대비 매출), CPC (클릭당 비용), 전환율 |
| 귀속기간 비교 | 쿠팡 1일 vs 14일 귀속 ROAS 차이 분석 |
| 직접/간접 전환 | 직접 전환 비중, 간접 전환 기여도 |
| 광고 유형별 | 동영상 vs 상품광고, 파워링크 vs 쇼핑검색 성과 비교 |
| 기간 비교 | 전월 대비, 전주 대비 변화 추이 |
| 플랫폼 비교 | 같은 상품의 플랫폼별 광고 성과 비교 |
| 문제 감지 | ROAS 급락, CPC 급등, 전환율 하락, 아이템위너 비율 하락 자동 감지 |

### AI 피드백 흐름

```
광고 데이터 수집 → pandas로 지표 계산 → 이상치/문제점 감지
                                              ↓
                                   Claude API에 데이터 + 컨텍스트 전달
                                              ↓
                              개선안 생성 (예산 조정, 키워드 제안, 채널 전환 등)
                                              ↓
                              ad_analysis_logs에 저장 + 대시보드에 표시
```

---

## 7. 변경 이벤트 & 성과 비교 UI

### 이벤트 리스트 뷰

- 전체 변경 이벤트를 테이블로 표시
- 필터: 상품별, 플랫폼별, 이벤트유형별, 기간별
- 정렬: 날짜순, 효과순
- 각 이벤트에 변경 후 효과 요약 표시

### 이벤트 상세 — Before/After 비교

이벤트 클릭 시 상세 화면:
- 변경 전/후 기간별 성과 비교 (매출, 순이익, 판매수량, 광고비, ROAS, 전환율)
- 비교 기간 선택: 변경 후 7일 / 14일 / 30일 / 자유기간
- 추이 차트 연동

### 기간별 추이 차트

- 라인 차트에 변경 이벤트를 수직선 마커로 표시
- 마커 클릭 시 Before/After 비교 패널 팝업
- 여러 변경 이벤트를 겹쳐서 어떤 변경이 효과적이었는지 비교 가능

---

## 8. 데이터 누적 관리

- 모든 데이터는 삭제하지 않고 누적 저장
- 업로드 시 기존 데이터와 병합:
  - orders: 같은 플랫폼 + 같은 주문번호 = 중복 스킵 (상태 변경 시 업데이트)
  - sales_summary: 같은 플랫폼 + 같은 상품(옵션) + 같은 기간 = 덮어쓰기 (최신 데이터 우선)
  - ad_data: 같은 플랫폼 + 같은 캠페인 + 같은 날짜 + 같은 키워드 + 같은 귀속기간 = 덮어쓰기
- 과거 데이터 수정 시 원본 보존 + 수정 이력 기록
- 업로드 이력 관리 (upload_history — 매칭 성공/실패 건수 포함)

---

## 9. 인증

- 간단한 로그인 (아이디/비밀번호)
- JWT 토큰 기반 인증
- 세션 만료 후 재로그인

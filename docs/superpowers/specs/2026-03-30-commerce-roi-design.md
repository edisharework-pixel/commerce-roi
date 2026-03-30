# 커머스 수익분석 프로그램 설계서

## 1. 개요

다중 판매 채널(쿠팡, 네이버 스마트스토어, 지마켓, 11번가, 카페24 등)의 판매/광고 데이터를 통합하여 상품별 수익을 분석하고, AI를 활용한 광고 개선안을 제공하는 웹 애플리케이션.

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

실제 채널 데이터 분석 결과, 주요 채널(쿠팡, 네이버)은 모두 **기간 합산 데이터**를 제공하며, 개별 주문 단위 데이터가 아님. 또한 쿠팡은 **옵션(SKU) 단위**로 데이터를 제공하므로 상품-옵션 2계층 구조가 필요. 광고 데이터는 채널별로 컬럼 수가 27~69개로 크게 다르므로 **공통 핵심 필드 + 채널별 확장 JSON** 패턴을 채택.

### 채널별 옵션 구조

| 채널 | 옵션 구조 | 데이터 단위 | 비고 |
|------|---------|-----------|------|
| 쿠팡 | 있음 (최대 28개) | 옵션ID | 등록상품ID → 옵션ID 2계층 |
| 네이버 | 없음 | 상품ID | 상품ID = 1행 |
| 11번가 | 미정 (향후 확인) | 미정 | |
| 지마켓 | 미정 (향후 확인) | 미정 | |
| 카페24 | 미정 (향후 확인) | 미정 | |

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
| name | VARCHAR | 플랫폼명 (쿠팡, 네이버 등) |
| type | VARCHAR | 마켓 / 외부광고 |
| fee_rate | DECIMAL | 기본 수수료율 |
| vat_included | BOOLEAN | 비용 데이터 VAT 포함 여부 |

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
| platform_product_id | VARCHAR | 마켓 상품번호 (쿠팡: 등록상품ID, 네이버: 상품번호) |
| platform_product_name | VARCHAR | 마켓 상품명 |
| seller_product_code | VARCHAR | 판매자상품코드 (크로스채널 매칭키) |
| selling_price | DECIMAL (nullable) | 마켓별 판매가 (수동 입력 또는 역산 보완) |
| discount_price | DECIMAL (nullable) | 할인가 |
| platform_fee_rate | DECIMAL (nullable) | 마켓별 수수료율 |
| shipping_type | VARCHAR (nullable) | free / paid / conditional |
| shipping_fee | DECIMAL (nullable) | 기본 배송비 |
| return_shipping_fee | DECIMAL (nullable) | 반품 배송비 |
| exchange_shipping_fee | DECIMAL (nullable) | 교환 배송비 |
| sale_status | VARCHAR (nullable) | selling / soldout / stopped / ended |
| matched_by | VARCHAR | 매칭 방법 (auto/ai/manual) |

> 가격 정보가 없는 채널(쿠팡 상품수정 엑셀 등)은 판매 데이터에서 역산(매출÷판매량)하여 평균 판매가를 자동 계산하거나, 별도 가격 파일 업로드로 보완.

> **수수료율 사용 우선순위**: 수익 계산 시 1) platform_products.platform_fee_rate 사용 → 2) null이면 platforms.fee_rate 사용 → 3) 모두 null이면 0% (경고 표시)

**platform_product_options** (옵션/SKU 단위 — 쿠팡 등 옵션 계층이 있는 채널용)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_product_id | FK → platform_products | 상위 상품 |
| option_id | VARCHAR | 마켓 옵션ID (쿠팡: 옵션ID) |
| option_name | VARCHAR | 옵션명 |
| option_values | JSON (nullable) | 옵션 속성 (색상, 사이즈 등) |
| selling_price | DECIMAL (nullable) | 옵션별 판매가 |
| base_cost | DECIMAL (nullable) | 옵션별 원가 |
| **UNIQUE** | | **(platform_product_id, option_id)** |

> **원가 조회 우선순위**: COALESCE(platform_product_options.base_cost, products.base_cost)
> **판매가 조회 우선순위**: COALESCE(platform_product_options.selling_price, platform_products.selling_price, sales_summary 역산값)

> 네이버는 옵션 구분 없이 상품ID = 1행. 쿠팡은 등록상품ID 1개에 최대 28개 옵션ID.
> 판매/광고 데이터 적재 시 옵션이 있으면 option 단위, 없으면 platform_product 단위로 저장.

### 3.3 판매 데이터 & 정산

**이중 판매 테이블 구조:**
- `orders` — 개별 주문 단위 (11번가, 지마켓 등 건별 데이터 제공 채널)
- `sales_summary` — 기간 합산 단위 (네이버, 쿠팡 등 합산 데이터 채널) ← **주력**

**orders** (개별 주문 단위 — 11번가, 지마켓 등)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_product_id | FK → platform_products | 마켓 상품 연결 |
| option_id | FK → platform_product_options (nullable) | 옵션 연결 |
| order_date | DATE | 주문일 |
| order_number | VARCHAR | 주문번호 (중복 방지) |
| quantity | INTEGER | 주문 수량 |
| sale_price | DECIMAL | 판매가 |
| shipping_fee | DECIMAL | 배송비 |
| platform_fee | DECIMAL | 플랫폼 수수료 |
| cancelled_amount | DECIMAL (nullable) | 취소 금액 (null이면 취소 없음) |
| cancelled_quantity | INTEGER (nullable) | 취소 수량 |
| refund_amount | DECIMAL (nullable) | 환불 금액 |
| order_status | VARCHAR | completed / cancelled / refunded / partial_cancel |
| last_updated | TIMESTAMP | 마지막 상태 변경일 |

> orders 테이블의 option_id가 있으면, 해당 옵션의 platform_product_id와 orders.platform_product_id가 일치해야 함 (정합성 검증).

**sales_summary** (기간 합산 — 네이버, 쿠팡 공통)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_product_id | FK → platform_products | 마켓 상품 연결 |
| option_id | FK → platform_product_options (nullable) | 옵션 연결 (쿠팡: 옵션 단위) |
| period_start | DATE | 집계 시작일 |
| period_end | DATE | 집계 종료일 |
| gross_revenue | DECIMAL | 총매출 (취소/환불 전) |
| net_revenue | DECIMAL | 순매출 (취소/환불 후) |
| actual_unit_price | DECIMAL (nullable) | 실제 평균 판매단가 (net_revenue / quantity 역산) |
| quantity | INTEGER | 판매수량 |
| cancel_amount | DECIMAL | 취소 금액 |
| cancel_quantity | INTEGER | 취소 수량 |
| refund_amount | DECIMAL | 환불 금액 |
| refund_count | INTEGER | 환불 건수 |
| coupon_seller | DECIMAL (nullable) | 판매자 부담 쿠폰 (네이버) |
| coupon_order | DECIMAL (nullable) | 주문 쿠폰 (네이버) |
| total_shipping_fee | DECIMAL (nullable) | 기간 총 배송비 (채널 제공 시) |
| total_return_shipping_fee | DECIMAL (nullable) | 기간 총 반품배송비 (채널 제공 시) |
| match_status | VARCHAR | matched / pending / unmatched |
| extended_metrics | JSON (nullable) | 채널별 확장 지표 |

> **정합성 검증**: option_id가 있으면, 해당 옵션의 platform_product_id와 sales_summary.platform_product_id가 반드시 일치해야 함.

> extended_metrics 예시:
> - 쿠팡: `{"visitors": 1234, "views": 5678, "cart_adds": 89, "conversion_rate": 3.2, "item_winner_rate": 85.5}`
> - 네이버: `{"review_count": 45, "review_score": 4.8}`

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
| campaign_id | FK → campaigns (nullable) | 캠페인 연결 (캠페인 배분 시) |
| category_id | FK → cost_categories | 비용 카테고리 |
| product_id | FK → products (nullable) | 상품 직접 연결 시 |
| amount | DECIMAL | 금액 |
| cost_date | DATE | 비용 발생일 |

> **비용 배분 규칙**:
> - product_id가 있으면 → 해당 상품에 100% 직접 배분 (campaigns.allocation_method 무관)
> - product_id가 null이고 campaign_id가 있으면 → campaigns.allocation_method에 따라 배분:
>   - `direct`: campaign_products에 등록된 상품에 직접 배분 (이 경우 product_id를 채워야 함)
>   - `equal`: campaign_products에 등록된 상품에 균등 배분
>   - `revenue_ratio`: campaign 기간(start_date~end_date) 내 각 상품의 매출 비율로 배분

### 3.5 광고

**공통 핵심 필드 + 채널별 확장 JSON 패턴** 채택. 채널별 컬럼 수가 27~69개로 크게 달라 단일 테이블로 커버 불가.

**ad_data** (광고 데이터 — 공통 핵심 필드)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_id | FK → platforms | 광고 플랫폼 |
| platform_product_id | FK → platform_products (nullable) | 상품 직접 매칭 |
| option_id | FK → platform_product_options (nullable) | 옵션 직접 매칭 (쿠팡) |
| campaign_name | VARCHAR | 광고 캠페인명 |
| ad_group | VARCHAR (nullable) | 광고그룹 |
| keyword | VARCHAR (nullable) | 키워드 (null이면 쇼핑검색 등) |
| ad_type | VARCHAR (nullable) | 광고유형 (파워링크/쇼핑검색/동영상/상품 등) |
| exposure_area | VARCHAR (nullable) | 노출영역 (검색/비검색/외부) |
| device | VARCHAR (nullable) | PC / 모바일 |
| spend | DECIMAL | 광고비 |
| impressions | INTEGER | 노출수 |
| clicks | INTEGER | 클릭수 |
| direct_conversions | INTEGER (nullable) | 직접 전환수 (미제공 채널은 null) |
| indirect_conversions | INTEGER (nullable) | 간접 전환수 (미제공 채널은 null) |
| direct_revenue | DECIMAL (nullable) | 직접 전환 매출 |
| indirect_revenue | DECIMAL (nullable) | 간접 전환 매출 |
| attribution_window | VARCHAR (nullable) | 귀속기간 (1d / 14d — 쿠팡) |
| ad_date | DATE | 광고 집행일 |
| match_status | VARCHAR | matched / pending / unmatched |
| match_confidence | DECIMAL (nullable) | 매칭 신뢰도 (0~100) |
| extended_metrics | JSON (nullable) | 채널별 확장 지표 |

> **전환수 필드 처리**: 직접/간접 전환 분리를 지원하지 않는 채널은 null. 단일 전환수만 제공하는 경우 direct_conversions에 저장.
>
> **쿠팡 귀속기간 처리**: 동일 광고 행이 attribution_window=1d, 14d 두 행으로 분리 저장. 분석 시 attribution_window 필터링.
>
> **광고 매출과 판매 매출의 관계**: ad_data.direct_revenue/indirect_revenue는 "광고 플랫폼 자체 추적 매출"로, sales_summary.net_revenue와 직접 대응하지 않음 (속성 기준이 다를 수 있음). 수익 계산에서 차감하는 것은 ad_data.spend(광고비)이며, 매출은 sales_summary에서 조회.

> extended_metrics 예시:
> - 쿠팡: `{"video_3s_views": 500, "video_25pct": 400, "video_50pct": 300, "video_75pct": 200, "video_100pct": 100, "reach": 5000, "new_customer_revenue": 150000, "new_customer_ratio": 0.35, "new_customer_cost": 2500, "exposure_frequency": 2.3}`
> - 네이버: `{"avg_rank": 3.2, "media_type": "검색", "business_channel": "네이버쇼핑"}`

**ad_campaign_mappings** (광고 캠페인 매핑 — 광고에 상품번호 없는 경우)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_id | FK → platforms | 광고 플랫폼 |
| campaign_name_pattern | VARCHAR | 캠페인명 패턴 (예: "◆바디트리머%") |
| pattern_type | VARCHAR | exact / like / regex |
| allocation_method | VARCHAR | single / equal / revenue_ratio |
| effective_start_date | DATE (nullable) | 유효 시작일 |
| effective_end_date | DATE (nullable) | 유효 종료일 |
| **UNIQUE** | | **(platform_id, campaign_name_pattern)** |

**ad_campaign_mapping_products** (캠페인 매핑-상품 연결)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| mapping_id | FK → ad_campaign_mappings | 캠페인 매핑 |
| product_id | FK → products | 매핑 상품 |
| **UNIQUE** | | **(mapping_id, product_id)** |

> **광고 캠페인 매핑과 마케팅 캠페인의 차이**:
> - `ad_campaign_mappings`: 광고 플랫폼의 캠페인명 → 상품 매핑 (광고비 → 상품 배분용)
> - `campaigns`: 마케팅 비용 배분을 위한 논리적 그룹 (인플루언서비, 촬영비 등 배분용)
>
> **광고 → 상품 매칭 방법 (채널별)**:
> - **쿠팡**: 광고 집행 옵션ID → platform_product_options.option_id 자동 매칭 (~92% 매칭률)
> - **네이버**: 상품번호 없음 → 캠페인명에서 상품 추론 → ad_campaign_mappings으로 수동 매핑
> - **메타/구글**: 캠페인명 기반 매핑
>
> **패턴 매칭 쿼리**:
> ```sql
> -- pattern_type에 따라:
> WHERE (pattern_type = 'exact' AND campaign_name = campaign_name_pattern)
>    OR (pattern_type = 'like'  AND campaign_name LIKE campaign_name_pattern)
>    OR (pattern_type = 'regex' AND campaign_name ~ campaign_name_pattern)
> ```
>
> **광고비 배분 계산**:
> - `single`: 매핑된 상품이 1개, 100% 배분
> - `equal`: 매핑된 상품에 균등 배분
> - `revenue_ratio`: effective_start_date~effective_end_date 기간 내 각 상품 매출 비율로 배분

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
| data_type | VARCHAR | order / sales_summary / ad / settlement / product_catalog / product_pricing |
| column_mapping | JSON | 컬럼 매핑 정보 |
| parsing_rules | JSON | 파싱 규칙 |
| file_type | VARCHAR | xlsx / csv |
| notes | TEXT | 비고 |

column_mapping 예시:
```json
// 쿠팡 판매 (data_type: sales_summary)
{
  "option_id": "옵션 ID",
  "product_id": "등록상품 ID",
  "product_name": "노출상품명",
  "option_name": "옵션명: 옵션값",
  "net_revenue": "매출(원)",
  "gross_revenue": "총 매출(원)",
  "cancel_amount": "총 취소 금액(원)",
  "quantity": "판매량(개)"
}

// 쿠팡 판매 extended_metrics 매핑
{
  "extended": {
    "visitors": "방문자(명)",
    "views": "조회수(건)",
    "cart_adds": "장바구니(건)",
    "conversion_rate": "구매전환율(%)",
    "item_winner_rate": "아이템위너 비율(%)"
  }
}

// 네이버 상품성과 (data_type: sales_summary)
{
  "product_id": "상품번호",
  "quantity": "결제상품수량",
  "net_revenue": "결제금액",
  "refund_amount": "환불금액",
  "refund_count": "환불수량",
  "coupon_seller": "상품쿠폰합계",
  "coupon_order": "주문쿠폰합계"
}

// 네이버 광고 (data_type: ad)
{
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
  "direct_revenue": "전환매출액(원)"
}

// 쿠팡 광고 (data_type: ad) — 69컬럼 중 핵심
{
  "campaign_name": "캠페인명",
  "ad_type": "광고유형",
  "exposure_area": "노출영역",
  "option_id": "광고집행 옵션ID",
  "spend": "광고비(원)",
  "impressions": "노출수",
  "clicks": "클릭수"
}

// 쿠팡 광고 귀속기간별 필드 매핑
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

// 쿠팡 광고 extended_metrics 매핑
{
  "extended": {
    "video_3s_views": "3초 조회수",
    "video_25pct": "25% 재생",
    "video_50pct": "50% 재생",
    "video_75pct": "75% 재생",
    "video_100pct": "100% 재생",
    "reach": "도달수",
    "new_customer_revenue": "신규고객 매출",
    "new_customer_ratio": "신규고객 비율",
    "new_customer_cost": "신규고객 비용",
    "exposure_frequency": "노출빈도"
  }
}

// 쿠팡 상품 카탈로그 (data_type: product_catalog)
{
  "product_id": "등록상품ID",
  "product_name": "등록 상품명",
  "brand": "브랜드",
  "category": "카테고리",
  "search_tags": "검색어태그"
}

// 메타 광고 (data_type: ad)
{
  "ad_date": "Date",
  "campaign_name": "Campaign Name",
  "spend": "Amount Spent",
  "clicks": "Link Clicks",
  "impressions": "Impressions"
}
```

parsing_rules 예시:
```json
// 네이버 광고
{
  "skip_rows": 1,
  "date_format": "YYYY.MM.DD.",
  "vat_included": true,
  "null_values": ["-"],
  "notes": "첫 행은 제목행, 날짜 끝 마침표 제거, 쇼핑검색 키워드는 - 표시"
}

// 네이버 상품성과
{
  "skip_rows": 0,
  "date_format": null,
  "period_from_filename": true,
  "notes": "기간 합산 데이터. 같은 상품ID에 상품명 변경 이력 가능 — 최신 상품명 우선"
}

// 쿠팡 판매 (Seller Insights)
{
  "skip_rows": 0,
  "date_format": null,
  "period_from_upload": true,
  "notes": "날짜 컬럼 없음. 업로드 시 사용자가 기간 입력. 옵션ID 단위 데이터"
}

// 쿠팡 상품 카탈로그
{
  "sheet_name": "Template",
  "header_row": 3,
  "notes": "상품정보 수정요청 엑셀. 가격정보 없음 — 메타데이터 전용"
}

// 쿠팡 광고
{
  "skip_rows": 0,
  "attribution_windows": ["1d", "14d"],
  "split_by_attribution": true,
  "notes": "1일/14일 귀속기간 데이터를 각각 별도 행으로 저장"
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
| change_details | JSON | 변경 내용 구조화 저장 |
| event_date | DATE | 변경일 |
| created_at | TIMESTAMP | 기록일 |

> change_details 예시:
> - 판매가 수정: `{"field": "selling_price", "before": 59900, "after": 54900, "currency": "KRW"}`
> - 쿠폰 적용: `{"field": "coupon", "type": "10% 할인쿠폰", "before": null, "after": "active"}`
> - 광고 예산: `{"field": "daily_budget", "before": 50000, "after": 100000, "currency": "KRW"}`

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

**v_product_effective_costs** (상품/옵션별 실효 원가·판매가 통합 뷰)

```sql
CREATE VIEW v_product_effective_costs AS
SELECT
  pp.id AS platform_product_id,
  ppo.id AS option_id,
  pp.platform_id,
  pp.product_id,
  COALESCE(ppo.selling_price, pp.selling_price) AS effective_selling_price,
  COALESCE(ppo.base_cost, p.base_cost) AS effective_base_cost,
  COALESCE(pp.platform_fee_rate, plt.fee_rate, 0) AS effective_fee_rate,
  ppo.option_name
FROM platform_products pp
LEFT JOIN platform_product_options ppo ON pp.id = ppo.platform_product_id
JOIN products p ON pp.product_id = p.id
JOIN platforms plt ON pp.platform_id = plt.id;
```

> 수익 계산, 리포트 등에서 이 뷰를 사용하여 계층적 가격/원가 참조 복잡도를 숨김.

---

## 4. 상품 매칭 로직

### 4.1 CSV 업로드 → 매칭 → 저장 전체 흐름

```
1. 채널별 CSV 업로드
   ↓
2. 파싱 (column_mapping + parsing_rules 적용)
   ↓
3. platform_product 매칭 (아래 4단계)
   - 성공: 기존 product에 연결
   - 실패: platform_product 임시 생성 (match_status='unmatched')
   ↓
4. 옵션 매칭 (쿠팡 등)
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
  마켓 상품번호/옵션ID가 platform_products 또는 platform_product_options에 이미 있으면 즉시 매칭
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

| 채널 | 매칭 방법 | 예상 매칭률 |
|------|-----------|------------|
| 쿠팡 | 광고 집행 옵션ID → platform_product_options.option_id 자동 매칭 | ~92% |
| 네이버 | 캠페인명에서 상품 추론 → ad_campaign_mappings으로 수동 매핑 | 수동 100% |
| 메타/구글 | 캠페인명 패턴 → ad_campaign_mappings | 수동 100% |

> 쿠팡 광고의 랜딩페이지ID와 등록상품ID는 체계가 달라 직접 매칭 불가. 옵션ID로 매칭.
> 매칭 실패한 광고는 match_status='unmatched'로 저장, 대시보드에서 미매칭 광고비 합계 추적.

### 4.4 크로스채널 상품 매칭

동일 상품이 여러 채널에 다른 이름/코드로 등록된 경우:
- 공통 브랜드명 기반 후보 추출 (예: 쿠팡 33개 브랜드 중 네이버와 공통 18개)
- 상품명 키워드 유사도 비교
- AI 매칭 보조
- 최종 확인은 수동 (판매자상품코드/SKU 체계가 채널별로 다름)

---

## 5. 수익 계산

### 채널별 수익 계산 플러그인 패턴

채널마다 데이터 구조와 계산 방식이 다르므로, 채널별 수익 계산 로직을 플러그인으로 분리.

### 5.1 수익 계산 전체 흐름

```
1. 판매 데이터 조회 (sales_summary 또는 orders)
   ↓
2. 원가 조회 (v_product_effective_costs 뷰 사용)
   ↓
3. 수수료 계산 (effective_fee_rate 사용)
   ↓
4. 광고비 조회
   - 직접 매칭분: ad_data.platform_product_id / option_id로 합산
   - 캠페인 매핑분: ad_campaign_mappings → allocation_method에 따라 배분
   ↓
5. 마케팅비 조회
   - 직접분: marketing_costs.product_id 직접 연결
   - 배분분: campaigns.allocation_method에 따라 배분
   ↓
6. 커스텀 비용 조회 (variable_costs)
   ↓
7. 최종 순이익 계산

주의: 수익은 조회 시점에 동적 계산. 데이터 변경 시 과거 수치도 변함.
```

### 5.2 네이버 수익 계산

```
순이익 = net_revenue
       - 쿠폰부담금 (coupon_seller + coupon_order)
       - 원가 × (quantity - refund_count)
       - 플랫폼수수료 (net_revenue × effective_fee_rate)
       - 환불배송비:
           total_return_shipping_fee (채널 제공 시)
           또는 return_shipping_fee × refund_count (기본값 역산)
       - 광고비 (캠페인 매핑 → 배분)
       - 마케팅비
       - 커스텀비용
```

### 5.3 쿠팡 수익 계산

```
순이익 = net_revenue (= 매출(원), 이미 취소 반영된 순매출)
       - 원가 × quantity (판매량)
       - 플랫폼수수료 (net_revenue × effective_fee_rate)
       - 광고비 (옵션ID 자동매칭)
       - 마케팅비
       - 커스텀비용
```

> 쿠팡 매출(원)은 이미 취소가 반영된 순매출. 별도 환불 차감 불필요.
>
> **쿠팡 배송비/쿠폰 데이터 보완 전략**:
> 1. 1단계 (현재): Seller Insights 기반 — 광고비, 판매량, 순매출, 확장지표
> 2. 2단계 (향후): 정산 데이터 업로드 — 배송비, 쿠폰, 추가 수수료 보완
>    - 정산 데이터에서 확인된 배송비/쿠폰은 sales_summary.extended_metrics에 저장:
>      `{"shipping_fee_from_settlement": 150000, "coupon_from_settlement": 50000}`
> 3. 3단계: 정산 보완 데이터가 있으면 수익 계산에 반영

### 5.4 공통 비용 항목

| 항목 | 출처 |
|------|------|
| 광고비 | ad_data (직접매칭 + 캠페인매핑 배분) |
| 마케팅비 (직접) | marketing_costs에서 product_id 직접 연결 |
| 마케팅비 (캠페인 배분) | campaign 기간 내 상품 매출 비율 / 균등 배분 |
| 커스텀 비용 | variable_costs에서 해당 상품 + 기간 합산 |

### 5.5 리포트

- 상품별 순이익 / 수익률
- 플랫폼별 비교 (같은 상품의 채널별 수익 비교)
- 옵션별 수익 분석 (쿠팡 등 옵션 데이터 있는 채널)
- 기간별 추이 (일/주/월/자유기간)
- 문제 상품 알림 (수익률 마이너스 또는 급락)
- **미매칭 데이터 현황** (미매칭 광고비, 미매칭 판매건 합계)

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
- 가격 데이터 미제공 채널은 판매 데이터에서 평균 판매가 역산 (매출 ÷ 판매량 → actual_unit_price)

---

## 9. 인증

- 간단한 로그인 (아이디/비밀번호)
- JWT 토큰 기반 인증
- 세션 만료 후 재로그인

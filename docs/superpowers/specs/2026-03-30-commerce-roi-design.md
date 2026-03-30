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
| selling_price | DECIMAL | 마켓별 판매가 |
| platform_fee_rate | DECIMAL | 마켓별 수수료율 |
| shipping_fee | DECIMAL | 마켓별 배송비 |
| matched_by | VARCHAR | 매칭 방법 (auto/ai/manual) |
| is_active | BOOLEAN | 판매 중 여부 |

### 3.3 주문 & 정산

**orders**
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_product_id | FK → platform_products | 마켓 상품 연결 |
| order_date | DATE | 주문일 (CSV에서 파싱) |
| order_number | VARCHAR | 주문번호 (중복 방지용) |
| quantity | INTEGER | 수량 |
| sale_price | DECIMAL | 판매가 |
| shipping_fee | DECIMAL | 배송비 |
| platform_fee | DECIMAL | 플랫폼 수수료 |

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

**campaigns** (마케팅 캠페인)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| name | VARCHAR | 캠페인명 |
| start_date | DATE | 시작일 |
| end_date | DATE | 종료일 |
| allocation_method | VARCHAR | 상품직접 / 캠페인배분 / 매출비율 |

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
| campaign_id | FK → campaigns | 캠페인 |
| category_id | FK → cost_categories | 비용 카테고리 |
| product_id | FK → products (nullable) | 상품 직접 연결 시 |
| amount | DECIMAL | 금액 |
| cost_date | DATE | 비용 발생일 |

### 3.5 광고

**ad_data** (마켓 내부 + 외부 광고 통합)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_id | FK → platforms | 광고 플랫폼 |
| platform_product_id | FK → platform_products | 마켓 상품번호로 매칭 |
| campaign_name | VARCHAR | 광고 캠페인명 |
| spend | DECIMAL | 광고비 |
| impressions | INTEGER | 노출수 |
| clicks | INTEGER | 클릭수 |
| conversions | INTEGER | 전환수 |
| ad_date | DATE | 광고 집행일 |

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
| data_type | VARCHAR | order / ad / settlement |
| column_mapping | JSON | 컬럼 매핑 정보 |
| file_type | VARCHAR | xlsx / csv |
| notes | TEXT | 비고 |

column_mapping 예시:
```json
// 쿠팡 주문
{"order_date": "주문일시", "product_id": "노출상품ID", "quantity": "수량", "price": "판매가", "shipping": "배송비"}

// 네이버 주문
{"order_date": "결제일", "product_id": "상품번호", "quantity": "수량", "price": "결제금액", "shipping": "배송비"}

// 쿠팡 광고
{"date": "날짜", "product_id": "광고상품ID", "spend": "광고비", "clicks": "클릭수", "impressions": "노출수"}

// 메타 광고
{"date": "Date", "campaign": "Campaign Name", "spend": "Amount Spent", "clicks": "Link Clicks", "impressions": "Impressions"}
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
| before_value | VARCHAR | 변경 전 값 |
| after_value | VARCHAR | 변경 후 값 |
| event_date | DATE | 변경일 |
| created_at | TIMESTAMP | 기록일 |

**upload_history** (업로드 이력)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_id | FK → platforms | 플랫폼 |
| data_type | VARCHAR | order / ad / settlement |
| file_name | VARCHAR | 파일명 |
| record_count | INTEGER | 처리 건수 |
| period_start | DATE | 데이터 시작일 |
| period_end | DATE | 데이터 종료일 |
| uploaded_at | TIMESTAMP | 업로드 시각 |

### 3.8 상품 매칭 로그

**matching_logs**
| 필드 | 타입 | 설명 |
|------|------|------|
| id | PK | |
| platform_product_name | VARCHAR | 마켓 상품명 (원본) |
| matched_product_id | FK → products | 매칭된 기준 상품 |
| method | VARCHAR | auto / ai / manual |
| confidence | DECIMAL | 매칭 신뢰도 (0~100) |
| created_at | TIMESTAMP | 매칭 시각 |

---

## 4. 상품 매칭 로직

### 자동 매칭 3단계

```
1단계: 정확 매칭
  마켓 상품번호가 platform_products에 이미 있으면 즉시 매칭
        ↓ 실패
2단계: 유사 매칭
  상품명 키워드 토큰화 + 유사도 점수 비교
        ↓ 실패 (confidence < 80%)
3단계: AI 매칭
  Claude API로 상품명 비교 요청 → 매칭 결과 + confidence 반환
        ↓ 실패 (confidence < 60%)
수동 매칭
  관리자에게 매칭 대기 목록으로 표시
```

- 모든 매칭 결과는 matching_logs에 기록
- 최초 1회 매칭 후 platform_products에 저장 → 이후 자동 처리

---

## 5. 수익 계산

### 공식

```
순이익 = 매출 - 원가 - 플랫폼수수료 - 배송비 - 광고비 - 마케팅비 - 커스텀비용
```

### 상품별 수익 계산 항목

| 항목 | 출처 |
|------|------|
| 매출 | orders.sale_price x quantity |
| 원가 | products.base_cost x quantity |
| 플랫폼 수수료 | 매출 x platform_fee_rate |
| 배송비 | orders.shipping_fee |
| 광고비 | ad_data에서 해당 상품 + 기간 합산 |
| 마케팅비 (직접) | marketing_costs에서 product_id 직접 연결분 |
| 마케팅비 (캠페인 배분) | 캠페인 총비용 / 캠페인 내 상품 매출 비율로 배분 |
| 마케팅비 (매출비율) | 월 전체 비용 x 해당 상품 매출 비중 |
| 커스텀 비용 | variable_costs에서 해당 상품 + 기간 합산 |

### 리포트

- 상품별 순이익 / 수익률
- 플랫폼별 비교
- 기간별 추이 (일/주/월/자유기간)
- 문제 상품 알림 (수익률 마이너스 또는 급락)

---

## 6. AI 광고 분석 & 개선안

### 분석 지표

| 항목 | 내용 |
|------|------|
| 광고 효율 | ROAS (광고비 대비 매출), CPC (클릭당 비용), 전환율 |
| 기간 비교 | 전월 대비, 전주 대비 변화 추이 |
| 플랫폼 비교 | 같은 상품의 플랫폼별 광고 성과 비교 |
| 문제 감지 | ROAS 급락, CPC 급등, 전환율 하락 자동 감지 |

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
- 업로드 시 기존 데이터와 병합 (같은 플랫폼 + 같은 날짜 + 같은 주문번호 = 중복 스킵)
- 과거 데이터 수정 시 원본 보존 + 수정 이력 기록
- 업로드 이력 관리 (upload_history)

---

## 9. 인증

- 간단한 로그인 (아이디/비밀번호)
- JWT 토큰 기반 인증
- 세션 만료 후 재로그인

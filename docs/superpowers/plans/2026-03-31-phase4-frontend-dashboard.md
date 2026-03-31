# Phase 4: 프론트엔드 대시보드 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** React 기반 대시보드를 구현하여 로그인, CSV 업로드, 상품/비용 관리, 수익 리포트, 광고 분석, 변경 이벤트 Before/After 비교를 제공한다.

**Architecture:** Vite + React + TypeScript + Ant Design (UI) + Recharts (차트). API 통신은 axios 인스턴스로 JWT 토큰 자동 첨부. 페이지별 라우팅은 React Router.

**Tech Stack:** Vite, React 18, TypeScript, Ant Design 5, Recharts, Axios, React Router 6

---

## 파일 구조

```
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   └── client.ts            # axios 인스턴스 + interceptors
│   ├── hooks/
│   │   └── useAuth.ts           # 인증 상태 관리
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx     # 메인 대시보드 (수익 요약)
│   │   ├── ProductsPage.tsx      # 상품 관리
│   │   ├── UploadPage.tsx        # CSV 업로드
│   │   ├── CostsPage.tsx         # 비용 관리
│   │   ├── AdsPage.tsx           # 광고 데이터 + 캠페인 매핑
│   │   ├── EventsPage.tsx        # 변경 이벤트 관리
│   │   └── ReportsPage.tsx       # 수익 리포트 + 추이 차트
│   ├── components/
│   │   ├── Layout.tsx            # 사이드바 + 헤더 레이아웃
│   │   ├── ProfitTable.tsx       # 수익 테이블
│   │   ├── PlatformCompare.tsx   # 플랫폼별 비교 차트
│   │   ├── TrendChart.tsx        # 기간별 추이 차트 + 이벤트 마커
│   │   └── EventDetail.tsx       # Before/After 비교 패널
│   └── types/
│       └── index.ts              # TypeScript 타입 정의
```

---

### Task 1: React 프로젝트 스캐폴딩

- Create Vite + React + TypeScript 프로젝트
- Install: antd, @ant-design/icons, recharts, axios, react-router-dom
- Configure vite proxy to backend (localhost:8000)
- Verify dev server runs

Commit: `"feat: scaffold React frontend with Vite, Ant Design, Recharts"`

### Task 2: API 클라이언트 + 타입 + 인증

- api/client.ts: axios instance with baseURL, JWT interceptor
- types/index.ts: all TypeScript interfaces matching backend schemas
- hooks/useAuth.ts: login/logout/token management
- pages/LoginPage.tsx: login form with Ant Design

Commit: `"feat: add API client, auth hook, login page"`

### Task 3: Layout + 라우팅 + 대시보드

- components/Layout.tsx: Ant Design Layout with Sider menu
- App.tsx: React Router with protected routes
- pages/DashboardPage.tsx: profit summary cards + quick stats

Commit: `"feat: add layout, routing, dashboard page"`

### Task 4: 상품 관리 + CSV 업로드 페이지

- pages/ProductsPage.tsx: product CRUD table + platform products view
- pages/UploadPage.tsx: file upload form with platform/data_type/period selectors

Commit: `"feat: add products management and CSV upload pages"`

### Task 5: 비용 관리 + 광고 페이지

- pages/CostsPage.tsx: tabs for categories/variable/campaigns/marketing
- pages/AdsPage.tsx: ad data table + campaign mapping CRUD

Commit: `"feat: add cost management and ad data pages"`

### Task 6: 이벤트 관리 + 리포트 페이지

- pages/EventsPage.tsx: event list + create form + detail with Before/After
- pages/ReportsPage.tsx: profit table + platform compare chart + trend chart with event markers

Commit: `"feat: add events and reports pages with charts"`

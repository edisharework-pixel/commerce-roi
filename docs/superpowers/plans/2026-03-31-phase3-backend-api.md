# Phase 3: 백엔드 API 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** FastAPI REST API를 구현하여 인증, 파일 업로드, 상품/플랫폼 CRUD, 수익 계산, 변경 이벤트 관리를 제공한다.

**Architecture:** FastAPI 라우터를 도메인별로 분리 (auth, platforms, products, upload, sales, costs, ads, events, reports). Pydantic 스키마로 요청/응답 검증. 수익 계산은 채널별 플러그인 패턴으로 services/profit_calculator.py에 집중.

**Tech Stack:** FastAPI, Pydantic v2, python-jose (JWT), passlib (bcrypt), 기존 SQLAlchemy 모델 + 파싱 엔진 활용

---

## 파일 구조

```
backend/app/
├── schemas/
│   ├── __init__.py
│   ├── auth.py              # LoginRequest, TokenResponse
│   ├── platform.py          # PlatformOut, PlatformCreate
│   ├── product.py           # ProductOut, ProductCreate, PlatformProductOut, MatchingStatus
│   ├── upload.py            # UploadResponse, UploadHistoryOut
│   ├── sales.py             # SalesSummaryOut, OrderOut, ProfitReport
│   ├── cost.py              # CostCategoryOut, VariableCostCreate, CampaignOut, MarketingCostCreate
│   ├── ad.py                # AdDataOut, AdCampaignMappingCreate
│   ├── event.py             # EventTypeOut, ChangeEventCreate, ChangeEventOut
│   └── report.py            # ProfitByProduct, ProfitByPlatform, TrendData
├── routers/
│   ├── __init__.py
│   ├── auth.py              # POST /auth/login, POST /auth/register
│   ├── platforms.py         # CRUD /platforms
│   ├── products.py          # CRUD /products, /products/{id}/platform-products, /products/unmatched
│   ├── upload.py            # POST /upload, GET /upload/history
│   ├── sales.py             # GET /sales/summary, /sales/orders
│   ├── costs.py             # CRUD /costs/categories, /costs/variable, /costs/campaigns, /costs/marketing
│   ├── ads.py               # GET /ads, CRUD /ads/campaign-mapping
│   ├── events.py            # CRUD /events/types, /events
│   └── reports.py           # GET /reports/profit, /reports/platform-compare, /reports/trend
├── services/
│   ├── upload_service.py    # (Phase 2 — 기존)
│   ├── auth_service.py      # 비밀번호 해싱, JWT 생성/검증
│   └── profit_calculator.py # 채널별 수익 계산 플러그인
├── dependencies.py          # get_current_user, get_db 등 공통 의존성
```

---

### Task 1: 인증 (auth_service + auth 라우터)

**Files:**
- Create: `backend/app/services/auth_service.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/auth.py`
- Create: `backend/app/dependencies.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_routers/__init__.py`
- Create: `backend/tests/test_routers/test_auth.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_routers/test_auth.py
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_register_user(db_session, override_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/auth/register", json={
            "username": "admin", "password": "test1234", "role": "admin"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"


@pytest.mark.asyncio
async def test_login_returns_token(db_session, override_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/auth/register", json={
            "username": "admin", "password": "test1234", "role": "admin"
        })
        resp = await client.post("/auth/login", json={
            "username": "admin", "password": "test1234"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(db_session, override_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/auth/register", json={
            "username": "admin", "password": "test1234", "role": "admin"
        })
        resp = await client.post("/auth/login", json={
            "username": "admin", "password": "wrongpass"
        })
        assert resp.status_code == 401
```

- [ ] **Step 2: Update conftest.py to add override_db fixture**

Add to `backend/tests/conftest.py`:
```python
@pytest_asyncio.fixture
async def override_db(db_session):
    """Override FastAPI's get_db dependency with test session."""
    from app.database import get_db
    from app.main import app

    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()
```

- [ ] **Step 3: Implement auth_service.py**

```python
# backend/app/services/auth_service.py
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
```

- [ ] **Step 4: Implement schemas/auth.py**

```python
# backend/app/schemas/auth.py
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    role: str

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: Implement dependencies.py**

```python
# backend/app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth_service import decode_access_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user
```

- [ ] **Step 6: Implement routers/auth.py**

```python
# backend/app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services.auth_service import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.username == req.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(username=req.username, password_hash=hash_password(req.password), role=req.role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.username})
    return TokenResponse(access_token=token)
```

- [ ] **Step 7: Update main.py to include router**

```python
# backend/app/main.py
from fastapi import FastAPI

from app.routers import auth

app = FastAPI(title="Commerce ROI", version="0.1.0")
app.include_router(auth.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 8: Run tests, commit**

```bash
git commit -m "feat: add auth API — register, login, JWT tokens"
```

---

### Task 2: 플랫폼 + 상품 CRUD API

**Files:**
- Create: `backend/app/schemas/platform.py`
- Create: `backend/app/schemas/product.py`
- Create: `backend/app/routers/platforms.py`
- Create: `backend/app/routers/products.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_routers/test_platforms.py`
- Create: `backend/tests/test_routers/test_products.py`

- [ ] **Step 1: Implement platform schemas**

```python
# backend/app/schemas/platform.py
from decimal import Decimal
from pydantic import BaseModel


class PlatformCreate(BaseModel):
    name: str
    type: str
    fee_rate: Decimal
    vat_included: bool = False
    site_identifier: str | None = None
    seller_id: str | None = None


class PlatformOut(BaseModel):
    id: int
    name: str
    type: str
    fee_rate: Decimal
    vat_included: bool
    site_identifier: str | None
    seller_id: str | None

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Implement product schemas**

```python
# backend/app/schemas/product.py
from decimal import Decimal
from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    sku: str
    base_cost: Decimal
    category: str


class ProductOut(BaseModel):
    id: int
    name: str
    sku: str
    base_cost: Decimal
    category: str

    model_config = {"from_attributes": True}


class PlatformProductOut(BaseModel):
    id: int
    product_id: int
    platform_id: int
    platform_product_id: str
    platform_product_name: str
    selling_price: Decimal | None
    platform_fee_rate: Decimal | None
    sale_status: str | None
    site: str | None
    matched_by: str

    model_config = {"from_attributes": True}


class UnmatchedProductOut(BaseModel):
    id: int
    platform_product_id: str
    platform_product_name: str
    platform_id: int
    matched_by: str

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Implement platforms router**

```python
# backend/app/routers/platforms.py
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.platform import Platform
from app.schemas.platform import PlatformCreate, PlatformOut

router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.get("", response_model=list[PlatformOut])
async def list_platforms(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Platform))
    return result.scalars().all()


@router.post("", response_model=PlatformOut)
async def create_platform(req: PlatformCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    platform = Platform(**req.model_dump())
    db.add(platform)
    await db.commit()
    await db.refresh(platform)
    return platform
```

- [ ] **Step 4: Implement products router**

```python
# backend/app/routers/products.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.product import PlatformProduct, Product
from app.schemas.product import PlatformProductOut, ProductCreate, ProductOut, UnmatchedProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
async def list_products(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Product))
    return result.scalars().all()


@router.post("", response_model=ProductOut)
async def create_product(req: ProductCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    product = Product(**req.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{product_id}/platform-products", response_model=list[PlatformProductOut])
async def list_platform_products(product_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(PlatformProduct).where(PlatformProduct.product_id == product_id))
    return result.scalars().all()


@router.get("/unmatched/list", response_model=list[UnmatchedProductOut])
async def list_unmatched(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(PlatformProduct).where(PlatformProduct.matched_by == "failed"))
    return result.scalars().all()
```

- [ ] **Step 5: Register routers in main.py**

```python
# backend/app/main.py
from fastapi import FastAPI
from app.routers import auth, platforms, products

app = FastAPI(title="Commerce ROI", version="0.1.0")
app.include_router(auth.router)
app.include_router(platforms.router)
app.include_router(products.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Write tests**

```python
# backend/tests/test_routers/test_platforms.py
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

async def _get_auth_header(client):
    await client.post("/auth/register", json={"username": "admin", "password": "test1234", "role": "admin"})
    resp = await client.post("/auth/login", json={"username": "admin", "password": "test1234"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_list_platforms(db_session, override_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await _get_auth_header(client)
        resp = await client.get("/platforms", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

@pytest.mark.asyncio
async def test_create_platform(db_session, override_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await _get_auth_header(client)
        resp = await client.post("/platforms", headers=headers, json={
            "name": "테스트마켓", "type": "마켓", "fee_rate": "5.5", "vat_included": False
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "테스트마켓"
```

```python
# backend/tests/test_routers/test_products.py
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

async def _get_auth_header(client):
    await client.post("/auth/register", json={"username": "admin", "password": "test1234", "role": "admin"})
    resp = await client.post("/auth/login", json={"username": "admin", "password": "test1234"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}

@pytest.mark.asyncio
async def test_create_and_list_products(db_session, override_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await _get_auth_header(client)
        resp = await client.post("/products", headers=headers, json={
            "name": "바디트리머", "sku": "BT-001", "base_cost": "25000", "category": "미용"
        })
        assert resp.status_code == 200
        product_id = resp.json()["id"]

        resp = await client.get("/products", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1
```

- [ ] **Step 7: Run tests, commit**

```bash
git commit -m "feat: add platform and product CRUD APIs with auth"
```

---

### Task 3: 파일 업로드 API

**Files:**
- Create: `backend/app/schemas/upload.py`
- Create: `backend/app/routers/upload.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_routers/test_upload.py`

- [ ] **Step 1: Implement upload schemas**

```python
# backend/app/schemas/upload.py
from datetime import date, datetime
from pydantic import BaseModel


class UploadResponse(BaseModel):
    upload_id: int
    record_count: int
    matched_count: int
    unmatched_count: int


class UploadHistoryOut(BaseModel):
    id: int
    platform_id: int
    data_type: str
    file_name: str
    record_count: int
    matched_count: int
    unmatched_count: int
    period_start: date
    period_end: date
    uploaded_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Implement upload router**

```python
# backend/app/routers/upload.py
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.upload import UploadHistory
from app.schemas.upload import UploadHistoryOut, UploadResponse
from app.services.upload_service import UploadService

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    platform_id: int = Form(...),
    data_type: str = Form(...),
    period_start: date = Form(...),
    period_end: date = Form(...),
    password: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "csv"
    file_type = "xlsx" if file_ext in ("xlsx", "xls") else "csv"

    service = UploadService(db)
    try:
        result = await service.process_upload(
            file=file.file,
            file_type=file_type,
            platform_id=platform_id,
            data_type=data_type,
            period_start=period_start,
            period_end=period_end,
            file_name=file.filename or "unknown",
            password=password,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return UploadResponse(
        upload_id=result.upload_id,
        record_count=result.record_count,
        matched_count=result.matched_count,
        unmatched_count=result.unmatched_count,
    )


@router.get("/history", response_model=list[UploadHistoryOut])
async def list_upload_history(
    platform_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(UploadHistory).order_by(UploadHistory.uploaded_at.desc())
    if platform_id:
        stmt = stmt.where(UploadHistory.platform_id == platform_id)
    result = await db.execute(stmt)
    return result.scalars().all()
```

- [ ] **Step 3: Register router, write test**

Test uploads a CSV via multipart form, verifies UploadResponse.

- [ ] **Step 4: Run tests, commit**

```bash
git commit -m "feat: add file upload API with multipart form support"
```

---

### Task 4: 비용 관리 API (categories, variable, campaigns, marketing)

**Files:**
- Create: `backend/app/schemas/cost.py`
- Create: `backend/app/routers/costs.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_routers/test_costs.py`

- [ ] **Step 1: Implement cost schemas**

```python
# backend/app/schemas/cost.py
from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class CostCategoryOut(BaseModel):
    id: int
    name: str
    type: str
    model_config = {"from_attributes": True}

class CostCategoryCreate(BaseModel):
    name: str
    type: str

class VariableCostCreate(BaseModel):
    product_id: int
    category_id: int
    amount: Decimal
    period_start: date
    period_end: date

class VariableCostOut(BaseModel):
    id: int
    product_id: int
    category_id: int
    amount: Decimal
    period_start: date
    period_end: date
    model_config = {"from_attributes": True}

class CampaignCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    allocation_method: str
    product_ids: list[int] = []

class CampaignOut(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    allocation_method: str
    model_config = {"from_attributes": True}

class MarketingCostCreate(BaseModel):
    campaign_id: int | None = None
    category_id: int
    product_id: int | None = None
    amount: Decimal
    cost_date: date

class MarketingCostOut(BaseModel):
    id: int
    campaign_id: int | None
    category_id: int
    product_id: int | None
    amount: Decimal
    cost_date: date
    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Implement costs router** with CRUD for all 4 entities

- [ ] **Step 3: Write tests, commit**

```bash
git commit -m "feat: add cost management API — categories, variable, campaigns, marketing"
```

---

### Task 5: 광고 데이터 + 캠페인 매핑 API

**Files:**
- Create: `backend/app/schemas/ad.py`
- Create: `backend/app/routers/ads.py`
- Create: `backend/tests/test_routers/test_ads.py`

- [ ] **Step 1: Implement ad schemas + router**

Endpoints:
- `GET /ads` — 광고 데이터 조회 (platform_id, date range 필터)
- `GET /ads/unmatched` — 미매칭 광고 목록
- `POST /ads/campaign-mapping` — 캠페인→상품 매핑 생성
- `GET /ads/campaign-mapping` — 매핑 목록 조회
- `DELETE /ads/campaign-mapping/{id}` — 매핑 삭제

- [ ] **Step 2: Write tests, commit**

```bash
git commit -m "feat: add ad data and campaign-product mapping API"
```

---

### Task 6: 변경 이벤트 API

**Files:**
- Create: `backend/app/schemas/event.py`
- Create: `backend/app/routers/events.py`
- Create: `backend/tests/test_routers/test_events.py`

- [ ] **Step 1: Implement event schemas + router**

Endpoints:
- `GET /events/types` — 이벤트 유형 목록
- `POST /events/types` — 사용자 정의 이벤트 유형 추가
- `GET /events` — 변경 이벤트 목록 (product_id, platform_id, date range 필터)
- `POST /events` — 변경 이벤트 등록
- `GET /events/{id}` — 이벤트 상세 + Before/After 성과 비교 데이터

Before/After 비교 로직: 이벤트 날짜 기준으로 전/후 기간의 sales_summary, ad_data를 집계하여 매출, 순이익, ROAS 등을 비교.

- [ ] **Step 2: Write tests, commit**

```bash
git commit -m "feat: add change event API with before/after comparison"
```

---

### Task 7: 수익 계산 서비스 (채널별 플러그인)

**Files:**
- Create: `backend/app/services/profit_calculator.py`
- Create: `backend/tests/test_services/test_profit_calculator.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_services/test_profit_calculator.py
from datetime import date
from decimal import Decimal

import pytest
from app.models.platform import Platform
from app.models.product import PlatformProduct, Product
from app.models.sales import Order, SalesSummary
from app.models.upload import UploadHistory
from app.services.profit_calculator import ProfitCalculator


@pytest.fixture
async def profit_fixtures(db_session):
    platform_nv = Platform(name="네이버 스마트스토어", type="마켓", fee_rate=5.5, vat_included=True)
    platform_cp = Platform(name="쿠팡", type="마켓", fee_rate=10.8, vat_included=False)
    product = Product(name="바디트리머", sku="BT-001", base_cost=25000, category="미용")
    db_session.add_all([platform_nv, platform_cp, product])
    await db_session.commit()

    pp_nv = PlatformProduct(product_id=product.id, platform_id=platform_nv.id,
        platform_product_id="NV-100", platform_product_name="바디트리머", matched_by="manual")
    pp_cp = PlatformProduct(product_id=product.id, platform_id=platform_cp.id,
        platform_product_id="CP-100", platform_product_name="바디트리머", matched_by="manual")
    db_session.add_all([pp_nv, pp_cp])
    await db_session.commit()

    upload = UploadHistory(platform_id=platform_nv.id, data_type="sales_summary",
        file_name="test.csv", record_count=1, period_start=date(2026, 3, 1), period_end=date(2026, 3, 31))
    db_session.add(upload)
    await db_session.commit()

    # 네이버 판매
    db_session.add(SalesSummary(
        platform_product_id=pp_nv.id, period_start=date(2026, 3, 1), period_end=date(2026, 3, 31),
        gross_revenue=Decimal("5000000"), net_revenue=Decimal("4500000"), quantity=100,
        refund_amount=Decimal("300000"), refund_count=5,
        coupon_seller=Decimal("50000"), coupon_order=Decimal("30000"),
        upload_id=upload.id,
    ))

    upload2 = UploadHistory(platform_id=platform_cp.id, data_type="sales_summary",
        file_name="test2.csv", record_count=1, period_start=date(2026, 3, 1), period_end=date(2026, 3, 31))
    db_session.add(upload2)
    await db_session.commit()

    # 쿠팡 판매
    db_session.add(SalesSummary(
        platform_product_id=pp_cp.id, period_start=date(2026, 3, 1), period_end=date(2026, 3, 31),
        gross_revenue=Decimal("3000000"), net_revenue=Decimal("2500000"), quantity=50,
        cancel_amount=Decimal("500000"), cancel_quantity=10,
        upload_id=upload2.id,
    ))
    await db_session.commit()
    return {"naver": platform_nv, "coupang": platform_cp, "product": product}


@pytest.mark.asyncio
async def test_naver_profit_calculation(db_session, profit_fixtures):
    fixtures = await profit_fixtures
    calc = ProfitCalculator(db_session)
    results = await calc.calculate(
        product_id=fixtures["product"].id,
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
    )
    assert len(results) >= 1
    naver = next(r for r in results if r.platform_name == "네이버 스마트스토어")
    assert naver.revenue > 0
    assert naver.cost_of_goods > 0
    assert naver.net_profit < naver.revenue  # profit < revenue


@pytest.mark.asyncio
async def test_coupang_profit_calculation(db_session, profit_fixtures):
    fixtures = await profit_fixtures
    calc = ProfitCalculator(db_session)
    results = await calc.calculate(
        product_id=fixtures["product"].id,
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
    )
    coupang = next(r for r in results if r.platform_name == "쿠팡")
    assert coupang.revenue == 2500000
```

- [ ] **Step 2: Implement profit_calculator.py**

```python
# backend/app/services/profit_calculator.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import AdData
from app.models.cost import MarketingCost, VariableCost
from app.models.platform import Platform
from app.models.product import PlatformProduct, Product
from app.models.sales import Order, SalesSummary


@dataclass
class ProfitResult:
    platform_name: str
    platform_id: int
    revenue: Decimal
    cost_of_goods: Decimal
    platform_fee: Decimal
    coupon_cost: Decimal
    refund_shipping_cost: Decimal
    ad_cost: Decimal
    marketing_cost: Decimal
    variable_cost: Decimal
    net_profit: Decimal
    profit_rate: Decimal  # percentage


class ProfitCalculator:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def calculate(
        self, product_id: int, period_start: date, period_end: date,
    ) -> list[ProfitResult]:
        product = (await self.session.execute(
            select(Product).where(Product.id == product_id)
        )).scalar_one()

        platform_products = (await self.session.execute(
            select(PlatformProduct).where(PlatformProduct.product_id == product_id)
        )).scalars().all()

        results = []
        for pp in platform_products:
            platform = (await self.session.execute(
                select(Platform).where(Platform.id == pp.platform_id)
            )).scalar_one()

            result = await self._calc_for_platform(product, pp, platform, period_start, period_end)
            if result:
                results.append(result)
        return results

    async def _calc_for_platform(
        self, product: Product, pp: PlatformProduct, platform: Platform,
        period_start: date, period_end: date,
    ) -> ProfitResult | None:
        # Get sales data (sales_summary)
        sales = (await self.session.execute(
            select(SalesSummary).where(
                SalesSummary.platform_product_id == pp.id,
                SalesSummary.period_start >= period_start,
                SalesSummary.period_end <= period_end,
            )
        )).scalars().all()

        # Get orders data (for gmarket/auction)
        orders = (await self.session.execute(
            select(Order).where(
                Order.platform_product_id == pp.id,
                Order.order_date >= period_start,
                Order.order_date <= period_end,
            )
        )).scalars().all()

        if not sales and not orders:
            return None

        # Determine fee rate
        fee_rate = Decimal(str(pp.platform_fee_rate or platform.fee_rate or 0)) / 100

        if platform.name.startswith("네이버"):
            return self._calc_naver(platform, pp, product, sales, fee_rate)
        elif platform.name.startswith("쿠팡"):
            return self._calc_coupang(platform, pp, product, sales, fee_rate)
        elif platform.name.startswith("지마켓") or platform.name.startswith("옥션"):
            return self._calc_gmarket(platform, pp, product, orders, fee_rate)
        return None

    def _calc_naver(self, platform, pp, product, sales, fee_rate) -> ProfitResult:
        revenue = sum(s.net_revenue or 0 for s in sales)
        refund = sum(s.refund_amount or 0 for s in sales)
        quantity = sum(s.quantity or 0 for s in sales)
        refund_count = sum(s.refund_count or 0 for s in sales)
        coupon = sum((s.coupon_seller or 0) + (s.coupon_order or 0) for s in sales)
        return_fee = Decimal(str(pp.return_shipping_fee or 0)) * refund_count

        cogs = product.base_cost * (quantity - refund_count)
        platform_fee = revenue * fee_rate

        net = revenue - cogs - platform_fee - coupon - return_fee
        rate = (net / revenue * 100) if revenue else Decimal("0")

        return ProfitResult(
            platform_name=platform.name, platform_id=platform.id,
            revenue=revenue, cost_of_goods=cogs, platform_fee=platform_fee,
            coupon_cost=coupon, refund_shipping_cost=return_fee,
            ad_cost=Decimal("0"), marketing_cost=Decimal("0"), variable_cost=Decimal("0"),
            net_profit=net, profit_rate=round(rate, 1),
        )

    def _calc_coupang(self, platform, pp, product, sales, fee_rate) -> ProfitResult:
        revenue = sum(s.net_revenue or 0 for s in sales)
        quantity = sum(s.quantity or 0 for s in sales)

        cogs = product.base_cost * quantity
        platform_fee = revenue * fee_rate

        net = revenue - cogs - platform_fee
        rate = (net / revenue * 100) if revenue else Decimal("0")

        return ProfitResult(
            platform_name=platform.name, platform_id=platform.id,
            revenue=revenue, cost_of_goods=cogs, platform_fee=platform_fee,
            coupon_cost=Decimal("0"), refund_shipping_cost=Decimal("0"),
            ad_cost=Decimal("0"), marketing_cost=Decimal("0"), variable_cost=Decimal("0"),
            net_profit=net, profit_rate=round(rate, 1),
        )

    def _calc_gmarket(self, platform, pp, product, orders, fee_rate) -> ProfitResult:
        normal_statuses = {"송금완료", "배송완료"}
        normal_orders = [o for o in orders if o.status in normal_statuses]
        cancel_orders = [o for o in orders if o.status not in normal_statuses]

        revenue = sum(o.sale_price * o.quantity for o in normal_orders)
        cancel_amount = sum(o.sale_price * o.quantity for o in cancel_orders)
        normal_qty = sum(o.quantity for o in normal_orders)

        cogs = product.base_cost * normal_qty
        platform_fee = revenue * fee_rate

        net = revenue - cancel_amount - cogs - platform_fee
        rate = (net / revenue * 100) if revenue else Decimal("0")

        return ProfitResult(
            platform_name=platform.name, platform_id=platform.id,
            revenue=revenue, cost_of_goods=cogs, platform_fee=platform_fee,
            coupon_cost=Decimal("0"), refund_shipping_cost=Decimal("0"),
            ad_cost=Decimal("0"), marketing_cost=Decimal("0"), variable_cost=Decimal("0"),
            net_profit=net, profit_rate=round(rate, 1),
        )
```

- [ ] **Step 3: Run tests, commit**

```bash
git commit -m "feat: add profit calculator with channel-specific plugins (naver/coupang/gmarket)"
```

---

### Task 8: 리포트 API

**Files:**
- Create: `backend/app/schemas/report.py`
- Create: `backend/app/routers/reports.py`
- Create: `backend/tests/test_routers/test_reports.py`

- [ ] **Step 1: Implement report schemas**

```python
# backend/app/schemas/report.py
from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class ProfitByProduct(BaseModel):
    product_id: int
    product_name: str
    sku: str
    platforms: list["PlatformProfit"]
    total_revenue: Decimal
    total_net_profit: Decimal
    total_profit_rate: Decimal


class PlatformProfit(BaseModel):
    platform_name: str
    platform_id: int
    revenue: Decimal
    cost_of_goods: Decimal
    platform_fee: Decimal
    coupon_cost: Decimal
    refund_shipping_cost: Decimal
    ad_cost: Decimal
    marketing_cost: Decimal
    variable_cost: Decimal
    net_profit: Decimal
    profit_rate: Decimal


class PlatformCompare(BaseModel):
    product_name: str
    platforms: list[PlatformProfit]


class TrendPoint(BaseModel):
    period: str  # "2026-03" or "2026-W12" or "2026-03-15"
    revenue: Decimal
    net_profit: Decimal
    profit_rate: Decimal


class TrendData(BaseModel):
    product_name: str
    platform_name: str | None
    points: list[TrendPoint]
    events: list["EventMarker"]


class EventMarker(BaseModel):
    event_date: date
    event_type: str
    description: str
```

- [ ] **Step 2: Implement reports router**

Endpoints:
- `GET /reports/profit` — 상품별 수익 (product_id, period_start, period_end)
- `GET /reports/profit/all` — 전체 상품 수익 요약
- `GET /reports/platform-compare` — 동일 상품의 플랫폼별 비교
- `GET /reports/trend` — 기간별 추이 (product_id, granularity=day/week/month, period)
- `GET /reports/unmatched-summary` — 미매칭 데이터 현황 요약

- [ ] **Step 3: Write tests, commit**

```bash
git commit -m "feat: add report API — profit, platform compare, trend, unmatched summary"
```

---

### Task 9: 전체 통합 + CORS + 최종 main.py

**Files:**
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_integration.py`

- [ ] **Step 1: Final main.py with all routers + CORS**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ads, auth, costs, events, platforms, products, reports, upload

app = FastAPI(title="Commerce ROI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(platforms.router)
app.include_router(products.router)
app.include_router(upload.router)
app.include_router(costs.router)
app.include_router(ads.router)
app.include_router(events.router)
app.include_router(reports.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 2: Integration test (upload → profit report flow)**

```python
# backend/tests/test_integration.py
import io
from datetime import date
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.models.platform import Platform
from app.models.product import PlatformProduct, Product
from app.models.upload import UploadHistory

@pytest.mark.asyncio
async def test_full_flow(db_session, override_db):
    """Integration test: register → create product → upload CSV → get profit report"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register + login
        await client.post("/auth/register", json={"username": "admin", "password": "test1234", "role": "admin"})
        resp = await client.post("/auth/login", json={"username": "admin", "password": "test1234"})
        headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

        # Create product
        resp = await client.post("/products", headers=headers, json={
            "name": "바디트리머", "sku": "BT-001", "base_cost": "25000", "category": "미용"
        })
        assert resp.status_code == 200

        # Health check
        resp = await client.get("/health")
        assert resp.json()["status"] == "ok"
```

- [ ] **Step 3: Run ALL tests, commit**

```bash
git commit -m "feat: integrate all routers with CORS — Phase 3 complete"
```

---

## Phase 3 완료 기준

- [ ] JWT 인증 (register/login)
- [ ] 플랫폼 CRUD
- [ ] 상품 CRUD + 미매칭 목록
- [ ] 파일 업로드 API (multipart form)
- [ ] 비용 관리 (카테고리, 변동비, 캠페인, 마케팅비)
- [ ] 광고 데이터 조회 + 캠페인-상품 매핑 CRUD
- [ ] 변경 이벤트 관리 + Before/After 비교
- [ ] 수익 계산 (네이버/쿠팡/지마켓 플러그인)
- [ ] 리포트 API (수익, 플랫폼비교, 추이, 미매칭)
- [ ] CORS 설정
- [ ] 모든 테스트 PASS

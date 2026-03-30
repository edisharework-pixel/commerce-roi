# Phase 1: 프로젝트 초기화 + DB 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** FastAPI 백엔드 프로젝트를 스캐폴딩하고, 설계서의 전체 DB 스키마를 SQLAlchemy ORM 모델로 구현하여 마이그레이션 및 시드 데이터가 작동하는 상태까지 완성한다.

**Architecture:** FastAPI + SQLAlchemy ORM + Alembic 마이그레이션 + PostgreSQL. 백엔드는 `backend/` 디렉토리에, 프론트엔드는 향후 `frontend/`에 배치. DB 모델은 도메인별로 분리된 파일 구조.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, asyncpg, PostgreSQL 16, pytest, Docker (PostgreSQL용)

---

## 파일 구조

```
commerce-roi/
├── backend/
│   ├── pyproject.toml              # 프로젝트 설정 + 의존성
│   ├── alembic.ini                 # Alembic 설정
│   ├── alembic/
│   │   ├── env.py                  # Alembic 환경 설정
│   │   └── versions/               # 마이그레이션 파일
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py               # 환경 설정 (DATABASE_URL 등)
│   │   ├── database.py             # DB 엔진, 세션 팩토리
│   │   ├── main.py                 # FastAPI 앱 엔트리포인트
│   │   └── models/
│   │       ├── __init__.py         # 모든 모델 re-export
│   │       ├── base.py             # Base 클래스, 공통 믹스인
│   │       ├── user.py             # users
│   │       ├── platform.py         # platforms
│   │       ├── product.py          # products, platform_products, platform_product_options
│   │       ├── sales.py            # orders, sales_summary, settlements
│   │       ├── cost.py             # cost_categories, variable_costs, campaigns, campaign_products, marketing_costs
│   │       ├── ad.py               # ad_data, ad_campaign_product_mapping, ad_analysis_logs
│   │       ├── event.py            # event_types, change_events
│   │       └── upload.py           # upload_history, matching_logs
│   ├── scripts/
│   │   └── seed.py                 # 시드 데이터 (기본 플랫폼, 이벤트 유형 등)
│   └── tests/
│       ├── conftest.py             # 테스트 DB 픽스처
│       ├── test_models/
│       │   ├── test_user.py
│       │   ├── test_platform.py
│       │   ├── test_product.py
│       │   ├── test_sales.py
│       │   ├── test_cost.py
│       │   ├── test_ad.py
│       │   ├── test_event.py
│       │   └── test_upload.py
│       └── test_seed.py
├── docker-compose.yml              # PostgreSQL 컨테이너
└── docs/                           # 기존 설계 문서
```

---

### Task 0: 환경 준비 (Python + PostgreSQL)

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Python 설치 확인**

Python이 Windows Store 리다이렉트 상태이므로 실제 Python 설치 필요.

Run: `winget install Python.Python.3.12`

설치 후 새 터미널에서 확인:
```bash
python --version
```
Expected: `Python 3.12.x`

- [ ] **Step 2: Docker로 PostgreSQL 실행**

Docker Desktop이 설치되어 있다면:

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: commerce
      POSTGRES_PASSWORD: commerce_dev
      POSTGRES_DB: commerce_roi
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

Run: `docker compose up -d`
Expected: PostgreSQL 컨테이너 실행, `localhost:5432` 접속 가능

> Docker가 없으면 PostgreSQL을 직접 설치: `winget install PostgreSQL.PostgreSQL.16`
> 설치 후 DB 생성: `createdb -U postgres commerce_roi`

- [ ] **Step 3: DB 연결 확인**

Run: `docker exec -it commerce-roi-db-1 psql -U commerce -d commerce_roi -c "SELECT 1;"`
Expected: `1` 반환

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml
git commit -m "infra: add docker-compose for PostgreSQL"
```

---

### Task 1: Python 프로젝트 스캐폴딩

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/main.py`

- [ ] **Step 1: pyproject.toml 생성**

```toml
# backend/pyproject.toml
[project]
name = "commerce-roi-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "pydantic-settings>=2.6.0",
    "passlib[bcrypt]>=1.7.4",
    "python-jose[cryptography]>=3.3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.28.0",
    "aiosqlite>=0.20.0",
]

[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 2: venv 생성 및 의존성 설치**

Run:
```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
pip install -e ".[dev]"
```
Expected: 모든 패키지 설치 성공

- [ ] **Step 3: config.py 생성**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://commerce:commerce_dev@localhost:5432/commerce_roi"
    test_database_url: str = "sqlite+aiosqlite:///./test.db"
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    model_config = {"env_prefix": "APP_"}


settings = Settings()
```

- [ ] **Step 4: database.py 생성**

```python
# backend/app/database.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        yield session
```

- [ ] **Step 5: main.py 생성**

```python
# backend/app/main.py
from fastapi import FastAPI

app = FastAPI(title="Commerce ROI", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: __init__.py 생성**

```python
# backend/app/__init__.py
```

- [ ] **Step 7: 서버 실행 확인**

Run:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

별도 터미널에서:
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"ok"}`

- [ ] **Step 8: Commit**

```bash
git add backend/pyproject.toml backend/app/
git commit -m "feat: scaffold FastAPI project with config and database setup"
```

---

### Task 2: SQLAlchemy Base 및 User 모델

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/base.py`
- Create: `backend/app/models/user.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_models/__init__.py`
- Create: `backend/tests/test_models/test_user.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_models/test_user.py
import pytest
from sqlalchemy import select

from app.models.user import User


@pytest.mark.asyncio
async def test_create_user(db_session):
    user = User(username="testuser", password_hash="hashed_pw", role="admin")
    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.username == "testuser"))
    found = result.scalar_one()
    assert found.username == "testuser"
    assert found.role == "admin"
    assert found.created_at is not None


@pytest.mark.asyncio
async def test_user_unique_username(db_session):
    user1 = User(username="duplicate", password_hash="hash1", role="user")
    user2 = User(username="duplicate", password_hash="hash2", role="user")
    db_session.add(user1)
    await db_session.commit()

    db_session.add(user2)
    with pytest.raises(Exception):
        await db_session.commit()
```

- [ ] **Step 2: Create conftest.py with test DB fixture**

```python
# backend/tests/conftest.py
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
```

```python
# backend/tests/__init__.py
```

```python
# backend/tests/test_models/__init__.py
```

- [ ] **Step 3: Create base.py**

```python
# backend/app/models/base.py
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 4: Create user.py model**

```python
# backend/app/models/user.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50))
```

- [ ] **Step 5: Create models __init__.py**

```python
# backend/app/models/__init__.py
from app.models.base import Base
from app.models.user import User

__all__ = ["Base", "User"]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_models/test_user.py -v`
Expected: 2 tests PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/ backend/tests/
git commit -m "feat: add User model with Base and test fixtures"
```

---

### Task 3: Platform 모델

**Files:**
- Create: `backend/app/models/platform.py`
- Create: `backend/tests/test_models/test_platform.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_models/test_platform.py
import pytest
from sqlalchemy import select

from app.models.platform import Platform


@pytest.mark.asyncio
async def test_create_platform(db_session):
    platform = Platform(
        name="쿠팡",
        type="마켓",
        fee_rate=10.8,
        vat_included=False,
    )
    db_session.add(platform)
    await db_session.commit()

    result = await db_session.execute(select(Platform).where(Platform.name == "쿠팡"))
    found = result.scalar_one()
    assert found.name == "쿠팡"
    assert found.fee_rate == 10.8
    assert found.vat_included is False


@pytest.mark.asyncio
async def test_create_gmarket_platform(db_session):
    platform = Platform(
        name="지마켓",
        type="마켓",
        fee_rate=12.0,
        vat_included=False,
        site_identifier="G",
        seller_id="itholic",
    )
    db_session.add(platform)
    await db_session.commit()

    result = await db_session.execute(select(Platform).where(Platform.site_identifier == "G"))
    found = result.scalar_one()
    assert found.name == "지마켓"
    assert found.seller_id == "itholic"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_models/test_platform.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.models.platform'`

- [ ] **Step 3: Create platform.py model**

```python
# backend/app/models/platform.py
from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Platform(Base):
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(50))
    fee_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    vat_included: Mapped[bool] = mapped_column(Boolean, default=False)
    site_identifier: Mapped[str | None] = mapped_column(String(10), nullable=True)
    seller_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
```

- [ ] **Step 4: Update models __init__.py**

```python
# backend/app/models/__init__.py
from app.models.base import Base
from app.models.platform import Platform
from app.models.user import User

__all__ = ["Base", "Platform", "User"]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_models/test_platform.py -v`
Expected: 2 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/platform.py backend/app/models/__init__.py backend/tests/test_models/test_platform.py
git commit -m "feat: add Platform model with site_identifier for gmarket/auction"
```

---

### Task 4: Product, PlatformProduct, PlatformProductOption 모델

**Files:**
- Create: `backend/app/models/product.py`
- Create: `backend/tests/test_models/test_product.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_models/test_product.py
import pytest
from sqlalchemy import select

from app.models.platform import Platform
from app.models.product import PlatformProduct, PlatformProductOption, Product


@pytest.mark.asyncio
async def test_create_product(db_session):
    product = Product(name="운동화A", sku="SHOE-A-001", base_cost=30000, category="신발")
    db_session.add(product)
    await db_session.commit()

    result = await db_session.execute(select(Product).where(Product.sku == "SHOE-A-001"))
    found = result.scalar_one()
    assert found.name == "운동화A"
    assert found.base_cost == 30000


@pytest.mark.asyncio
async def test_platform_product_with_gmarket_fields(db_session):
    platform = Platform(name="지마켓", type="마켓", fee_rate=12.0, vat_included=False, site_identifier="G")
    product = Product(name="볼펜녹음기", sku="PEN-001", base_cost=15000, category="전자")
    db_session.add_all([platform, product])
    await db_session.commit()

    pp = PlatformProduct(
        product_id=product.id,
        platform_id=platform.id,
        platform_product_id="GP-12345",
        platform_product_name="볼펜녹음기 32GB",
        seller_product_code="PEN-REC-32",
        selling_price=39900,
        platform_fee_rate=12.0,
        shipping_type="paid",
        shipping_fee=3000,
        return_shipping_fee=5000,
        exchange_shipping_fee=10000,
        sale_status="판매중",
        site="G",
        master_product_id="MASTER-001",
        matched_by="auto",
    )
    db_session.add(pp)
    await db_session.commit()

    result = await db_session.execute(
        select(PlatformProduct).where(PlatformProduct.platform_product_id == "GP-12345")
    )
    found = result.scalar_one()
    assert found.site == "G"
    assert found.master_product_id == "MASTER-001"
    assert found.return_shipping_fee == 5000


@pytest.mark.asyncio
async def test_platform_product_option_unique_constraint(db_session):
    platform = Platform(name="쿠팡", type="마켓", fee_rate=10.8, vat_included=False)
    product = Product(name="바디트리머", sku="BT-001", base_cost=25000, category="미용")
    db_session.add_all([platform, product])
    await db_session.commit()

    pp = PlatformProduct(
        product_id=product.id,
        platform_id=platform.id,
        platform_product_id="CP-67890",
        platform_product_name="바디트리머 프로",
        matched_by="auto",
    )
    db_session.add(pp)
    await db_session.commit()

    opt1 = PlatformProductOption(
        platform_product_id=pp.id,
        option_id="OPT-001",
        option_name="블랙",
        is_active=True,
    )
    opt2 = PlatformProductOption(
        platform_product_id=pp.id,
        option_id="OPT-002",
        option_name="화이트",
        is_active=True,
    )
    db_session.add_all([opt1, opt2])
    await db_session.commit()

    result = await db_session.execute(
        select(PlatformProductOption).where(
            PlatformProductOption.platform_product_id == pp.id
        )
    )
    options = result.scalars().all()
    assert len(options) == 2

    # Test unique constraint
    opt_dup = PlatformProductOption(
        platform_product_id=pp.id,
        option_id="OPT-001",
        option_name="블랙 중복",
        is_active=True,
    )
    db_session.add(opt_dup)
    with pytest.raises(Exception):
        await db_session.commit()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_models/test_product.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create product.py model**

```python
# backend/app/models/product.py
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    sku: Mapped[str] = mapped_column(String(100), unique=True)
    base_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    category: Mapped[str] = mapped_column(String(200))

    platform_products: Mapped[list["PlatformProduct"]] = relationship(back_populates="product")


class PlatformProduct(Base):
    __tablename__ = "platform_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"))
    platform_product_id: Mapped[str] = mapped_column(String(100))
    platform_product_name: Mapped[str] = mapped_column(String(500))
    seller_product_code: Mapped[str | None] = mapped_column(String(200), nullable=True)
    selling_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    discount_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    platform_fee_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    shipping_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    shipping_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    return_shipping_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    exchange_shipping_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    sale_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    site: Mapped[str | None] = mapped_column(String(10), nullable=True)
    master_product_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    matched_by: Mapped[str] = mapped_column(String(20))

    product: Mapped["Product"] = relationship(back_populates="platform_products")
    options: Mapped[list["PlatformProductOption"]] = relationship(back_populates="platform_product")


class PlatformProductOption(Base):
    __tablename__ = "platform_product_options"
    __table_args__ = (
        UniqueConstraint("platform_product_id", "option_id", name="uq_pp_option"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_product_id: Mapped[int] = mapped_column(ForeignKey("platform_products.id"))
    option_id: Mapped[str] = mapped_column(String(100))
    option_name: Mapped[str] = mapped_column(String(500))
    option_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    platform_product: Mapped["PlatformProduct"] = relationship(back_populates="options")
```

- [ ] **Step 4: Update models __init__.py**

```python
# backend/app/models/__init__.py
from app.models.base import Base
from app.models.platform import Platform
from app.models.product import PlatformProduct, PlatformProductOption, Product
from app.models.user import User

__all__ = [
    "Base",
    "Platform",
    "PlatformProduct",
    "PlatformProductOption",
    "Product",
    "User",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_models/test_product.py -v`
Expected: 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/product.py backend/app/models/__init__.py backend/tests/test_models/test_product.py
git commit -m "feat: add Product, PlatformProduct, PlatformProductOption models"
```

---

### Task 5: Sales 모델 (orders, sales_summary, settlements)

**Files:**
- Create: `backend/app/models/sales.py`
- Create: `backend/tests/test_models/test_sales.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_models/test_sales.py
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.platform import Platform
from app.models.product import PlatformProduct, PlatformProductOption, Product
from app.models.sales import Order, SalesSummary, Settlement
from app.models.upload import UploadHistory


@pytest.fixture
async def sample_platform_product(db_session):
    platform = Platform(name="쿠팡", type="마켓", fee_rate=10.8, vat_included=False)
    product = Product(name="테스트상품", sku="TEST-001", base_cost=10000, category="테스트")
    db_session.add_all([platform, product])
    await db_session.commit()

    pp = PlatformProduct(
        product_id=product.id,
        platform_id=platform.id,
        platform_product_id="CP-TEST",
        platform_product_name="테스트상품 쿠팡",
        matched_by="auto",
    )
    db_session.add(pp)
    await db_session.commit()

    upload = UploadHistory(
        platform_id=platform.id,
        data_type="sales_summary",
        file_name="test.csv",
        record_count=1,
        matched_count=1,
        unmatched_count=0,
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
    )
    db_session.add(upload)
    await db_session.commit()

    return pp, platform, upload


@pytest.mark.asyncio
async def test_create_sales_summary(db_session, sample_platform_product):
    pp, platform, upload = await sample_platform_product

    ss = SalesSummary(
        platform_product_id=pp.id,
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
        gross_revenue=Decimal("5000000"),
        net_revenue=Decimal("4500000"),
        quantity=100,
        cancel_amount=Decimal("500000"),
        cancel_quantity=10,
        visitors=5000,
        page_views=8000,
        cart_count=200,
        conversion_rate=Decimal("3.2"),
        upload_id=upload.id,
    )
    db_session.add(ss)
    await db_session.commit()

    result = await db_session.execute(select(SalesSummary).where(SalesSummary.id == ss.id))
    found = result.scalar_one()
    assert found.net_revenue == Decimal("4500000")
    assert found.visitors == 5000


@pytest.mark.asyncio
async def test_create_order_with_status(db_session, sample_platform_product):
    pp, platform, upload = await sample_platform_product

    order = Order(
        platform_product_id=pp.id,
        order_date=date(2026, 3, 15),
        order_number="ORD-001",
        quantity=2,
        sale_price=Decimal("39900"),
        status="배송완료",
        site="G",
        upload_id=upload.id,
    )
    db_session.add(order)
    await db_session.commit()

    result = await db_session.execute(select(Order).where(Order.order_number == "ORD-001"))
    found = result.scalar_one()
    assert found.status == "배송완료"
    assert found.site == "G"


@pytest.mark.asyncio
async def test_create_settlement(db_session, sample_platform_product):
    _, platform, _ = await sample_platform_product

    settlement = Settlement(
        platform_id=platform.id,
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
        expected_amount=Decimal("4500000"),
        status="예정",
    )
    db_session.add(settlement)
    await db_session.commit()

    result = await db_session.execute(select(Settlement).where(Settlement.id == settlement.id))
    found = result.scalar_one()
    assert found.status == "예정"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_models/test_sales.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create upload.py model first (sales depends on it)**

```python
# backend/app/models/upload.py
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UploadHistory(Base):
    __tablename__ = "upload_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"))
    data_type: Mapped[str] = mapped_column(String(50))
    file_name: Mapped[str] = mapped_column(String(500))
    record_count: Mapped[int] = mapped_column(Integer)
    matched_count: Mapped[int] = mapped_column(Integer, default=0)
    unmatched_count: Mapped[int] = mapped_column(Integer, default=0)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MatchingLog(Base):
    __tablename__ = "matching_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_product_name: Mapped[str] = mapped_column(String(500))
    matched_product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    method: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[float] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 4: Create sales.py model**

```python
# backend/app/models/sales.py
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SalesSummary(Base):
    __tablename__ = "sales_summary"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_product_id: Mapped[int] = mapped_column(ForeignKey("platform_products.id"))
    option_id: Mapped[int | None] = mapped_column(ForeignKey("platform_product_options.id"), nullable=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    gross_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    net_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    quantity: Mapped[int] = mapped_column(Integer)
    cancel_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    cancel_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    refund_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    refund_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    coupon_seller: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    coupon_order: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    visitors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cart_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conversion_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    upload_id: Mapped[int] = mapped_column(ForeignKey("upload_history.id"))


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_product_id: Mapped[int] = mapped_column(ForeignKey("platform_products.id"))
    option_id: Mapped[int | None] = mapped_column(ForeignKey("platform_product_options.id"), nullable=True)
    order_date: Mapped[date] = mapped_column(Date)
    order_number: Mapped[str] = mapped_column(String(100), unique=True)
    quantity: Mapped[int] = mapped_column(Integer)
    sale_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    shipping_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    platform_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    cancelled_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    cancelled_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    refund_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(50))
    site: Mapped[str | None] = mapped_column(String(10), nullable=True)
    upload_id: Mapped[int] = mapped_column(ForeignKey("upload_history.id"))
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    actual_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20))
```

- [ ] **Step 5: Update models __init__.py**

```python
# backend/app/models/__init__.py
from app.models.base import Base
from app.models.platform import Platform
from app.models.product import PlatformProduct, PlatformProductOption, Product
from app.models.sales import Order, SalesSummary, Settlement
from app.models.upload import MatchingLog, UploadHistory
from app.models.user import User

__all__ = [
    "Base",
    "MatchingLog",
    "Order",
    "Platform",
    "PlatformProduct",
    "PlatformProductOption",
    "Product",
    "SalesSummary",
    "Settlement",
    "UploadHistory",
    "User",
]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_models/test_sales.py -v`
Expected: 3 tests PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/ backend/tests/test_models/test_sales.py
git commit -m "feat: add SalesSummary, Order, Settlement, UploadHistory, MatchingLog models"
```

---

### Task 6: Cost 모델 (cost_categories, variable_costs, campaigns, marketing_costs)

**Files:**
- Create: `backend/app/models/cost.py`
- Create: `backend/tests/test_models/test_cost.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_models/test_cost.py
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.cost import Campaign, CampaignProduct, CostCategory, MarketingCost, VariableCost
from app.models.product import Product


@pytest.mark.asyncio
async def test_create_cost_category(db_session):
    cat = CostCategory(name="인플루언서 비용", type="마케팅비")
    db_session.add(cat)
    await db_session.commit()

    result = await db_session.execute(select(CostCategory).where(CostCategory.name == "인플루언서 비용"))
    found = result.scalar_one()
    assert found.type == "마케팅비"


@pytest.mark.asyncio
async def test_variable_cost(db_session):
    product = Product(name="테스트", sku="VC-001", base_cost=10000, category="테스트")
    cat = CostCategory(name="포장비", type="변동비")
    db_session.add_all([product, cat])
    await db_session.commit()

    vc = VariableCost(
        product_id=product.id,
        category_id=cat.id,
        amount=Decimal("500"),
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
    )
    db_session.add(vc)
    await db_session.commit()

    result = await db_session.execute(select(VariableCost).where(VariableCost.product_id == product.id))
    found = result.scalar_one()
    assert found.amount == Decimal("500")


@pytest.mark.asyncio
async def test_campaign_with_marketing_cost(db_session):
    product = Product(name="테스트", sku="MC-001", base_cost=10000, category="테스트")
    cat = CostCategory(name="촬영비", type="마케팅비")
    db_session.add_all([product, cat])
    await db_session.commit()

    campaign = Campaign(
        name="Q1 바디케어 프로모션",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        allocation_method="revenue_ratio",
    )
    db_session.add(campaign)
    await db_session.commit()

    cp = CampaignProduct(campaign_id=campaign.id, product_id=product.id)
    mc = MarketingCost(
        campaign_id=campaign.id,
        category_id=cat.id,
        amount=Decimal("3000000"),
        cost_date=date(2026, 3, 15),
    )
    db_session.add_all([cp, mc])
    await db_session.commit()

    result = await db_session.execute(select(MarketingCost).where(MarketingCost.campaign_id == campaign.id))
    found = result.scalar_one()
    assert found.amount == Decimal("3000000")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_models/test_cost.py -v`
Expected: FAIL

- [ ] **Step 3: Create cost.py model**

```python
# backend/app/models/cost.py
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CostCategory(Base):
    __tablename__ = "cost_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(50))


class VariableCost(Base):
    __tablename__ = "variable_costs"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("cost_categories.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    allocation_method: Mapped[str] = mapped_column(String(30))


class CampaignProduct(Base):
    __tablename__ = "campaign_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))


class MarketingCost(Base):
    __tablename__ = "marketing_costs"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int | None] = mapped_column(ForeignKey("campaigns.id"), nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("cost_categories.id"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    cost_date: Mapped[date] = mapped_column(Date)
```

- [ ] **Step 4: Update models __init__.py**

```python
# backend/app/models/__init__.py
from app.models.base import Base
from app.models.cost import Campaign, CampaignProduct, CostCategory, MarketingCost, VariableCost
from app.models.platform import Platform
from app.models.product import PlatformProduct, PlatformProductOption, Product
from app.models.sales import Order, SalesSummary, Settlement
from app.models.upload import MatchingLog, UploadHistory
from app.models.user import User

__all__ = [
    "Base",
    "Campaign",
    "CampaignProduct",
    "CostCategory",
    "MarketingCost",
    "MatchingLog",
    "Order",
    "Platform",
    "PlatformProduct",
    "PlatformProductOption",
    "Product",
    "SalesSummary",
    "Settlement",
    "UploadHistory",
    "User",
    "VariableCost",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_models/test_cost.py -v`
Expected: 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/cost.py backend/app/models/__init__.py backend/tests/test_models/test_cost.py
git commit -m "feat: add CostCategory, VariableCost, Campaign, MarketingCost models"
```

---

### Task 7: Ad 모델 (ad_data, ad_campaign_product_mapping, ad_analysis_logs)

**Files:**
- Create: `backend/app/models/ad.py`
- Create: `backend/tests/test_models/test_ad.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_models/test_ad.py
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.ad import AdAnalysisLog, AdCampaignProductMapping, AdData
from app.models.platform import Platform
from app.models.product import PlatformProduct, Product


@pytest.fixture
async def ad_fixtures(db_session):
    platform = Platform(name="네이버", type="마켓", fee_rate=5.5, vat_included=True)
    product = Product(name="바디트리머", sku="AD-001", base_cost=25000, category="미용")
    db_session.add_all([platform, product])
    await db_session.commit()

    pp = PlatformProduct(
        product_id=product.id,
        platform_id=platform.id,
        platform_product_id="NV-12345",
        platform_product_name="바디트리머 네이버",
        matched_by="manual",
    )
    db_session.add(pp)
    await db_session.commit()
    return platform, product, pp


@pytest.mark.asyncio
async def test_create_ad_data_naver(db_session, ad_fixtures):
    platform, product, pp = await ad_fixtures

    ad = AdData(
        platform_id=platform.id,
        campaign_name="◆바디트리머",
        ad_group="바디트리머_쇼핑",
        keyword="바디트리머",
        ad_type="쇼핑검색",
        spend=Decimal("50000"),
        impressions=10000,
        clicks=500,
        direct_conversions=15,
        direct_revenue=Decimal("750000"),
        ad_date=date(2026, 3, 15),
        match_status="pending",
    )
    db_session.add(ad)
    await db_session.commit()

    result = await db_session.execute(select(AdData).where(AdData.id == ad.id))
    found = result.scalar_one()
    assert found.platform_product_id is None
    assert found.match_status == "pending"


@pytest.mark.asyncio
async def test_create_ad_campaign_mapping(db_session, ad_fixtures):
    platform, product, _ = await ad_fixtures

    mapping = AdCampaignProductMapping(
        platform_id=platform.id,
        campaign_name="◆바디트리머",
        product_id=product.id,
        allocation_method="single",
    )
    db_session.add(mapping)
    await db_session.commit()

    result = await db_session.execute(
        select(AdCampaignProductMapping).where(AdCampaignProductMapping.campaign_name == "◆바디트리머")
    )
    found = result.scalar_one()
    assert found.allocation_method == "single"


@pytest.mark.asyncio
async def test_create_ad_analysis_log(db_session, ad_fixtures):
    _, product, _ = await ad_fixtures

    log = AdAnalysisLog(
        product_id=product.id,
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
        analysis_result={"roas": 3.2, "cpc": 850, "conversion_rate": 2.5},
        suggestions="ROAS가 전월 대비 15% 하락. CPC 유지 중 전환율 감소 — 상세페이지 점검 권장",
    )
    db_session.add(log)
    await db_session.commit()

    result = await db_session.execute(select(AdAnalysisLog).where(AdAnalysisLog.product_id == product.id))
    found = result.scalar_one()
    assert found.analysis_result["roas"] == 3.2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_models/test_ad.py -v`
Expected: FAIL

- [ ] **Step 3: Create ad.py model**

```python
# backend/app/models/ad.py
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AdData(Base):
    __tablename__ = "ad_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"))
    platform_product_id: Mapped[int | None] = mapped_column(ForeignKey("platform_products.id"), nullable=True)
    option_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    campaign_name: Mapped[str] = mapped_column(String(500))
    ad_group: Mapped[str | None] = mapped_column(String(500), nullable=True)
    keyword: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ad_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    exposure_area: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device: Mapped[str | None] = mapped_column(String(20), nullable=True)
    spend: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    impressions: Mapped[int] = mapped_column(Integer)
    clicks: Mapped[int] = mapped_column(Integer)
    direct_conversions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    indirect_conversions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    direct_revenue: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    indirect_revenue: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    attribution_window: Mapped[str | None] = mapped_column(String(10), nullable=True)
    avg_rank: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    site: Mapped[str | None] = mapped_column(String(10), nullable=True)
    ad_date: Mapped[date] = mapped_column(Date)
    match_status: Mapped[str] = mapped_column(String(20), default="pending")
    extended_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AdCampaignProductMapping(TimestampMixin, Base):
    __tablename__ = "ad_campaign_product_mapping"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"))
    campaign_name: Mapped[str] = mapped_column(String(500))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    allocation_method: Mapped[str] = mapped_column(String(30))


class AdAnalysisLog(TimestampMixin, Base):
    __tablename__ = "ad_analysis_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    analysis_result: Mapped[dict] = mapped_column(JSON)
    suggestions: Mapped[str] = mapped_column(Text)
```

- [ ] **Step 4: Update models __init__.py**

```python
# backend/app/models/__init__.py
from app.models.ad import AdAnalysisLog, AdCampaignProductMapping, AdData
from app.models.base import Base
from app.models.cost import Campaign, CampaignProduct, CostCategory, MarketingCost, VariableCost
from app.models.platform import Platform
from app.models.product import PlatformProduct, PlatformProductOption, Product
from app.models.sales import Order, SalesSummary, Settlement
from app.models.upload import MatchingLog, UploadHistory
from app.models.user import User

__all__ = [
    "AdAnalysisLog",
    "AdCampaignProductMapping",
    "AdData",
    "Base",
    "Campaign",
    "CampaignProduct",
    "CostCategory",
    "MarketingCost",
    "MatchingLog",
    "Order",
    "Platform",
    "PlatformProduct",
    "PlatformProductOption",
    "Product",
    "SalesSummary",
    "Settlement",
    "UploadHistory",
    "User",
    "VariableCost",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_models/test_ad.py -v`
Expected: 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/ad.py backend/app/models/__init__.py backend/tests/test_models/test_ad.py
git commit -m "feat: add AdData, AdCampaignProductMapping, AdAnalysisLog models"
```

---

### Task 8: Event 모델 (event_types, change_events)

**Files:**
- Create: `backend/app/models/event.py`
- Create: `backend/tests/test_models/test_event.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_models/test_event.py
from datetime import date

import pytest
from sqlalchemy import select

from app.models.event import ChangeEvent, EventType
from app.models.user import User


@pytest.mark.asyncio
async def test_create_default_event_type(db_session):
    et = EventType(name="판매가 수정", is_default=True)
    db_session.add(et)
    await db_session.commit()

    result = await db_session.execute(select(EventType).where(EventType.is_default.is_(True)))
    found = result.scalars().all()
    assert len(found) >= 1
    assert found[0].name == "판매가 수정"


@pytest.mark.asyncio
async def test_create_change_event_with_json_details(db_session):
    user = User(username="admin", password_hash="hash", role="admin")
    et = EventType(name="광고 예산 변경", is_default=True)
    db_session.add_all([user, et])
    await db_session.commit()

    event = ChangeEvent(
        event_type_id=et.id,
        description="쿠팡 바디트리머 일 예산 5만→10만원",
        change_details={"field": "daily_budget", "before": 50000, "after": 100000},
        event_date=date(2026, 3, 20),
    )
    db_session.add(event)
    await db_session.commit()

    result = await db_session.execute(select(ChangeEvent).where(ChangeEvent.id == event.id))
    found = result.scalar_one()
    assert found.change_details["before"] == 50000
    assert found.change_details["after"] == 100000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_models/test_event.py -v`
Expected: FAIL

- [ ] **Step 3: Create event.py model**

```python
# backend/app/models/event.py
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class EventType(Base):
    __tablename__ = "event_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class ChangeEvent(TimestampMixin, Base):
    __tablename__ = "change_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type_id: Mapped[int] = mapped_column(ForeignKey("event_types.id"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    platform_id: Mapped[int | None] = mapped_column(ForeignKey("platforms.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    change_details: Mapped[dict] = mapped_column(JSON)
    event_date: Mapped[date] = mapped_column(Date)
```

- [ ] **Step 4: Update models __init__.py**

```python
# backend/app/models/__init__.py
from app.models.ad import AdAnalysisLog, AdCampaignProductMapping, AdData
from app.models.base import Base
from app.models.cost import Campaign, CampaignProduct, CostCategory, MarketingCost, VariableCost
from app.models.event import ChangeEvent, EventType
from app.models.platform import Platform
from app.models.product import PlatformProduct, PlatformProductOption, Product
from app.models.sales import Order, SalesSummary, Settlement
from app.models.upload import MatchingLog, UploadHistory
from app.models.user import User

__all__ = [
    "AdAnalysisLog",
    "AdCampaignProductMapping",
    "AdData",
    "Base",
    "Campaign",
    "CampaignProduct",
    "ChangeEvent",
    "CostCategory",
    "EventType",
    "MarketingCost",
    "MatchingLog",
    "Order",
    "Platform",
    "PlatformProduct",
    "PlatformProductOption",
    "Product",
    "SalesSummary",
    "Settlement",
    "UploadHistory",
    "User",
    "VariableCost",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_models/test_event.py -v`
Expected: 2 tests PASS

- [ ] **Step 6: Run ALL tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: 모든 테스트 PASS (약 16개)

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/ backend/tests/test_models/test_event.py
git commit -m "feat: add EventType, ChangeEvent models — all DB models complete"
```

---

### Task 9: Alembic 마이그레이션 설정

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/` (자동 생성)

- [ ] **Step 1: Alembic 초기화**

Run:
```bash
cd backend
alembic init alembic
```
Expected: `alembic/` 디렉토리 및 `alembic.ini` 생성

- [ ] **Step 2: alembic.ini 수정**

`alembic.ini`에서 `sqlalchemy.url` 행을 수정:

```ini
sqlalchemy.url = postgresql+asyncpg://commerce:commerce_dev@localhost:5432/commerce_roi
```

- [ ] **Step 3: alembic/env.py 수정**

```python
# backend/alembic/env.py
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: 초기 마이그레이션 생성**

Run:
```bash
cd backend
alembic revision --autogenerate -m "initial schema"
```
Expected: `alembic/versions/` 아래에 마이그레이션 파일 생성

- [ ] **Step 5: 마이그레이션 실행**

Run:
```bash
cd backend
alembic upgrade head
```
Expected: 모든 테이블 생성 완료

- [ ] **Step 6: DB 확인**

Run:
```bash
docker exec -it commerce-roi-db-1 psql -U commerce -d commerce_roi -c "\dt"
```
Expected: users, platforms, products, platform_products, platform_product_options, sales_summary, orders, settlements, cost_categories, variable_costs, campaigns, campaign_products, marketing_costs, ad_data, ad_campaign_product_mapping, ad_analysis_logs, event_types, change_events, upload_history, matching_logs 테이블 존재

- [ ] **Step 7: Commit**

```bash
git add backend/alembic.ini backend/alembic/
git commit -m "feat: add Alembic migrations — initial schema applied"
```

---

### Task 10: 시드 데이터

**Files:**
- Create: `backend/scripts/seed.py`
- Create: `backend/tests/test_seed.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_seed.py
import pytest
from sqlalchemy import select

from app.models.cost import CostCategory
from app.models.event import EventType
from app.models.platform import Platform
from scripts.seed import seed_data


@pytest.mark.asyncio
async def test_seed_creates_platforms(db_session):
    await seed_data(db_session)

    result = await db_session.execute(select(Platform))
    platforms = result.scalars().all()
    names = {p.name for p in platforms}
    assert "쿠팡" in names
    assert "네이버 스마트스토어" in names
    assert "지마켓" in names
    assert "옥션" in names


@pytest.mark.asyncio
async def test_seed_creates_event_types(db_session):
    await seed_data(db_session)

    result = await db_session.execute(select(EventType).where(EventType.is_default.is_(True)))
    event_types = result.scalars().all()
    names = {et.name for et in event_types}
    assert "판매가 수정" in names
    assert "쿠폰 적용" in names
    assert "목표 ROAS 변경" in names
    assert "광고 예산 변경" in names


@pytest.mark.asyncio
async def test_seed_creates_cost_categories(db_session):
    await seed_data(db_session)

    result = await db_session.execute(select(CostCategory))
    categories = result.scalars().all()
    names = {c.name for c in categories}
    assert "인플루언서 비용" in names
    assert "촬영비" in names


@pytest.mark.asyncio
async def test_seed_is_idempotent(db_session):
    await seed_data(db_session)
    await seed_data(db_session)

    result = await db_session.execute(select(Platform))
    platforms = result.scalars().all()
    # 중복 생성 없이 동일 수
    name_counts = {}
    for p in platforms:
        name_counts[p.name] = name_counts.get(p.name, 0) + 1
    assert all(count == 1 for count in name_counts.values())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_seed.py -v`
Expected: FAIL

- [ ] **Step 3: Create seed.py**

```python
# backend/scripts/seed.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost import CostCategory
from app.models.event import EventType
from app.models.platform import Platform


async def _seed_if_empty(session: AsyncSession, model, items: list[dict]):
    result = await session.execute(select(model))
    if result.scalars().first() is not None:
        return
    for item in items:
        session.add(model(**item))
    await session.commit()


async def seed_data(session: AsyncSession):
    await _seed_if_empty(session, Platform, [
        {"name": "쿠팡", "type": "마켓", "fee_rate": 10.8, "vat_included": False},
        {"name": "네이버 스마트스토어", "type": "마켓", "fee_rate": 5.5, "vat_included": True},
        {"name": "지마켓", "type": "마켓", "fee_rate": 12.0, "vat_included": False, "site_identifier": "G", "seller_id": "itholic"},
        {"name": "옥션", "type": "마켓", "fee_rate": 12.0, "vat_included": False, "site_identifier": "A", "seller_id": "itemholic"},
        {"name": "11번가", "type": "마켓", "fee_rate": 11.0, "vat_included": False},
        {"name": "카페24", "type": "마켓", "fee_rate": 0.0, "vat_included": False},
        {"name": "네이버 검색광고", "type": "외부광고", "fee_rate": 0.0, "vat_included": True},
        {"name": "쿠팡 광고", "type": "외부광고", "fee_rate": 0.0, "vat_included": False},
        {"name": "지마켓/옥션 광고", "type": "외부광고", "fee_rate": 0.0, "vat_included": False},
        {"name": "메타 광고", "type": "외부광고", "fee_rate": 0.0, "vat_included": False},
        {"name": "구글 광고", "type": "외부광고", "fee_rate": 0.0, "vat_included": False},
    ])

    await _seed_if_empty(session, EventType, [
        {"name": "쿠폰 적용", "is_default": True},
        {"name": "목표 ROAS 변경", "is_default": True},
        {"name": "광고 예산 변경", "is_default": True},
        {"name": "판매가 수정", "is_default": True},
    ])

    await _seed_if_empty(session, CostCategory, [
        {"name": "인플루언서 비용", "type": "마케팅비"},
        {"name": "촬영비", "type": "마케팅비"},
        {"name": "모델비", "type": "마케팅비"},
        {"name": "물류비", "type": "마케팅비"},
        {"name": "행사진행비", "type": "마케팅비"},
        {"name": "체험단 비용", "type": "마케팅비"},
    ])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_seed.py -v`
Expected: 4 tests PASS

- [ ] **Step 5: Run seed against real DB**

Run:
```bash
cd backend
python -c "
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import settings
from scripts.seed import seed_data

async def main():
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await seed_data(session)
        print('Seed complete')
    await engine.dispose()

asyncio.run(main())
"
```
Expected: `Seed complete`

- [ ] **Step 6: Run ALL tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: 모든 테스트 PASS (약 20개)

- [ ] **Step 7: Commit**

```bash
git add backend/scripts/seed.py backend/tests/test_seed.py
git commit -m "feat: add seed data — platforms, event types, cost categories"
```

---

## Phase 1 완료 기준

- [ ] PostgreSQL 실행 중 (Docker 또는 로컬)
- [ ] 모든 20개 DB 테이블 생성 완료
- [ ] 시드 데이터 (플랫폼 11개, 이벤트유형 4개, 비용카테고리 6개) 투입 완료
- [ ] 모든 테스트 PASS
- [ ] FastAPI `/health` 엔드포인트 응답 확인

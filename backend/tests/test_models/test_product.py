import pytest
from sqlalchemy import select
from app.models.platform import Platform
from app.models.product import PlatformProduct, PlatformProductOption, Product


@pytest.mark.asyncio
async def test_create_product(db_session):
    product = Product(name="테스트 상품", sku="SKU-001", base_cost=10000, category="생활용품")
    db_session.add(product)
    await db_session.commit()
    result = await db_session.execute(select(Product).where(Product.sku == "SKU-001"))
    found = result.scalar_one()
    assert found.name == "테스트 상품"
    assert found.base_cost == 10000


@pytest.mark.asyncio
async def test_create_platform_product_with_gmarket_fields(db_session):
    product = Product(name="상품A", sku="SKU-A", base_cost=5000, category="패션")
    platform = Platform(name="지마켓", type="마켓", fee_rate=12.0, vat_included=False, site_identifier="G")
    db_session.add_all([product, platform])
    await db_session.commit()

    pp = PlatformProduct(
        product_id=product.id,
        platform_id=platform.id,
        platform_product_id="G123456",
        platform_product_name="지마켓 상품A",
        site="G",
        master_product_id="M100",
        matched_by="sku",
    )
    db_session.add(pp)
    await db_session.commit()
    result = await db_session.execute(
        select(PlatformProduct).where(PlatformProduct.site == "G")
    )
    found = result.scalar_one()
    assert found.master_product_id == "M100"
    assert found.matched_by == "sku"


@pytest.mark.asyncio
async def test_option_unique_constraint(db_session):
    product = Product(name="상품B", sku="SKU-B", base_cost=3000, category="식품")
    platform = Platform(name="쿠팡", type="마켓", fee_rate=10.8, vat_included=False)
    db_session.add_all([product, platform])
    await db_session.commit()

    pp = PlatformProduct(
        product_id=product.id,
        platform_id=platform.id,
        platform_product_id="C999",
        platform_product_name="쿠팡 상품B",
        matched_by="name",
    )
    db_session.add(pp)
    await db_session.commit()

    opt1 = PlatformProductOption(
        platform_product_id=pp.id,
        option_id="OPT-1",
        option_name="빨강",
    )
    opt2 = PlatformProductOption(
        platform_product_id=pp.id,
        option_id="OPT-1",
        option_name="파랑",
    )
    db_session.add(opt1)
    await db_session.commit()
    db_session.add(opt2)
    with pytest.raises(Exception):
        await db_session.commit()

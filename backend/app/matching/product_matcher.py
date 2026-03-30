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
    method: str = "failed"
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
        # Stage 1: Exact match by platform_product_id
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
        # Stage 4: AI (placeholder)
        return MatchResult(matched=False, method="failed", confidence=0.0)

    async def _exact_match(self, platform_id, platform_product_id):
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

    async def _seller_code_match(self, platform_id, seller_code):
        stmt = select(PlatformProduct).where(
            PlatformProduct.seller_product_code == seller_code
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

    async def _similar_match(self, platform_id, product_name):
        stmt = select(PlatformProduct).where(
            PlatformProduct.platform_id == platform_id
        )
        result = await self.session.execute(stmt)
        candidates = result.scalars().all()
        best_match, best_score = None, 0.0
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

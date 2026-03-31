from datetime import date
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.ad import AdAnalysisLog, AdData
from app.models.platform import Platform
from app.models.product import PlatformProduct, Product


class AIAdAnalyzer:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def analyze_product_ads(
        self, product_id: int, period_start: date, period_end: date
    ) -> dict:
        """Analyze ad performance for a product and generate AI suggestions."""
        product = (await self.session.execute(
            select(Product).where(Product.id == product_id)
        )).scalar_one()

        platform_products = (await self.session.execute(
            select(PlatformProduct).where(PlatformProduct.product_id == product_id)
        )).scalars().all()

        # Gather ad data per platform
        ad_summary = []
        for pp in platform_products:
            platform = (await self.session.execute(
                select(Platform).where(Platform.id == pp.platform_id)
            )).scalar_one()

            ads = (await self.session.execute(
                select(AdData).where(
                    AdData.platform_product_id == pp.id,
                    AdData.ad_date >= period_start,
                    AdData.ad_date <= period_end,
                )
            )).scalars().all()

            if not ads:
                continue

            total_spend = sum(float(a.spend) for a in ads)
            total_clicks = sum(a.clicks for a in ads)
            total_impressions = sum(a.impressions for a in ads)
            total_conversions = sum((a.direct_conversions or 0) for a in ads)
            total_revenue = sum(float(a.direct_revenue or 0) for a in ads)

            roas = total_revenue / total_spend if total_spend > 0 else 0
            cpc = total_spend / total_clicks if total_clicks > 0 else 0
            ctr = total_clicks / total_impressions * 100 if total_impressions > 0 else 0
            cvr = total_conversions / total_clicks * 100 if total_clicks > 0 else 0

            ad_summary.append({
                "platform": platform.name,
                "spend": total_spend,
                "clicks": total_clicks,
                "impressions": total_impressions,
                "conversions": total_conversions,
                "revenue": total_revenue,
                "roas": round(roas, 2),
                "cpc": round(cpc, 0),
                "ctr": round(ctr, 2),
                "cvr": round(cvr, 2),
            })

        if not ad_summary:
            return {"analysis_result": {}, "suggestions": "분석할 광고 데이터가 없습니다."}

        # Generate AI suggestions
        suggestions = await self._generate_suggestions(product.name, ad_summary)

        # Save to ad_analysis_logs
        log = AdAnalysisLog(
            product_id=product_id,
            period_start=period_start,
            period_end=period_end,
            analysis_result={"platforms": ad_summary},
            suggestions=suggestions,
        )
        self.session.add(log)
        await self.session.commit()

        return {
            "analysis_result": {"platforms": ad_summary},
            "suggestions": suggestions,
            "log_id": log.id,
        }

    async def _generate_suggestions(self, product_name: str, ad_summary: list[dict]) -> str:
        """Generate ad improvement suggestions using Claude API."""
        if not settings.anthropic_api_key:
            return self._generate_fallback_suggestions(product_name, ad_summary)

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

            prompt = f"""다음은 '{product_name}' 상품의 플랫폼별 광고 성과 데이터입니다:

{self._format_ad_data(ad_summary)}

위 데이터를 분석하여 다음을 한국어로 제공해주세요:
1. 각 플랫폼별 광고 효율 평가 (ROAS, CPC, 전환율 기준)
2. 문제점 진단 (ROAS 낮은 채널, CPC 높은 채널 등)
3. 구체적인 개선 제안 (예산 재배분, 키워드 전략, 채널 전환 등)
4. 우선순위가 높은 액션 아이템 3가지

간결하고 실행 가능한 조언을 제공해주세요."""

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            return self._generate_fallback_suggestions(product_name, ad_summary)

    def _generate_fallback_suggestions(self, product_name: str, ad_summary: list[dict]) -> str:
        """Generate rule-based suggestions when AI is not available."""
        suggestions = [f"## {product_name} 광고 분석 결과\n"]

        for p in ad_summary:
            name = p["platform"]
            suggestions.append(f"### {name}")
            suggestions.append(f"- ROAS: {p['roas']} | CPC: \u20a9{p['cpc']:,.0f} | CTR: {p['ctr']}% | \uc804\ud658\uc728: {p['cvr']}%")

            if p["roas"] < 2:
                suggestions.append(f"  \u26a0\ufe0f ROAS {p['roas']}\ub85c \ub0ae\uc74c \u2014 \uad11\uace0 \uc18c\uc7ac/\ud0c0\uac9f\ud305 \uc810\uac80 \ub610\ub294 \uc608\uc0b0 \ucd95\uc18c \uac80\ud1a0")
            elif p["roas"] > 5:
                suggestions.append(f"  \u2705 ROAS {p['roas']}\ub85c \uc6b0\uc218 \u2014 \uc608\uc0b0 \ud655\ub300 \uac80\ud1a0")

            if p["ctr"] < 1:
                suggestions.append(f"  \u26a0\ufe0f CTR {p['ctr']}%\ub85c \ub0ae\uc74c \u2014 \uad11\uace0 \uc18c\uc7ac/\ud0a4\uc6cc\ub4dc \uac1c\uc120 \ud544\uc694")

            if p["cvr"] < 1:
                suggestions.append(f"  \u26a0\ufe0f \uc804\ud658\uc728 {p['cvr']}%\ub85c \ub0ae\uc74c \u2014 \uc0c1\uc138\ud398\uc774\uc9c0 \ub610\ub294 \uac00\uaca9 \uacbd\uc7c1\ub825 \uc810\uac80")

        # Cross-platform comparison
        if len(ad_summary) >= 2:
            best = max(ad_summary, key=lambda x: x["roas"])
            worst = min(ad_summary, key=lambda x: x["roas"])
            if best["roas"] > worst["roas"] * 2:
                suggestions.append(f"\n### \ucc44\ub110 \uac04 \ube44\uad50")
                suggestions.append(f"- {best['platform']}\uc758 ROAS({best['roas']})\uac00 {worst['platform']}({worst['roas']})\ubcf4\ub2e4 {best['roas']/worst['roas']:.1f}\ubc30 \ub192\uc74c")
                suggestions.append(f"- {worst['platform']} \uc608\uc0b0\uc744 {best['platform']}\uc73c\ub85c \uc7ac\ubc30\ubd84 \uac80\ud1a0")

        return "\n".join(suggestions)

    def _format_ad_data(self, ad_summary: list[dict]) -> str:
        lines = []
        for p in ad_summary:
            lines.append(f"[{p['platform']}] \uad11\uace0\ube44: \u20a9{p['spend']:,.0f} | \ud074\ub9ad: {p['clicks']} | "
                        f"\ub178\ucd9c: {p['impressions']} | \uc804\ud658: {p['conversions']} | "
                        f"\ub9e4\ucd9c: \u20a9{p['revenue']:,.0f} | ROAS: {p['roas']} | "
                        f"CPC: \u20a9{p['cpc']:,.0f} | CTR: {p['ctr']}% | \uc804\ud658\uc728: {p['cvr']}%")
        return "\n".join(lines)

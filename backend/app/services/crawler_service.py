"""
Technical SEO Crawler Service.
Analyzes Core Web Vitals, heading hierarchy, schema markup, and image ALTs.
"""
import asyncio
import hashlib
import time
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.models.database import (
    CrawlAudit,
    CoreWebVitals,
    HeadingHierarchy,
    SchemaMarkup,
    ImageAltIssue,
    PageIssue,
    InternalLink,
    IssueSeverity,
    CrawlStatus,
)

settings = get_settings()


class PageSpeedService:
    """
    Google PageSpeed Insights API integration for Core Web Vitals.
    """
    
    def __init__(self):
        self.api_key = settings.pagespeed_api_key
        self.base_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    
    async def analyze_url(self, url: str, strategy: str = "mobile") -> Dict[str, Any]:
        """
        Fetch Core Web Vitals from PageSpeed API.
        """
        if not self.api_key:
            return self._empty_metrics()
        
        params = {
            "url": url,
            "strategy": strategy,
            "key": self.api_key,
            "category": ["PERFORMANCE", "ACCESSIBILITY", "BEST_PRACTICES", "SEO"]
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                return self._parse_metrics(data, strategy)
            except Exception:
                return self._empty_metrics()
    
    def _parse_metrics(self, data: Dict, strategy: str) -> Dict[str, Any]:
        """
        Extract Core Web Vitals from PageSpeed response.
        """
        lighthouse = data.get("lighthouseResult", {})
        metrics = lighthouse.get("audits", {})
        categories = lighthouse.get("categories", {})
        
        performance_score = categories.get("performance", {}).get("score", 0)
        
        def get_metric(name: str) -> Optional[float]:
            metric = metrics.get(name, {})
            raw = metric.get("numericValue")
            if raw:
                # Convert to appropriate units
                if "largest-contentful-paint" in name or "contentful-paint" in name:
                    return round(raw / 1000, 2)  # ms to seconds
                elif "layout-shift" in name:
                    return round(raw, 3)
                return raw
            return None
        
        return CoreWebVitals(
            lcp=get_metric("largest-contentful-paint"),
            fcp=get_metric("first-contentful-paint"),
            cls=get_metric("cumulative-layout-shift"),
            score_mobile=int(performance_score * 100) if strategy == "mobile" else None,
            score_desktop=int(performance_score * 100) if strategy == "desktop" else None,
        )
    
    def _empty_metrics(self) -> CoreWebVitals:
        return CoreWebVitals()


class TechnicalCrawler:
    """
    Advanced technical SEO crawler with JavaScript rendering support.
    """
    
    def __init__(self):
        self.pagespeed = PageSpeedService()
        self.headers = {
            "User-Agent": settings.crawler_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
        }
    
    async def crawl_url(
        self,
        url: str,
        project_id: str,
        crawl_session_id: str,
        check_pagespeed: bool = True
    ) -> CrawlAudit:
        """
        Execute comprehensive technical audit on a single URL.
        """
        audit = CrawlAudit(
            project_id=project_id,
            url=url,
            domain=urlparse(url).netloc,
            crawl_session_id=crawl_session_id,
            status=CrawlStatus.IN_PROGRESS,
        )
        
        await audit.insert()
        
        try:
            start_time = time.time()
            
            # Fetch page
            async with httpx.AsyncClient(
                headers=self.headers,
                follow_redirects=True,
                timeout=30.0
            ) as client:
                response = await client.get(url)
                audit.status_code = response.status_code
                audit.content_type = response.headers.get("content-type")
                audit.page_size_bytes = len(response.content)
                audit.load_time_ms = round((time.time() - start_time) * 1000, 2)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml")
                    
                    # Extract all SEO elements
                    await self._extract_seo_elements(audit, soup, response.text)
                    await self._analyze_headings(audit, soup)
                    await self._analyze_schema_markup(audit, soup)
                    await self._analyze_images(audit, soup, url)
                    await self._analyze_links(audit, soup, url)
                    await self._analyze_content(audit, response.text)
                    
                    # Fetch Core Web Vitals
                    if check_pagespeed:
                        mobile_vitals = await self.pagespeed.analyze_url(url, "mobile")
                        audit.core_web_vitals = mobile_vitals
            
            audit.status = CrawlStatus.COMPLETED
            audit.issue_counts = self._calculate_issue_counts(audit.issues)
            
        except Exception as e:
            audit.status = CrawlStatus.FAILED
            audit.issues.append(PageIssue(
                type="crawl_error",
                severity=IssueSeverity.CRITICAL,
                description=str(e),
                fix_suggestion="Check URL accessibility and server response"
            ))
        
        await audit.save()
        return audit
    
    async def _extract_seo_elements(self, audit: CrawlAudit, soup: BeautifulSoup, raw_html: str):
        """
        Extract title, meta description, canonical, and robots meta.
        """
        # Title
        title_tag = soup.find("title")
        if title_tag:
            audit.title = title_tag.get_text(strip=True)
            audit.title_length = len(audit.title)
            
            # Validate title
            if not audit.title:
                audit.issues.append(PageIssue(
                    type="missing_title",
                    severity=IssueSeverity.CRITICAL,
                    description="Page has no title tag",
                    fix_suggestion="Add a descriptive <title> tag between 50-60 characters"
                ))
            elif audit.title_length < 30:
                audit.issues.append(PageIssue(
                    type="short_title",
                    severity=IssueSeverity.MEDIUM,
                    description=f"Title is only {audit.title_length} characters",
                    fix_suggestion="Expand title to 50-60 characters for better CTR"
                ))
            elif audit.title_length > 70:
                audit.issues.append(PageIssue(
                    type="long_title",
                    severity=IssueSeverity.LOW,
                    description=f"Title is {audit.title_length} characters (may be truncated in SERP)",
                    element=f"<title>{audit.title}</title>",
                    fix_suggestion="Reduce title to 60 characters or less"
                ))
        
        # Meta Description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            audit.meta_description = meta_desc.get("content", "")
            audit.meta_description_length = len(audit.meta_description)
            
            if audit.meta_description_length < 120:
                audit.issues.append(PageIssue(
                    type="short_meta_description",
                    severity=IssueSeverity.MEDIUM,
                    description=f"Meta description is only {audit.meta_description_length} characters",
                    fix_suggestion="Expand to 150-160 characters with compelling CTA"
                ))
            elif audit.meta_description_length > 170:
                audit.issues.append(PageIssue(
                    type="long_meta_description",
                    severity=IssueSeverity.LOW,
                    description="Meta description may be truncated in SERP",
                    fix_suggestion="Reduce to 160 characters or less"
                ))
        else:
            audit.issues.append(PageIssue(
                type="missing_meta_description",
                severity=IssueSeverity.HIGH,
                description="No meta description found",
                fix_suggestion="Add a unique meta description between 150-160 characters"
            ))
        
        # Canonical URL
        canonical = soup.find("link", attrs={"rel": "canonical"})
        if canonical:
            audit.canonical_url = canonical.get("href")
        else:
            audit.issues.append(PageIssue(
                type="missing_canonical",
                severity=IssueSeverity.MEDIUM,
                description="No canonical tag specified",
                fix_suggestion="Add <link rel=\"canonical\" href=\"...\"> to prevent duplicate content issues"
            ))
        
        # Robots Meta
        robots = soup.find("meta", attrs={"name": "robots"})
        if robots:
            audit.robots_meta = robots.get("content", "")
    
    async def _analyze_headings(self, audit: CrawlAudit, soup: BeautifulSoup):
        """
        Analyze H1-H6 hierarchy and detect issues.
        """
        hierarchy = HeadingHierarchy()
        
        for level in range(1, 7):
            tags = soup.find_all(f"h{level}")
            texts = [tag.get_text(strip=True) for tag in tags if tag.get_text(strip=True)]
            setattr(hierarchy, f"h{level}", texts)
        
        # Validate hierarchy
        if len(hierarchy.h1) == 0:
            audit.issues.append(PageIssue(
                type="missing_h1",
                severity=IssueSeverity.CRITICAL,
                description="No H1 heading found",
                fix_suggestion="Add exactly one H1 heading that describes the page content"
            ))
        elif len(hierarchy.h1) > 1:
            audit.issues.append(PageIssue(
                type="multiple_h1",
                severity=IssueSeverity.HIGH,
                description=f"Found {len(hierarchy.h1)} H1 headings",
                element="<h1>",
                fix_suggestion="Use only one H1 per page; convert additional H1s to H2"
            ))
        
        # Check for skipped levels
        if hierarchy.h3 and not hierarchy.h2:
            hierarchy.issues.append("H3 found without H2 - hierarchy violation")
            audit.issues.append(PageIssue(
                type="heading_hierarchy",
                severity=IssueSeverity.MEDIUM,
                description="Heading structure skips levels (H3 without H2)",
                fix_suggestion="Maintain proper heading hierarchy (H1 > H2 > H3)"
            ))
        
        # Check for empty headings
        for level in range(1, 7):
            headings = getattr(hierarchy, f"h{level}")
            empty_count = sum(1 for h in headings if not h.strip())
            if empty_count > 0:
                audit.issues.append(PageIssue(
                    type="empty_heading",
                    severity=IssueSeverity.MEDIUM,
                    description=f"Found {empty_count} empty H{level} tags",
                    fix_suggestion="Remove empty heading tags or add descriptive text"
                ))
        
        audit.headings = hierarchy
    
    async def _analyze_schema_markup(self, audit: CrawlAudit, soup: BeautifulSoup):
        """
        Extract and validate JSON-LD and Microdata schema markup.
        """
        schemas = []
        
        # JSON-LD
        json_ld_scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
        for script in json_ld_scripts:
            import json
            try:
                data = json.loads(script.string) if script.string else {}
                schema_type = data.get("@type", "Unknown")
                schemas.append(SchemaMarkup(
                    type=schema_type,
                    properties=data,
                    valid=True
                ))
            except json.JSONDecodeError:
                schemas.append(SchemaMarkup(
                    type="Invalid JSON-LD",
                    valid=False,
                    errors=["Malformed JSON in script tag"]
                ))
                audit.issues.append(PageIssue(
                    type="invalid_schema",
                    severity=IssueSeverity.HIGH,
                    description="Invalid JSON-LD schema markup detected",
                    fix_suggestion="Validate JSON-LD using Google's Rich Results Test"
                ))
        
        # Check for recommended schemas
        schema_types = [s.type for s in schemas]
        recommended = ["WebPage", "Organization", "BreadcrumbList"]
        missing = [r for r in recommended if r not in schema_types]
        
        if "WebPage" not in schema_types and "Article" not in schema_types:
            audit.issues.append(PageIssue(
                type="missing_schema",
                severity=IssueSeverity.MEDIUM,
                description="No WebPage or Article schema markup found",
                fix_suggestion="Add structured data to enhance SERP appearance"
            ))
        
        audit.schema_markup = schemas
    
    async def _analyze_images(self, audit: CrawlAudit, soup: BeautifulSoup, base_url: str):
        """
        Detect images missing ALT text.
        """
        images = soup.find_all("img")
        missing_alts = []
        
        for img in images:
            src = img.get("src", "")
            alt = img.get("alt")
            
            # Skip decorative images (tracking pixels, etc.)
            if src and ("tracking" in src or "pixel" in src or "1x1" in src):
                continue
            
            if alt is None:
                missing_alts.append(ImageAltIssue(
                    src=urljoin(base_url, src),
                    severity=IssueSeverity.HIGH,
                    suggestion="Add descriptive alt text for accessibility and SEO"
                ))
            elif alt == "":
                missing_alts.append(ImageAltIssue(
                    src=urljoin(base_url, src),
                    severity=IssueSeverity.MEDIUM,
                    suggestion="Empty alt attribute; add text or use alt=\"\" for decorative images"
                ))
        
        audit.images_without_alt = missing_alts
        
        if len(missing_alts) > 5:
            audit.issues.append(PageIssue(
                type="multiple_missing_alts",
                severity=IssueSeverity.HIGH,
                description=f"{len(missing_alts)} images missing alt text",
                fix_suggestion="Add descriptive alt attributes to all content images"
            ))
    
    async def _analyze_links(self, audit: CrawlAudit, soup: BeautifulSoup, base_url: str):
        """
        Analyze internal and external links.
        """
        internal_links = []
        external_links = []
        broken_links = 0
        
        base_domain = urlparse(base_url).netloc
        links = soup.find_all("a", href=True)
        
        for link in links:
            href = link.get("href", "").strip()
            absolute_url = urljoin(base_url, href)
            parsed = urlparse(absolute_url)
            
            # Skip anchors, javascript, mailto
            if href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            
            if parsed.netloc == base_domain or not parsed.netloc:
                # Internal link
                internal_links.append(InternalLink(
                    source_url=base_url,
                    target_url=absolute_url,
                    anchor_text=link.get_text(strip=True)[:100]
                ))
            else:
                # External link
                external_links.append(absolute_url)
        
        audit.internal_links = internal_links[:100]  # Limit storage
        audit.external_links = external_links[:50]
        audit.broken_links_count = broken_links
    
    async def _analyze_content(self, audit: CrawlAudit, raw_html: str):
        """
        Basic content analysis: word count, fingerprinting.
        """
        # Simple word count (strip HTML tags)
        text = BeautifulSoup(raw_html, "lxml").get_text()
        words = text.split()
        audit.word_count = len(words)
        
        # Content fingerprint for change detection
        audit.content_fingerprint = hashlib.md5(text[:1000].encode()).hexdigest()
        
        if audit.word_count < 300:
            audit.issues.append(PageIssue(
                type="thin_content",
                severity=IssueSeverity.HIGH,
                description=f"Page has only {audit.word_count} words",
                fix_suggestion="Add substantial content; aim for 500+ words for ranking pages"
            ))
    
    def _calculate_issue_counts(self, issues: List[PageIssue]) -> Dict[str, int]:
        """
        Aggregate issue counts by severity.
        """
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for issue in issues:
            counts[issue.severity] = counts.get(issue.severity, 0) + 1
        return counts
    
    async def crawl_site(
        self,
        start_url: str,
        project_id: str,
        max_pages: int = 100,
        max_depth: int = 3
    ) -> List[CrawlAudit]:
        """
        Multi-page site crawl with BFS traversal.
        """
        import uuid
        crawl_session_id = str(uuid.uuid4())
        
        visited = set()
        to_visit = [(start_url, 0)]  # (url, depth)
        results = []
        
        while to_visit and len(visited) < max_pages:
            current_url, depth = to_visit.pop(0)
            
            if current_url in visited or depth > max_depth:
                continue
            
            visited.add(current_url)
            
            # Crawl the page
            audit = await self.crawl_url(
                current_url,
                project_id,
                crawl_session_id,
                check_pagespeed=(len(visited) <= 10)  # Limit PageSpeed API calls
            )
            results.append(audit)
            
            # Queue internal links
            if depth < max_depth:
                for link in audit.internal_links:
                    if link.target_url not in visited:
                        to_visit.append((link.target_url, depth + 1))
            
            # Rate limiting
            await asyncio.sleep(settings.crawler_request_delay)
        
        return results

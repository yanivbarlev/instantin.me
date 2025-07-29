"""
SEO Optimization Utilities

Comprehensive SEO system for storefronts including meta tags, structured data,
sitemaps, and search engine optimization utilities.
"""

import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, quote
from dataclasses import dataclass, asdict
from enum import Enum

from app.config import settings


class StructuredDataType(str, Enum):
    """Types of structured data schemas."""
    ORGANIZATION = "Organization"
    PERSON = "Person" 
    WEBSITE = "WebSite"
    WEBPAGE = "WebPage"
    PRODUCT = "Product"
    OFFER = "Offer"
    BREADCRUMB_LIST = "BreadcrumbList"
    FAQ_PAGE = "FAQPage"
    ARTICLE = "Article"
    LOCAL_BUSINESS = "LocalBusiness"


class SitemapChangeFreq(str, Enum):
    """XML sitemap change frequency values."""
    ALWAYS = "always"
    HOURLY = "hourly" 
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    NEVER = "never"


@dataclass
class MetaTags:
    """Container for HTML meta tags."""
    title: str
    description: str
    keywords: List[str] = None
    canonical_url: str = None
    og_title: str = None
    og_description: str = None
    og_image: str = None
    og_url: str = None
    og_type: str = "website"
    og_site_name: str = "InstantIn.me"
    twitter_card: str = "summary_large_image"
    twitter_title: str = None
    twitter_description: str = None
    twitter_image: str = None
    twitter_site: str = None
    robots: str = "index, follow"
    author: str = None
    viewport: str = "width=device-width, initial-scale=1.0"
    charset: str = "utf-8"
    
    def __post_init__(self):
        """Set defaults based on primary values."""
        if not self.og_title:
            self.og_title = self.title
        if not self.og_description:
            self.og_description = self.description
        if not self.twitter_title:
            self.twitter_title = self.title
        if not self.twitter_description:
            self.twitter_description = self.description
        if not self.twitter_image and self.og_image:
            self.twitter_image = self.og_image
        if self.keywords is None:
            self.keywords = []
    
    def to_html(self) -> str:
        """Generate HTML meta tags."""
        tags = []
        
        # Basic meta tags
        tags.append(f'<meta charset="{self.charset}">')
        tags.append(f'<meta name="viewport" content="{self.viewport}">')
        tags.append(f'<title>{self._escape_html(self.title)}</title>')
        tags.append(f'<meta name="description" content="{self._escape_html(self.description)}">')
        
        if self.keywords:
            keywords_str = ", ".join(self.keywords)
            tags.append(f'<meta name="keywords" content="{self._escape_html(keywords_str)}">')
        
        if self.author:
            tags.append(f'<meta name="author" content="{self._escape_html(self.author)}">')
        
        tags.append(f'<meta name="robots" content="{self.robots}">')
        
        if self.canonical_url:
            tags.append(f'<link rel="canonical" href="{self.canonical_url}">')
        
        # Open Graph tags
        tags.append(f'<meta property="og:title" content="{self._escape_html(self.og_title)}">')
        tags.append(f'<meta property="og:description" content="{self._escape_html(self.og_description)}">')
        tags.append(f'<meta property="og:type" content="{self.og_type}">')
        tags.append(f'<meta property="og:site_name" content="{self.og_site_name}">')
        
        if self.og_url:
            tags.append(f'<meta property="og:url" content="{self.og_url}">')
        
        if self.og_image:
            tags.append(f'<meta property="og:image" content="{self.og_image}">')
            tags.append('<meta property="og:image:type" content="image/jpeg">')
            tags.append('<meta property="og:image:width" content="1200">')
            tags.append('<meta property="og:image:height" content="630">')
        
        # Twitter Card tags
        tags.append(f'<meta name="twitter:card" content="{self.twitter_card}">')
        tags.append(f'<meta name="twitter:title" content="{self._escape_html(self.twitter_title)}">')
        tags.append(f'<meta name="twitter:description" content="{self._escape_html(self.twitter_description)}">')
        
        if self.twitter_image:
            tags.append(f'<meta name="twitter:image" content="{self.twitter_image}">')
        
        if self.twitter_site:
            tags.append(f'<meta name="twitter:site" content="{self.twitter_site}">')
        
        return "\n".join(tags)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&#x27;"))


@dataclass
class SitemapEntry:
    """Single entry in an XML sitemap."""
    url: str
    last_modified: datetime = None
    change_frequency: SitemapChangeFreq = SitemapChangeFreq.WEEKLY
    priority: float = 0.5
    
    def __post_init__(self):
        """Set default last_modified if not provided."""
        if not self.last_modified:
            self.last_modified = datetime.now(timezone.utc)
        
        # Validate priority
        if not 0.0 <= self.priority <= 1.0:
            self.priority = 0.5


class SEOService:
    """Service for generating SEO optimizations."""
    
    def __init__(self, base_url: str = None):
        """Initialize SEO service with base URL."""
        self.base_url = base_url or settings.app_url or "https://instantin.me"
        if not self.base_url.endswith('/'):
            self.base_url += '/'
    
    def generate_storefront_meta_tags(
        self, 
        storefront_data: Dict[str, Any],
        current_url: str = None
    ) -> MetaTags:
        """Generate meta tags for a storefront page."""
        
        # Extract storefront information
        name = storefront_data.get('name', 'Creator Profile')
        description = storefront_data.get('description', '')
        slug = storefront_data.get('slug', '')
        avatar_url = storefront_data.get('avatar_url')
        
        # Generate SEO-friendly title
        title = f"{name} | InstantIn.me"
        if len(title) > 60:
            title = f"{name[:50]}... | InstantIn.me"
        
        # Generate description
        if not description:
            description = f"Discover {name}'s products and services on InstantIn.me. Shop directly from this creator's personalized storefront."
        
        # Truncate description for meta tags
        if len(description) > 160:
            description = description[:157] + "..."
        
        # Generate URLs
        canonical_url = current_url or self._build_storefront_url(slug)
        
        # Extract keywords from name and description
        keywords = self._extract_keywords(f"{name} {description}")
        
        return MetaTags(
            title=title,
            description=description,
            keywords=keywords,
            canonical_url=canonical_url,
            og_url=canonical_url,
            og_image=avatar_url,
            og_type="profile",
            author=name,
            twitter_site="@instantinme"
        )
    
    def generate_product_meta_tags(
        self,
        product_data: Dict[str, Any],
        storefront_data: Dict[str, Any],
        current_url: str = None
    ) -> MetaTags:
        """Generate meta tags for a product page."""
        
        # Extract product information
        product_name = product_data.get('name', 'Product')
        product_description = product_data.get('description', '')
        product_image = product_data.get('image_url')
        price = product_data.get('price', 0)
        
        # Extract storefront information
        creator_name = storefront_data.get('name', 'Creator')
        storefront_slug = storefront_data.get('slug', '')
        
        # Generate SEO-friendly title
        title = f"{product_name} by {creator_name} | InstantIn.me"
        if len(title) > 60:
            title = f"{product_name[:40]}... | InstantIn.me"
        
        # Generate description
        if not product_description:
            product_description = f"Get {product_name} by {creator_name} on InstantIn.me."
        
        # Add price to description if available
        if price > 0:
            price_str = f"${price:.2f}".rstrip('0').rstrip('.')
            product_description = f"{product_description} Starting at {price_str}."
        
        # Truncate description
        if len(product_description) > 160:
            product_description = product_description[:157] + "..."
        
        # Generate URLs
        canonical_url = current_url or self._build_product_url(storefront_slug, product_data.get('id'))
        
        # Extract keywords
        keywords = self._extract_keywords(f"{product_name} {creator_name} {product_description}")
        
        return MetaTags(
            title=title,
            description=product_description,
            keywords=keywords,
            canonical_url=canonical_url,
            og_url=canonical_url,
            og_image=product_image,
            og_type="product",
            author=creator_name,
            twitter_site="@instantinme"
        )
    
    def generate_structured_data(
        self,
        data_type: StructuredDataType,
        data: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> str:
        """Generate JSON-LD structured data."""
        
        structured_data = {
            "@context": "https://schema.org",
            "@type": data_type.value
        }
        
        if data_type == StructuredDataType.ORGANIZATION:
            structured_data.update(self._build_organization_data(data))
        elif data_type == StructuredDataType.PERSON:
            structured_data.update(self._build_person_data(data))
        elif data_type == StructuredDataType.WEBSITE:
            structured_data.update(self._build_website_data(data))
        elif data_type == StructuredDataType.WEBPAGE:
            structured_data.update(self._build_webpage_data(data, context))
        elif data_type == StructuredDataType.PRODUCT:
            structured_data.update(self._build_product_data(data, context))
        elif data_type == StructuredDataType.BREADCRUMB_LIST:
            structured_data.update(self._build_breadcrumb_data(data))
        elif data_type == StructuredDataType.LOCAL_BUSINESS:
            structured_data.update(self._build_local_business_data(data))
        
        return json.dumps(structured_data, indent=2)
    
    def generate_sitemap(self, entries: List[SitemapEntry]) -> str:
        """Generate XML sitemap from entries."""
        
        # Create root element
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        for entry in entries:
            url_elem = ET.SubElement(urlset, 'url')
            
            # Add URL
            loc = ET.SubElement(url_elem, 'loc')
            loc.text = entry.url
            
            # Add last modified
            if entry.last_modified:
                lastmod = ET.SubElement(url_elem, 'lastmod')
                lastmod.text = entry.last_modified.strftime('%Y-%m-%d')
            
            # Add change frequency
            changefreq = ET.SubElement(url_elem, 'changefreq')
            changefreq.text = entry.change_frequency.value
            
            # Add priority
            priority = ET.SubElement(url_elem, 'priority')
            priority.text = str(entry.priority)
        
        # Generate XML string
        return ET.tostring(urlset, encoding='unicode', xml_declaration=True)
    
    def generate_robots_txt(
        self,
        user_agents: List[str] = None,
        disallow_paths: List[str] = None,
        allow_paths: List[str] = None,
        sitemap_url: str = None
    ) -> str:
        """Generate robots.txt content."""
        
        if user_agents is None:
            user_agents = ["*"]
        
        if disallow_paths is None:
            disallow_paths = [
                "/admin",
                "/api",
                "/.well-known",
                "/private",
                "/temp"
            ]
        
        lines = []
        
        for user_agent in user_agents:
            lines.append(f"User-agent: {user_agent}")
            
            # Add disallow paths
            for path in disallow_paths:
                lines.append(f"Disallow: {path}")
            
            # Add allow paths if specified
            if allow_paths:
                for path in allow_paths:
                    lines.append(f"Allow: {path}")
            
            lines.append("")  # Empty line between user agents
        
        # Add sitemap URL
        if sitemap_url:
            lines.append(f"Sitemap: {sitemap_url}")
        else:
            lines.append(f"Sitemap: {self.base_url}sitemap.xml")
        
        return "\n".join(lines)
    
    def optimize_url_slug(self, text: str, max_length: int = 50) -> str:
        """Generate SEO-friendly URL slug from text."""
        if not text:
            return ""
        
        # Convert to lowercase
        slug = text.lower()
        
        # Replace special characters with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        # Truncate to max length
        if len(slug) > max_length:
            slug = slug[:max_length].rstrip('-')
        
        return slug
    
    def build_canonical_url(self, path: str) -> str:
        """Build canonical URL for a given path."""
        if path.startswith('http'):
            return path
        
        path = path.lstrip('/')
        return urljoin(self.base_url, path)
    
    def validate_meta_description(self, description: str) -> Dict[str, Any]:
        """Validate meta description for SEO best practices."""
        if not description:
            return {
                "valid": False,
                "issues": ["Description is empty"],
                "length": 0
            }
        
        length = len(description)
        issues = []
        
        if length < 120:
            issues.append("Description is too short (recommended: 120-160 characters)")
        elif length > 160:
            issues.append("Description is too long (recommended: 120-160 characters)")
        
        # Check for duplicate words
        words = description.lower().split()
        if len(words) != len(set(words)):
            issues.append("Description contains duplicate words")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "length": length,
            "recommended_length": "120-160 characters"
        }
    
    def _build_storefront_url(self, slug: str) -> str:
        """Build URL for a storefront."""
        return f"{self.base_url}storefronts/{slug}/page"
    
    def _build_product_url(self, storefront_slug: str, product_id: Union[str, int]) -> str:
        """Build URL for a product."""
        return f"{self.base_url}storefronts/{storefront_slug}/products/{product_id}"
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text for meta tags."""
        if not text:
            return []
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
            'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'is', 'was',
            'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'must', 'can', 'this', 'that', 'these', 'those', 'a', 'an'
        }
        
        # Extract words and filter
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = [word for word in words if word not in stop_words]
        
        # Get unique keywords while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:max_keywords]
    
    def _build_organization_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build Organization structured data."""
        org_data = {
            "name": data.get('name', 'InstantIn.me'),
            "url": data.get('url', self.base_url),
            "description": data.get('description', 'Create your instant storefront'),
        }
        
        if data.get('logo'):
            org_data["logo"] = data['logo']
        
        if data.get('social_media'):
            org_data["sameAs"] = data['social_media']
        
        return org_data
    
    def _build_person_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build Person structured data."""
        person_data = {
            "name": data.get('name', ''),
            "description": data.get('bio', data.get('description', '')),
        }
        
        if data.get('avatar_url'):
            person_data["image"] = data['avatar_url']
        
        if data.get('url'):
            person_data["url"] = data['url']
        
        if data.get('social_media'):
            person_data["sameAs"] = data['social_media']
        
        return person_data
    
    def _build_website_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build WebSite structured data."""
        return {
            "name": data.get('name', 'InstantIn.me'),
            "url": data.get('url', self.base_url),
            "description": data.get('description', 'Create your instant storefront'),
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"{self.base_url}search?q={{search_term_string}}",
                "query-input": "required name=search_term_string"
            }
        }
    
    def _build_webpage_data(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Build WebPage structured data."""
        webpage_data = {
            "name": data.get('title', ''),
            "description": data.get('description', ''),
            "url": data.get('url', ''),
        }
        
        if context and context.get('breadcrumbs'):
            webpage_data["breadcrumb"] = context['breadcrumbs']
        
        return webpage_data
    
    def _build_product_data(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Build Product structured data."""
        product_data = {
            "name": data.get('name', ''),
            "description": data.get('description', ''),
        }
        
        if data.get('image_url'):
            product_data["image"] = data['image_url']
        
        if data.get('price'):
            product_data["offers"] = {
                "@type": "Offer",
                "price": str(data['price']),
                "priceCurrency": data.get('currency', 'USD'),
                "availability": "https://schema.org/InStock"
            }
        
        if data.get('brand'):
            product_data["brand"] = {
                "@type": "Brand",
                "name": data['brand']
            }
        
        return product_data
    
    def _build_breadcrumb_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build BreadcrumbList structured data."""
        items = []
        
        for i, item in enumerate(data.get('items', []), 1):
            items.append({
                "@type": "ListItem",
                "position": i,
                "name": item.get('name', ''),
                "item": item.get('url', '')
            })
        
        return {
            "itemListElement": items
        }
    
    def _build_local_business_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build LocalBusiness structured data."""
        business_data = {
            "name": data.get('name', ''),
            "description": data.get('description', ''),
        }
        
        if data.get('address'):
            business_data["address"] = {
                "@type": "PostalAddress",
                "streetAddress": data['address'].get('street', ''),
                "addressLocality": data['address'].get('city', ''),
                "addressRegion": data['address'].get('state', ''),
                "postalCode": data['address'].get('zip', ''),
                "addressCountry": data['address'].get('country', 'US')
            }
        
        if data.get('phone'):
            business_data["telephone"] = data['phone']
        
        if data.get('hours'):
            business_data["openingHours"] = data['hours']
        
        return business_data
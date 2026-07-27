#!/usr/bin/env python3
"""
Lumina Playwright Scraper
Handles JavaScript-heavy sites: Instagram, TikTok, Facebook, LinkedIn
Usage: python3 playwright_scraper.py <platform> <keyword> <location> <limit>
Output: JSON array of leads to stdout
"""
import sys
import json
import asyncio
from playwright.async_api import async_playwright

PLATFORM_CONFIG = {
    'instagram': {
        'url': lambda kw: f'https://www.instagram.com/explore/tags/{kw}/',
        'timeout': 15000,
    },
    'tiktok': {
        'url': lambda kw: f'https://www.tiktok.com/search?q={kw}',
        'timeout': 10000,
    },
    'facebook': {
        'url': lambda kw, loc: f'https://www.facebook.com/search/pages?q={kw}%20{loc}',
        'timeout': 15000,
    },
    'linkedin': {
        'url': lambda kw, loc: f'https://www.linkedin.com/search/results/companies/?keywords={kw}%20{loc}',
        'timeout': 15000,
    },
    'youtube': {
        'url': lambda kw: f'https://www.youtube.com/results?search_query={kw}',
        'timeout': 10000,
    },
}

async def scrape_platform(platform, keyword, location, limit):
    config = PLATFORM_CONFIG.get(platform)
    if not config:
        return []

    if 'loc' in str(config['url'].__code__.co_varnames):
        url = config['url'](keyword, location)
    else:
        url = config['url'](keyword)

    leads = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=config['timeout'])
            await page.wait_for_timeout(3000)

            if platform == 'instagram':
                items = await page.query_selector_all('article a')
                for item in items[:limit]:
                    href = await item.get_attribute('href') or ''
                    text = await item.inner_text() or ''
                    if text.strip():
                        leads.append({
                            'source': 'instagram',
                            'business_name': text.strip()[:200],
                            'social_instagram': f'https://instagram.com{href}' if href else '',
                            'lead_score': 50,
                        })

            elif platform == 'tiktok':
                items = await page.query_selector_all('[data-e2e="search-card-user"]')
                for item in items[:limit]:
                    name_el = await item.query_selector('[data-e2e="user-title"]')
                    link_el = await item.query_selector('a[href*="/@"]')
                    name = await name_el.inner_text() if name_el else ''
                    href = await link_el.get_attribute('href') if link_el else ''
                    if name.strip():
                        leads.append({
                            'source': 'tiktok',
                            'business_name': name.strip(),
                            'social_tiktok': href if href.startswith('http') else f'https://tiktok.com{href}',
                            'lead_score': 50,
                        })

            elif platform == 'facebook':
                items = await page.query_selector_all('div[role="article"]')
                for item in items[:limit]:
                    text = await item.inner_text() or ''
                    name = text.split('\n')[0] if text else ''
                    if name.strip() and len(name) > 2:
                        leads.append({
                            'source': 'facebook',
                            'business_name': name.strip()[:200],
                            'lead_score': 50,
                        })

            elif platform == 'linkedin':
                items = await page.query_selector_all('.entity-result__title-text a')
                for item in items[:limit]:
                    name = await item.inner_text() or ''
                    href = await item.get_attribute('href') or ''
                    if name.strip():
                        leads.append({
                            'source': 'linkedin',
                            'business_name': name.strip()[:200],
                            'website': href,
                            'lead_score': 55,
                        })

            elif platform == 'youtube':
                items = await page.query_selector_all('#video-title')
                for item in items[:limit]:
                    name = await item.inner_text() or ''
                    href = await item.get_attribute('href') or ''
                    if name.strip():
                        leads.append({
                            'source': 'youtube',
                            'business_name': name.strip()[:200],
                            'social_youtube': f'https://youtube.com{href}' if href else '',
                            'lead_score': 50,
                        })

            await browser.close()
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        return []

    return leads

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(json.dumps({'error': 'Usage: playwright_scraper.py <platform> <keyword> <location> <limit>'}))
        sys.exit(1)

    platform = sys.argv[1]
    keyword = sys.argv[2]
    location = sys.argv[3] if len(sys.argv) > 3 else ''
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10

    leads = asyncio.run(scrape_platform(platform, keyword, location, limit))
    print(json.dumps(leads))

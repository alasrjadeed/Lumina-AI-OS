#!/usr/bin/env python3
"""
Lumina Fast HTTP Scraper
Handles simple HTML sites: classifieds, directories, business listings
Usage: python3 fast_scraper.py <platform> <keyword> <location> <limit>
Output: JSON array of leads to stdout
"""
import sys
import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser

class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.texts = []
        self.current_tag = None
        self.current_text = ''
        self.current_href = ''

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.current_tag = tag
        if tag == 'a':
            self.current_href = attrs_dict.get('href', '')
            self.current_text = ''

    def handle_data(self, data):
        if self.current_tag == 'a':
            self.current_text += data

    def handle_endtag(self, tag):
        if tag == 'a':
            if self.current_text.strip() and self.current_href:
                self.links.append(self.current_href)
                self.texts.append(self.current_text.strip())
            self.current_tag = None
            self.current_text = ''
            self.current_href = ''

def fetch_html(url):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0'
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception:
        return ''

def extract_emails(text):
    return list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)))

def extract_phones(text):
    return list(set(re.findall(r'\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{2,4}', text)))

PLATFORM_URLS = {
    'expatriates': lambda kw, loc: f'https://www.expatriates.com/classifieds/{loc.lower()}/{urllib.parse.quote(kw.lower())}/',
    'opensooq': lambda kw, loc: f'https://{loc.lower()}.opensooq.com/en/search?q={urllib.parse.quote(kw)}',
    'olx': lambda kw, loc: f'https://{loc.lower()}.olx.com/en/search/?q={urllib.parse.quote(kw)}',
    'dubizzle': lambda kw, loc: f'https://www.dubizzle.com/en/search/?query={urllib.parse.quote(kw)}',
    'haraj': lambda kw, loc: f'https://www.haraj.com.sa/search/?query={urllib.parse.quote(kw)}',
    'bayut': lambda kw, loc: f'https://www.bayut.com/to-rent/?q={urllib.parse.quote(kw)}',
    'arabiantalks': lambda kw, loc: f'https://www.arabiantalks.com/search?q={urllib.parse.quote(kw)}',
    'dcciinfo': lambda kw, loc: f'https://dcciinfo.com/search?q={urllib.parse.quote(kw)}',
    'abcgcc': lambda kw, loc: f'https://abc-gcc.net/search?q={urllib.parse.quote(kw)}',
    'bahrainyellow': lambda kw, loc: f'https://www.bahrainyellowpages.com/search/{urllib.parse.quote(kw)}',
    'bayt': lambda kw, loc: f'https://www.bayt.com/en/search/?q={urllib.parse.quote(kw)}',
    'gulftalent': lambda kw, loc: f'https://www.gulftalent.com/search/jobs?q={urllib.parse.quote(kw)}',
}

def scrape_platform(platform, keyword, location, limit):
    url_builder = PLATFORM_URLS.get(platform)
    if not url_builder:
        return []

    loc = location or 'bahrain'
    url = url_builder(keyword, loc)
    html = fetch_html(url)
    if not html:
        return []

    parser = LinkExtractor()
    parser.feed(html)

    leads = []
    seen = set()
    kw_parts = [w.lower() for w in keyword.lower().split()] if keyword else []

    for i, (href, text) in enumerate(zip(parser.links, parser.texts)):
        if len(leads) >= limit:
            break
        if len(text) < 3 or text in seen:
            continue

        if kw_parts:
            text_lower = text.lower()
            if not any(kw in text_lower for kw in kw_parts):
                continue

        seen.add(text)

        full_url = href
        if not href.startswith('http'):
            domain = url.split('/')[2]
            full_url = f'https://{domain}{href}' if href.startswith('/') else f'https://{domain}/{href}'

        leads.append({
            'source': platform,
            'business_name': text[:200],
            'website': full_url,
            'category': keyword,
            'country': location,
            'lead_score': 50,
        })

    return leads

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(json.dumps({'error': 'Usage: fast_scraper.py <platform> <keyword> <location> <limit>'}))
        sys.exit(1)

    platform = sys.argv[1]
    keyword = sys.argv[2]
    location = sys.argv[3] if len(sys.argv) > 3 else ''
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10

    leads = scrape_platform(platform, keyword, location, limit)
    print(json.dumps(leads))

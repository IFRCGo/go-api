import json
import time
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin

import django
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from playwright.sync_api import sync_playwright

from api.models import ItemCodeMapping

if not settings.configured:
    django.setup()


class RedCrossItemScraper:
    def __init__(self, base_url: str = "https://itemscatalogue.redcross.int"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 "
                    "Safari/537.36"
                )
            }
        )

    def fetch_page_with_scrolling(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page using Playwright and scroll to load all dynamic content"""
        try:
            print(f"Fetching (with JS rendering): {url}")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle")

                last_height = page.evaluate("document.body.scrollHeight")
                while True:
                    page.evaluate("window.scrollBy(0, window.innerHeight)")
                    time.sleep(0.5)

                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

                html_content = page.content()
                browser.close()

                soup = BeautifulSoup(html_content, "html.parser")
                return soup

        except Exception as e:
            print(f"Error fetching page with Playwright: {e}")
            return None

    def fetch_page(self, url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
        """Fetch a page using requests (faster, no JS rendering)"""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            return soup

        except requests.exceptions.RequestException as e:
            print(f"Error fetching page: {e}")
            return None

    def extract_top_level_categories(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        categories = []

        form = soup.find("form", {"name": "aspnetForm"})
        if not form:
            print("aspnetForm not found")
            return categories

        links = form.find_all("a", class_="col-md-12 col-sm-7 col-xs-9")
        for link in links:
            title = link.get("title", "").strip().upper()
            href = link.get("href", "")

            if title == "GREEN" or "green--" in href.lower():
                print(f"Skipping: {title}")
                continue

            if href and ".aspx" in href:
                full_url = urljoin(self.base_url, href)
                categories.append({"title": title, "url": full_url})
                print(f"Found top-level category: {title} - {full_url}")

        return categories

    def extract_product_urls_from_container(self, soup: BeautifulSoup) -> List[str]:
        urls = []
        seen_urls = set()

        form = soup.find("form", {"name": "aspnetForm"})
        if not form:
            print("  DEBUG: aspnetForm not found")
            return urls

        products_div = form.find("div", class_="container products")

        if not products_div:
            print("  DEBUG: 'container products' div not found in aspnetForm")
            return urls

        print("  DEBUG: Found products container")

        product_divs = products_div.find_all("div", class_=lambda x: x and "product" in x and "grid-group-item" in x)
        print(f"  DEBUG: Found {len(product_divs)} product grid items")

        for product_div in product_divs:
            link = product_div.find("a", href=True)
            if link:
                href = link.get("href", "").strip()
                if href:
                    full_url = urljoin(self.base_url, href)

                    if full_url not in seen_urls:
                        seen_urls.add(full_url)
                        urls.append(full_url)

        print(f"  DEBUG: Extracted {len(urls)} unique product URLs")
        return urls

    def collect_products_from_top_level_categories(self, homepage_url: str) -> Dict:
        print("Fetching homepage and extracting top-level categories...")
        homepage_soup = self.fetch_page(homepage_url)
        if not homepage_soup:
            return {}

        top_level_categories = self.extract_top_level_categories(homepage_soup)
        print(f"\nFound {len(top_level_categories)} top-level categories (excluding GREEN)")

        print("\nScraping product URLs from each top-level category page...")

        all_urls = []
        products_by_category = {}

        for i, category in enumerate(top_level_categories, 1):
            category_title = category["title"]
            category_url = category["url"]

            print(f"\n[{i}/{len(top_level_categories)}] Processing: {category_title}")
            print(f"  URL: {category_url}")

            soup = self.fetch_page_with_scrolling(category_url)
            if not soup:
                continue

            urls = self.extract_product_urls_from_container(soup)
            if urls:
                print(f"Found {len(urls)} URLs")
                products_by_category[category_title] = urls
                all_urls.extend(urls)
            else:
                print("No URLs found")

            time.sleep(1)

        return {
            "all_urls": all_urls,
            "products_by_category": products_by_category,
            "total_categories": len(top_level_categories),
            "total_urls": len(all_urls),
            "unique_urls": len(set(all_urls)),
        }

    def extract_codes_from_product_page(self, soup: BeautifulSoup) -> List[str]:
        codes: List[str] = []
        seen = set()

        table_div = soup.find("div", id="MP_CPH_Centre_div_product_table")
        if not table_div:
            return codes

        table = table_div.find("table", class_="technicalTable")
        if not table:
            return codes

        tbody = table.find("tbody")
        if not tbody:
            return codes

        rows = tbody.find_all("tr")

        for row in rows:
            # Pattern 1: spans containing codes
            code_spans = row.find_all("span", id=lambda x: x and "rp_code" in x)
            for span in code_spans:
                code = span.get_text(strip=True)
                if code and code not in seen:
                    seen.add(code)
                    codes.append(code)

            # Pattern 2: label-value pair structure
            # Find divs with class 'label-table' that contain "Code"
            label_divs = row.find_all("div", class_="label-table")
            for label_div in label_divs:
                label_text = label_div.get_text(strip=True)
                if label_text.lower() == "code":
                    # Find the next sibling div with class 'value-table'
                    value_div = label_div.find_next_sibling("div", class_="value-table")
                    if value_div:
                        code = value_div.get_text(strip=True)
                        if code and code not in seen:
                            seen.add(code)
                            codes.append(code)

        return codes

    def build_code_to_url_mapping(self, urls: List[str]) -> Dict[str, any]:
        code_to_url: Dict[str, str] = {}
        missing_codes: List[str] = []

        print(f"\nBuilding code to URL mapping for {len(urls)} URLs...")

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Processing: {url}")

            soup = self.fetch_page(url)
            if not soup:
                print("Failed to fetch page")
                missing_codes.append(url)
                continue

            codes = self.extract_codes_from_product_page(soup)
            if codes:
                print(f"Found {len(codes)} code(s): {', '.join(codes)}")
                for code in codes:
                    code_to_url[code] = url
            else:
                print("No codes found")
                missing_codes.append(url)

            time.sleep(0.5)

        return {"code_to_url": code_to_url, "missing_code_urls": missing_codes}

    def save_to_json(self, data: Union[Dict, List], filename: str = "scraped_data.json"):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\nData saved to {filename}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")

    def save_to_database(self, code_to_url_mapping: Dict[str, str], clear_existing: bool = True):
        """Save code to URL mappings to the ItemCodeMapping model"""
        try:
            if clear_existing:
                print("Clearing existing mappings...")
                ItemCodeMapping.objects.all().delete()

            print(f"Saving {len(code_to_url_mapping)} mappings to database...")

            # Prepare bulk create objects
            mappings = [ItemCodeMapping(code=code, url=url) for code, url in code_to_url_mapping.items()]

            # Bulk create for efficiency
            ItemCodeMapping.objects.bulk_create(mappings, batch_size=1000)

            print(f"Successfully saved {len(mappings)} mappings to database")
        except Exception as e:
            print(f"Error saving to database: {e}")


def main():
    scraper = RedCrossItemScraper()

    print("=" * 80)
    print("Collecting all URLs from top-level categories")
    print("=" * 80)

    homepage_url = "https://itemscatalogue.redcross.int/index.aspx"

    result = scraper.collect_products_from_top_level_categories(homepage_url)

    print("\n" + "=" * 80)
    print("URL COLLECTION SUMMARY")
    print("=" * 80)
    print(f"Top-level categories processed: {result['total_categories']}")
    print(f"Total URLs found: {result['total_urls']}")
    print(f"Unique URLs: {result['unique_urls']}")

    print("\nURLs by category:")
    for category, urls in result.get("products_by_category", {}).items():
        print(f"  {category}: {len(urls)} URLs")

    scraper.save_to_json(result["all_urls"], "product_urls.json")
    print("\nSaved: product_urls.json")

    print("\n" + "=" * 80)
    print("Building Code to URL Mapping")
    print("=" * 80)

    code_results = scraper.build_code_to_url_mapping(result["all_urls"])

    print("\n" + "=" * 80)
    print("CODE MAPPING SUMMARY")
    print("=" * 80)
    print(f"Total unique codes found: {len(code_results['code_to_url'])}")
    print(f"URLs with missing codes: {len(code_results['missing_code_urls'])}")

    # Save to JSON files
    scraper.save_to_json(code_results["code_to_url"], "code_to_url.json")
    scraper.save_to_json(code_results["missing_code_urls"], "missing_code_urls.json")

    # Save to database
    scraper.save_to_database(code_results["code_to_url"])

    print("\n" + "=" * 80)
    print("Saved: code_to_url.json, missing_code_urls.json, and ItemCodeMapping model")
    print("=" * 80)


if __name__ == "__main__":
    main()

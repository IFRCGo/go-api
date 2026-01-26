import json
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class RedCrossItemScraper:
    def __init__(self, base_url: str = "https://itemscatalogue.redcross.int"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def fetch_page(self, url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            return soup

        except requests.exceptions.RequestException as e:
            print(f"Error fetching page: {e}")
            return None

    def extract_product_data(self, soup: BeautifulSoup) -> Dict:
        product_data = {
            "title": None,
            "product_code": None,
            "description": None,
            "weight": None,
            "last_updated": None,
            "category_path": [],
            "general_info": [],
            "specifications": [],
            "images": [],
            "documents": [],
        }

        title_tag = soup.find("h1") or soup.find("h2")
        if title_tag:
            product_data["title"] = title_tag.get_text(strip=True)
            print(f"Found title: {product_data['title']}")

        table = soup.find("table")
        if table:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 3:
                    code = cells[0].get_text(strip=True)
                    if code and not code.isspace():
                        product_data["product_code"] = code

                    desc = cells[1].get_text(strip=True)
                    if desc:
                        product_data["description"] = desc

                    for cell in cells[2:]:
                        text = cell.get_text(strip=True)
                        if "kg" in text.lower():
                            product_data["weight"] = text
                            break

        for element in soup.find_all(string=lambda text: text and "last updated" in text.lower()):
            parent_text = element.strip()
            product_data["last_updated"] = parent_text
            break

        nav_links = soup.find_all("a", href=True)
        for link in nav_links:
            href = link["href"]
            text = link.get_text(strip=True)
            if "--" in href and text and len(text) > 2:
                if text.upper() == text:
                    product_data["category_path"].append(text)

        paragraphs = soup.find_all("p")
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 20:
                product_data["general_info"].append(text)

        lists = soup.find_all(["ul", "ol"])
        for lst in lists:
            items = lst.find_all("li")
            for item in items:
                text = item.get_text(strip=True)
                if text:
                    product_data["specifications"].append(text)

        images = soup.find_all("img")
        for img in images:
            src = img.get("src")
            alt = img.get("alt", "")
            if src:
                full_url = urljoin(self.base_url, src)
                product_data["images"].append({"url": full_url, "alt": alt})

        doc_extensions = [".pdf", ".doc", ".docx", ".xls", ".xlsx"]
        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            text = link.get_text(strip=True)

            if any(href.lower().endswith(ext) for ext in doc_extensions):
                full_url = urljoin(self.base_url, href)
                product_data["documents"].append({"url": full_url, "name": text or href.split("/")[-1]})

        return product_data

    def scrape_product(self, url: str) -> Optional[Dict]:
        soup = self.fetch_page(url)
        if not soup:
            return None

        product_data = self.extract_product_data(soup)
        product_data["url"] = url

        return product_data

    def scrape_category(self, category_url: str, max_items: int = 10) -> List[Dict]:
        soup = self.fetch_page(category_url)
        if not soup:
            return []

        product_links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if ".aspx" in href and "--" in href:
                full_url = urljoin(self.base_url, href)
                if full_url not in product_links:
                    product_links.append(full_url)

        print(f"Found {len(product_links)} product links")

        products = []
        for i, product_url in enumerate(product_links[:max_items]):
            print(f"\nScraping product {i+1}/{min(len(product_links), max_items)}")
            product_data = self.scrape_product(product_url)
            if product_data:
                products.append(product_data)

            time.sleep(1)

        return products

    def save_to_json(self, data: Dict or List, filename: str = "scraped_data.json"):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\nData saved to {filename}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")


def main():
    scraper = RedCrossItemScraper()

    print("=" * 80)
    print("Scraping page")
    print("=" * 80)

    product_url = "https://itemscatalogue.redcross.int/wash--6/sanitation--22/excreta-disposal--35/latrine-rapid-infrastructure--WSANLATR.aspx"

    product_data = scraper.scrape_product(product_url)

    if product_data:
        print("\n" + "=" * 80)
        print("SCRAPED PRODUCT DATA")
        print("=" * 80)
        print(json.dumps(product_data, indent=2, ensure_ascii=False))

        scraper.save_to_json(product_data, "product_data.json")
    else:
        print("Failed to scrape product data")


if __name__ == "__main__":
    main()

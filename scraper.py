import random
import time
import json
import os
import requests
from bs4 import BeautifulSoup
import re

# Constants
BASE_URL = "https://www.amazon.com/surfboards/s?k=surfboards"
OUTPUT_FOLDER = "amazon_products"
SUMMARY_FILE = "products_summary.json"

# Custom HTTP headers to mimic a browser request
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.5735.199 Safari/537.36"
    ),
    "sec-ch-ua": "\"Google Chrome\";v=\"116\", \"Chromium\";v=\"116\", \"Not_A.Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": "\"Android\"",
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Referer": "https://www.amazon.com/",
}

class Scraper:
    """
    Scraper class to fetch product details from Amazon and update progress via a UI callback.
    """

    def __init__(self, update_progress_callback):
        """
        Initialize the scraper.

        Args:
            update_progress_callback (callable): A function to call with scraping progress updates.
        """
        self.update_progress_callback = update_progress_callback

    def fetch_page_soup(self, url):
        """
        Fetch the HTML content of a page and return a BeautifulSoup object.

        Args:
            url (str): URL to fetch.

        Returns:
            BeautifulSoup | None: Parsed page content or None if request fails.
        """
        try:
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                return BeautifulSoup(response.text, "html.parser")
        except requests.exceptions.RequestException:
            # Silently ignore network errors
            pass
        return None

    def save_product_data(self, product_data, index):
        """
        Save product details to a local JSON file.

        Args:
            product_data (dict): Extracted product information.
            index (int): Product index used for filename.
        """
        if not os.path.exists(OUTPUT_FOLDER):
            os.makedirs(OUTPUT_FOLDER)
        filename = os.path.join(OUTPUT_FOLDER, f"product_{index}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)

    def extract_product_links(self, soup):
        """
        Extract product detail page links from a search result page.

        Args:
            soup (BeautifulSoup): Parsed HTML of the search result page.

        Returns:
            list[str]: List of full product URLs.
        """
        if soup is None:
            return []

        return [
            "https://www.amazon.com" + item.find("a", class_="a-link-normal s-no-outline")["href"]
            for item in soup.find_all("div", {"data-component-type": "s-search-result"})
            if item.find("a", class_="a-link-normal s-no-outline")
        ]
       
 # Extract the shipping price from a string containing the shipping info.
    def extract_shipping_price(self, shipping_text):       
        match = re.search(r'\$[\d,]+\.\d{2}', shipping_text)
        if match:
            return match.group(0)
        return "Shipping info not available"

    def extract_product_details(self, soup):
        """
        Extract relevant product details from a product page.

        Args:
            soup (BeautifulSoup): Parsed HTML of a product detail page.

        Returns:
            dict: Product information (name, price, shipping, seller, brand).
        """
        title_tag = soup.find(id="productTitle")
        price_tag = soup.select_one("span.a-price span.a-offscreen")
        shipping_tag = soup.find("span", class_="a-size-base a-color-secondary")
        seller_name = soup.find('a', {'id': 'sellerProfileTriggerId'})
        brand = soup.find(class_="a-size-base po-break-word")
        
        shipping_price = (
            self.extract_shipping_price(shipping_tag.get_text(strip=True)) 
            if shipping_tag else "Shipping info not available"
        )

        return {
            "product_name": title_tag.get_text(strip=True) if title_tag else None,
            "price": price_tag.get_text(strip=True) if price_tag else "Price shown at checkout.",
            "shipping_price": shipping_price,
            "seller_name": seller_name.get_text(strip=True) if seller_name else "Amazon.com",
            "brand": brand.get_text(strip=True) if brand else "Amazon",
        }

    def begin_scraping_process(self):
        """
        Start the scraping process.

        - Iterates through Amazon search result pages.
        - Extracts product links and details.
        - Saves data to disk.
        - Notifies the UI with progress updates.
        - Stops after 50 products are collected or pages are exhausted.
        """
        collected_products = 0     # Total products collected
        page_number = 1            # Start at page 1
        all_products = []          # Summary data

        while collected_products < 50:
            # Construct the URL for the current page
            url = f"{BASE_URL}&page={page_number}"
            soup = self.fetch_page_soup(url)

            if not soup:
                page_number += 1
                continue

            # Extract links to individual product pages
            product_links = self.extract_product_links(soup)
            if not product_links:
                page_number += 1
                continue

            # Loop through each product link and scrape details
            for link in product_links:
                if collected_products >= 50:
                    break

                product_soup = self.fetch_page_soup(link)
                if not product_soup:
                    continue

                product_data = self.extract_product_details(product_soup)
                if not product_data.get("product_name"):
                    continue  # Skip incomplete entries

                collected_products += 1
                self.save_product_data(product_data, collected_products)
                all_products.append(product_data)

                # Update summary file
                try:
                    with open(SUMMARY_FILE, "w", encoding="utf-8") as summary_file:
                        json.dump(all_products, summary_file, indent=4)
                except Exception:
                    # If file write fails, silently continue
                    pass

                # Prepare a short message for the UI
                short_title = (
                    product_data["product_name"][:50] + "..."
                    if len(product_data["product_name"]) > 50
                    else product_data["product_name"]
                )

                # Send progress update to UI
                self.update_progress_callback(collected_products, f"Just scraped: {short_title}")

                # Wait randomly to mimic human behavior
                time.sleep(random.uniform(5.0, 12.0))

            # Move to the next search results page
            page_number += 1

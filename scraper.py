import random
import time
import json
import os
import requests
from bs4 import BeautifulSoup

# Constants for the base URL of the Amazon search page, output folder, and file names
BASE_URL = "https://www.amazon.com/surfboards/s?k=surfboards"
OUTPUT_FOLDER = "amazon_products"  # Folder where product JSON files will be saved
SUMMARY_FILE = "products_summary.json"  # File where summary of all products will be saved
HEADERS = {  # Headers for the HTTP requests to mimic a browser request
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.5735.199 Safari/537.36"
    ),
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Referer": "https://www.amazon.com/",
}

class Scraper:
    """
    Scraper class handles the web scraping logic for Amazon product data.
    The scraper extracts information like product name, price, shipping, seller, and brand from the Amazon surfboards search page.
    """

    def __init__(self, update_progress_callback):
        """
        Constructor to initialize the Scraper instance.
        
        Parameters:
        update_progress_callback (function): Callback function to update progress on the UI/console.

        The constructor accepts a callback function which will be called to update progress after scraping each product.
        """
        self.update_progress_callback = update_progress_callback

    def fetch_page_soup(self, url):
        """
        Fetches the HTML content of a page and parses it with BeautifulSoup.

        Parameters:
        url (str): The URL of the page to scrape.

        Returns:
        BeautifulSoup object: Parsed HTML content of the page if successful, else None.
        """
        try:
            # Make an HTTP GET request to the provided URL
            response = requests.get(url, headers=HEADERS)
            
            # If the request is successful (HTTP status code 200)
            if response.status_code == 200:
                return BeautifulSoup(response.text, "html.parser")
            else:
                # Log a warning if status code is not 200 (OK)
                print(f"[Warning] Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            # Handle errors that occur during the HTTP request (e.g., connection errors)
            print(f"[Error] {e}")
        
        # Return None if there was an error or invalid response
        return None

    def save_product_data(self, product_data, index):
        """
        Saves the product data to a JSON file.

        Parameters:
        product_data (dict): The product information as a dictionary.
        index (int): The index of the product to be used in the filename (e.g., product_1.json).
        
        The method will create a directory for saving the JSON files if it does not exist.
        Each product will be saved in a separate JSON file.
        """
        if not os.path.exists(OUTPUT_FOLDER):
            os.makedirs(OUTPUT_FOLDER)  # Create the output folder if it doesn't exist
            
        filename = os.path.join(OUTPUT_FOLDER, f"product_{index}.json")  # Define the filename
        
        with open(filename, "w", encoding="utf-8") as f:
            # Write the product data to the JSON file
            json.dump(product_data, f, ensure_ascii=False, indent=2)
        
        print(f"[Info] Saved: {filename}")  # Print a message confirming the save

    def extract_product_links(self, soup):
        """
        Extracts product links from the Amazon search result page.

        Parameters:
        soup (BeautifulSoup): The parsed HTML content of the Amazon search results page.

        Returns:
        list: A list of product URLs.
        """
        if soup is None:
            return []
        
        # Find all product items on the page and extract their links
        return [
            "https://www.amazon.com" + item.find("a", class_="a-link-normal s-no-outline")["href"]
            for item in soup.find_all("div", {"data-component-type": "s-search-result"})
            if item.find("a", class_="a-link-normal s-no-outline")
        ]

    def extract_product_details(self, soup):
        """
        Extracts product details such as name, price, shipping, seller, and brand.

        Parameters:
        soup (BeautifulSoup): The parsed HTML content of the product page.

        Returns:
        dict: A dictionary containing product details.
        """
        # Extract the relevant details using BeautifulSoup
        title_tag = soup.find(id="productTitle")
        price_tag = soup.select_one("span.a-price span.a-offscreen")
        shipping_tag = soup.find('b', text='FREE Shipping')
        seller_name = soup.find('a', {'id': 'sellerProfileTriggerId'})
        brand = soup.find(class_="a-size-base po-break-word")

        return {
            "product_name": title_tag.get_text(strip=True) if title_tag else None,
            "price": price_tag.get_text(strip=True) if price_tag else "Price shown at checkout.",
            "shipping_price": shipping_tag.get_text(strip=True) if shipping_tag else "Free Shipping",
            "seller_name": seller_name.get_text(strip=True) if seller_name else "Amazon.com",
            "brand": brand.get_text(strip=True) if brand else "Amazon",
        }

    def begin_scraping_process(self):
        """
        Starts the scraping process by navigating through Amazon search result pages and scraping product details.

        The method will continue scraping until 50 products are collected.
        After each product is scraped, the data is saved, and a progress update is made.
        """
        collected_products = 0
        page_number = 1
        all_products = []

        while collected_products < 50:
            # Construct the URL for the current page of search results
            url = f"{BASE_URL}&page={page_number}"
            soup = self.fetch_page_soup(url)

            if not soup:
                # If there's an error or no soup returned, skip to the next page
                page_number += 1
                continue

            # Extract product links from the current search page
            product_links = self.extract_product_links(soup)
            if not product_links:
                page_number += 1
                continue

            # Iterate over each product link and scrape product details
            for link in product_links:
                if collected_products >= 50:
                    break  # Stop scraping once 50 products are collected
                
                product_soup = self.fetch_page_soup(link)  # Get the product page's soup
                if not product_soup:
                    continue  # Skip if the product page could not be loaded

                product_data = self.extract_product_details(product_soup)  # Extract product data
                if not product_data.get("product_name"):
                    continue  # Skip if no product name was found

                collected_products += 1
                self.save_product_data(product_data, collected_products)  # Save product data
                all_products.append(product_data)

                # Save the summary file with all collected product data
                try:
                    with open(SUMMARY_FILE, "w") as summary_file:
                        json.dump(all_products, summary_file, indent=4)
                except Exception as e:
                    print(f"Error writing summary JSON file: {e}")

                # Update progress for the user interface or console
                short_title = (product_data["product_name"][:50] + "...") if len(product_data["product_name"]) > 50 else product_data["product_name"]
                self.update_progress_callback(collected_products, f"Just scraped: {short_title}")

                # Sleep for a random time between 2 and 6 seconds to avoid overloading Amazon's servers
                time.sleep(random.uniform(2.0, 6.0))

            page_number += 1  # Move to the next page of search results

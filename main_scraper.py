from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import os
import json
import time

# Load keywords from pitch deck verticals
with open('keywords.json', 'r') as file:
    keywords = json.load(file)
print("✅ Keywords loaded!")

# Define URLs for Grants and Tenders/EOIs
URLS = {
    "Grants": "https://ngobox.org/grant_announcement_listing.php",
    "TendersAndEOIs": "https://ngobox.org/rfp_eoi_listing.php"
}

# Scraping Function with Enhanced Debugging
def fetch_opportunities(url, type_name):
    print(f"🔍 Scraping {type_name} from {url}")
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(url)
        time.sleep(10)  # Wait for page to load
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        items = soup.find_all('div', class_=lambda x: x and ('col-md-6' in x or 'card' in x or 'listing' in x))
        print(f"Found {len(items)} items with matching classes")

        listings = []
        for item in items:
            title_tag = item.find('a', href=True)
            title = title_tag.get_text(strip=True) if title_tag else 'N/A'
            if title_tag and title_tag['href']:
                href = title_tag['href'].strip()
                link = href if href.startswith('http') else f"https://ngobox.org/{href}" if href.startswith('/') else f"https://ngobox.org/{href}"
            else:
                link = url
            print(f"Title: {title}, Final Link: {link}")
            
            desc_tag = item.find('p') or item.find('div', recursive=False)
            desc = desc_tag.get_text(strip=True) if desc_tag else 'N/A'
            print(f"Description: {desc}")
            
            matched_vertical = None
            for vertical, words in keywords.items():
                if any(word.lower() in (title + desc).lower() for word in words):
                    matched_vertical = vertical.capitalize()
                    break
            
            # Only include rows with a valid matched_vertical (exclude unclassified)
            if matched_vertical:
                listings.append({
                    "Type": type_name,
                    "Title": title,
                    "Description": desc,
                    "Matched_Vertical": matched_vertical,
                    "Link": link
                })
                print(f"✅ Matched {title} to {matched_vertical}")
        print(f"✅ Found {len(listings)} relevant {type_name.lower()}!")
        return listings
    except Exception as e:
        print(f"❌ Failed to fetch {type_name}: {e}")
        return []

# Collect and save data to XLSX with error handling
def run_scraper():
    all_data = []
    for name, url in URLS.items():
        data = fetch_opportunities(url, name)
        all_data.extend(data)
        if not data:
            print(f"⚠️ No relevant {name.lower()} found.")
    
    if not os.path.exists('output'):
        try:
            os.makedirs('output')
        except PermissionError as e:
            print(f"❌ Permission denied while creating 'output' directory: {e}")
            return
    
    if all_data:
        try:
            df = pd.DataFrame(all_data)
            # Add Clickable_Link column with HYPERLINK formula
            df['Clickable_Link'] = '=HYPERLINK("' + df['Link'] + '", "' + df['Title'] + '")'
            # Select desired columns
            df = df[['Type', 'Title', 'Description', 'Matched_Vertical', 'Clickable_Link']]
            # Save as XLSX to preserve formulas
            df.to_excel('output/relevant_grants.xlsx', index=False, engine='openpyxl')
            print("✅ Scraping completed and results saved as XLSX!")
        except PermissionError as e:
            print(f"❌ Permission denied while saving 'output/relevant_grants.xlsx': {e}")
        except Exception as e:
            print(f"❌ Error saving XLSX: {e}")
    else:
        print("⚠️ No relevant data found to save.")

# Run immediately and exit
if __name__ == "__main__":
    run_scraper()


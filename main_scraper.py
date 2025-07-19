import os, time, json, re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from openpyxl import load_workbook
from openpyxl.styles import Alignment

# === Load keywords ===
with open('keywords.json', 'r') as file:
    keywords = json.load(file)

priority = ["Governance", "Learning", "Safety", "Climate"]

URLS = {
    "Grants": "https://ngobox.org/grant_announcement_listing.php",
    "Tenders": "https://ngobox.org/rfp_eoi_listing.php"
}

custom_keywords = [
    "Selection Criteria", "Evaluation & Follow-Up", "Application Guidelines", "Eligible Applicants:", "Scope of Work:",
    "Proposal Requirements: (Strictly follow the format)", "Evaluation Criteria:", "Submission Details:",
    "Eligible Entities", "How to apply", "Purpose of RFP", "Proposal Guidelines", "Eligibility Criteria:",
    "Application must include:", "Eligibility", "Submission of Tender:", "Technical Bid-", "Who Can Apply:",
    "Documents Required", "Expectation:", "Eligibility Criterion:", "Submission terms:", "Vendor Qualifications",
    "To apply", "To know about the eligibility criteria:", "The agency's specific responsibilities include –",
    "SELCO Foundation will be responsible for:", "Partner Eligibility CriteriaProposal Submission Requirements",
    "Proposal Evaluation Criteria", "Eligibility Criteria for CSOs to be part of the programme:", "Pre-Bid Queries:",
    "Response to Pre-Bid Queries:", "Submission of Bid:", "Applicant Profiles:", "What we like to see in grant applications:",
    "Research that is supported by the SVRI must:", "Successful projects are most often:", "Criteria for funding:",
    "Before you begin to write your proposal, consider that IEF prefers to fund:",
    "As you prepare your budget, these are some items that IEF will not fund:", "Proposal Requirements",
    "Evaluation Criteria", "Who Can Apply", "Organizational Profile", "Selection Process",
    "Proposal Submission Guidelines", "Terms and Conditions", "Security Deposit:",
    "Facilities and Support Offered under the call for proposal:"
]

def extract_description_after_apply_by(soup):
    h2_tags = soup.find_all('h2', class_='card-text')
    for h2 in h2_tags:
        strong = h2.find('strong')
        if strong and 'Apply By:' in strong.text:
            desc_parts = []
            for sibling in h2.find_all_next(['p', 'div'], limit=50):
                text = sibling.get_text(" ", strip=True)
                if text:
                    desc_parts.append(text)
            return "\n\n".join(desc_parts)
    return 'N/A'

def extract_relevant_sections_from_description_html(soup):
    page_sections = []
    section_keywords = [kw.strip().lower().rstrip(":") for kw in custom_keywords]
    stop_phrases = ["contact", "important dates", "terms and conditions", "disclaimer", "about the organization"]

    all_tags = soup.find('body').find_all(['h1', 'h2', 'h3', 'h4', 'p', 'div', 'span'])

    i = 0
    while i < len(all_tags):
        tag = all_tags[i]
        text = tag.get_text(" ", strip=True).lower()
        matched_heading = next((k for k in section_keywords if k in text), None)

        if matched_heading:
            heading_label = all_tags[i].get_text(" ", strip=True).strip()
            section_block = [f"🔹 {heading_label}"]
            i += 1
            while i < len(all_tags):
                next_tag = all_tags[i]
                next_text = next_tag.get_text(" ", strip=True).lower().strip()
                if any(k in next_text for k in section_keywords) or any(stop in next_text for stop in stop_phrases):
                    break
                if len(next_text) > 5 and "subscribe" not in next_text:
                    section_block.append(next_tag.get_text(" ", strip=True).strip())
                i += 1
            page_sections.append("\n".join(section_block))
        else:
            i += 1

    if not page_sections:
        return "N/A"

    combined = "\n\n".join(page_sections)
    return combined[:1000]  # Limit to 1000 characters

def fetch_opportunities(type_name, base_url):
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    listings, seen_links = [], set()
    page = 1

    while True:
        url = f"{base_url}?page={page}"
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # ✅ Updated selector to include 'card-block'
        items = soup.find_all('div', class_=lambda x: x and any(cls in x for cls in ['col-md-6', 'card', 'listing', 'card-block']))
        if not items:
            break

        for item in items:
            a = item.find('a', href=True)
            if not a:
                continue

            href = a.get('href', '').strip()
            if href in ['', '#', 'javascript:void(0)']:
                continue

            title = a.get_text(strip=True)
            link = href if href.startswith('http') else f"https://ngobox.org/{href.lstrip('/')}"

            if link in seen_links:
                continue

            driver.get(link)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(1)

            detail_soup = BeautifulSoup(driver.page_source, 'html.parser')

            deadline = 'N/A'
            for tag in detail_soup.find_all('h2', class_='card-text'):
                strong = tag.find('strong')
                if strong and 'Apply By:' in strong.text:
                    deadline = tag.get_text(strip=True).replace('Apply By:', '').strip()
                    break

            description = extract_description_after_apply_by(detail_soup)
            how_to_apply = extract_relevant_sections_from_description_html(detail_soup)

            print(f"\n📄 {title}")
            print(f"➡️ How_to_Apply (Trimmed):\n{how_to_apply[:300]}...\n")

            text_blob = (title + " " + description + " " + how_to_apply).lower()
            matched_verticals = []
            for vertical in priority:
                for word in keywords.get(vertical, []):
                    if re.search(r'\b' + re.escape(word.lower()) + r'\b', text_blob):
                        matched_verticals.append(vertical)
                        break

            if matched_verticals:
                listings.append({
                    "Type": type_name,
                    "Title": title,
                    "Description": description,
                    "How_to_Apply": how_to_apply,
                    "Matched_Vertical": ", ".join(matched_verticals),
                    "Deadline": deadline,
                    "Link": link
                })

            seen_links.add(link)

        next_btn = soup.find('a', string=lambda s: s and 'next' in s.lower())
        if not next_btn:
            break
        page += 1

    driver.quit()
    return listings

def run_scraper():
    all_data = []
    for name, url in URLS.items():
        all_data.extend(fetch_opportunities(name, url))

    if not all_data:
        print("⚠️ No data to save.")
        return

    if not os.path.exists('output'):
        os.makedirs('output')

    df = pd.DataFrame(all_data)
    df = df[df['Link'].notna() & (df['Link'].str.strip() != '')]
    df['Clickable_Link'] = '=HYPERLINK("' + df['Link'] + '", "' + df['Title'] + '")'

    try:
        df['Deadline_Date'] = pd.to_datetime(df['Deadline'], format='%d %b %Y', errors='coerce')
    except:
        df['Deadline_Date'] = pd.NaT

    df = df.sort_values(['Deadline_Date'], na_position='last')
    df = df[['Type', 'Title', 'Description', 'How_to_Apply', 'Matched_Vertical', 'Deadline', 'Clickable_Link']]

    excel_path = 'output/relevant_grants.xlsx'
    df.to_excel(excel_path, index=False, engine='openpyxl')

    # Format Excel
    wb = load_workbook(excel_path)
    ws = wb.active
    for col, width in {'A': 20, 'B': 50, 'C': 80, 'D': 50, 'E': 30, 'F': 15, 'G': 50}.items():
        ws.column_dimensions[col].width = width
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            if cell.column_letter in ['C', 'D']:
                cell.alignment = Alignment(wrap_text=True, vertical='top')
            else:
                cell.alignment = Alignment(wrap_text=False, vertical='top')
    wb.save(excel_path)
    print(f"✅ Excel saved to {excel_path}")

if __name__ == "__main__":
    run_scraper()

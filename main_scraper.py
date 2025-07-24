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

def extract_description_after_apply_by(soup):
    h2_tags = soup.find_all('h2', class_='card-text')
    for h2 in h2_tags:
        strong = h2.find('strong')
        if strong and 'Apply By:' in strong.text:
            desc_parts = []
            seen_lines = set()
            for sibling in h2.find_all_next():
                if sibling.name == "div" and "row_section" in sibling.get("class", []):
                    b_tag = sibling.find("b")
                    if b_tag and b_tag.get_text(strip=True).lower() == "tags":
                        break
                text_content = sibling.get_text(separator='\n', strip=True)
                lines = text_content.split('\n')
                unique_lines = [line.strip() for line in lines if line.strip() and line.strip() not in seen_lines]
                if unique_lines:
                    seen_lines.update(unique_lines)
                    new_sibling = BeautifulSoup(f"<div>{text_content}</div>", 'html.parser').find('div')
                    new_text = '\n'.join(unique_lines)
                    new_sibling.string = new_text
                    desc_parts.append(str(new_sibling).replace('<div>', '').replace('</div>', ''))
            return "\n".join(desc_parts)
    return ''

def extract_how_to_apply_from_html(description):
    if not description or not isinstance(description, str):
        return "N/A"

    custom_keywords = [
        "Selection Criteria", "Evaluation & Follow-Up", "Application Guidelines", "Eligible Applicants:",
        "Scope of Work:", "Proposal Requirements", "Evaluation Criteria", "Submission Details", "Eligible Entities",
        "How to apply", "Purpose of RFP", "Proposal Guidelines", "Eligibility Criteria", "Application must include:",
        "Eligibility", "Submission of Tender:", "Technical Bid-", "Who Can Apply", "Documents Required", "Expectation:",
        "Eligibility Criterion:", "Submission terms:", "Vendor Qualifications", "To apply",
        "To know about the eligibility criteria:", "The agency's specific responsibilities include –",
        "SELCO Foundation will be responsible for:", "Partner Eligibility Criteria", "Proposal Submission Requirements",
        "Proposal Evaluation Criteria", "Eligibility Criteria for CSOs to be part of the programme:", "Pre-Bid Queries:",
        "Response to Pre-Bid Queries:", "Submission of Bid:", "Applicant Profiles:", "What we like to see in grant applications:",
        "Research that is supported by the SVRI must:", "Successful projects are most often:", "Criteria for funding:",
        "Before you begin to write your proposal, consider that IEF prefers to fund:",
        "As you prepare your budget, these are some items that IEF will not fund:", "Organizational Profile",
        "Selection Process", "Proposal Submission Guidelines", "Terms and Conditions", "Security Deposit:",
        "Facilities and Support Offered under the call for proposal:", "Prospective Consultants should demonstrate:"
    ]

    norm_keywords = [kw.lower().rstrip(":") for kw in custom_keywords]
    matched_sections = []

    segments = re.split(r'(\.\s+|\n+)', description)
    segments = [s.strip() for s in segments if s.strip() and not s.strip().startswith('.')]

    i = 0
    while i < len(segments):
        segment = segments[i]
        segment_lower = segment.lower()

        if any(kw in segment_lower for kw in norm_keywords):
            section = ["• " + segment]  # ✅ fixed bullet here
            i += 1
            while i < len(segments):
                next_segment = segments[i]
                next_segment_lower = next_segment.lower()
                if any(kw in next_segment_lower for kw in norm_keywords):
                    break
                section.append(next_segment)
                i += 1
            matched_sections.append(" ".join(section))
        else:
            i += 1

    return "\n".join(matched_sections).strip() or "N/A"

def fetch_opportunities(type_name, base_url):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    listings, seen_links = [], set()
    page = 1

    while True:
        url = f"{base_url}?page={page}"
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
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

            description_html = extract_description_after_apply_by(detail_soup)
            description = BeautifulSoup(description_html, 'html.parser').get_text(separator=' ', strip=True)
            how_to_apply = extract_how_to_apply_from_html(description)

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

    df['Clickable_Link'] = df.apply(
        lambda row: '=HYPERLINK("{}","{}")'.format(row['Link'], row['Title'].replace('"', '""')),
        axis=1
    )

    try:
        df['Deadline_Date'] = pd.to_datetime(df['Deadline'], format='%d %b %Y', errors='coerce')
    except:
        df['Deadline_Date'] = pd.NaT

    df = df.sort_values(['Deadline_Date'], na_position='last')
    df = df[['Type', 'Title', 'Description', 'How_to_Apply', 'Matched_Vertical', 'Deadline', 'Clickable_Link']]

    excel_path = 'output/relevant_grants.xlsx'
    df.to_excel(excel_path, index=False, engine='openpyxl')

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

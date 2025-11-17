import requests
import re
import html
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

URL = "https://services.ecourts.gov.in/ecourtindia_v6/?p=cnr_status/searchByCNR/"
CNR = input("Enter CNR: ")

CAPTCHA = "ct4dbt"
APP_TOKEN = "ebe9e4384ac690fdfacb5f3ab5133401a94e885d387d60bc510d59a0cf796562"

data = {
    "cino": CNR,
    "fcaptcha_code": CAPTCHA,
    "ajax_req": "true",
    "app_token": APP_TOKEN,
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
}

session = requests.Session()
r = session.post(URL, headers=headers, data=data, timeout=15)
r.raise_for_status()

try:
    js = r.json()
    html_content = js.get("casetype_list") or js.get("html")
    if not html_content:
        print("No HTML found in JSON")
        html_content = r.text  
except Exception:
    html_content = r.text  


def calc(date_str):
    cleaned_date_str = date_str.replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
    date_obj = datetime.strptime(cleaned_date_str, "%d %B %Y").date()
    
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)

    if date_obj == today:
        return "Today"
    elif date_obj == tomorrow:
        return "Tomorrow"
    else:
        return "Neither today nor tomorrow"

soup = BeautifulSoup(html_content, "html.parser")
court_tag = soup.find("h2")
court_name = court_tag.get_text(strip=True) if court_tag else "Court name not found"
print("CNR: ",CNR)
print("Court Name:", court_name)

html_content = html.unescape(html_content)
match = re.search(r"Next Hearing Date.*?(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})", html_content, re.IGNORECASE | re.DOTALL)
if match:
    next_hearing_date = match.group(1).strip()
    
    print("Next Hearing Date:", next_hearing_date)
    print(calc(next_hearing_date))
else:
    print("Next Hearing Date not found")

import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import re
import json

BASE_URL = "https://services.ecourts.gov.in"

def fetch_captcha(session):
    url = BASE_URL + "/ecourtindia_v6/?p=casestatus/getCaptcha"
    payload = {
        "ajax_req": "true",
        "app_token": "dummy" 
    }

    resp = session.get(url, params=payload)
    resp.raise_for_status()
    data = resp.json()

    app_token = data.get("app_token")

    div_captcha = data.get("div_captcha", "")
    match = re.search(r'src="([^"]+securimage_show\.php\?[^"]+)"', div_captcha)
    if not match:
        raise Exception("CAPTCHA image URL not found")

    captcha_path = match.group(1).replace("\\/", "/")
    captcha_url = BASE_URL + captcha_path
    return captcha_url, app_token

def show_captcha(session, captcha_url):
    resp = session.get(captcha_url)
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content))
    img.show()
    captcha_code = input("Enter CAPTCHA: ")
    return captcha_code

def submit_cause_list(CL_court_no, court_name_txt, state_code, dist_code, court_complex_code, est_code, causelist_date, cicri):
    with requests.Session() as session:
        captcha_url, app_token = fetch_captcha(session)
        print("Please solve the CAPTCHA shown in the image...")
        captcha_code = show_captcha(session, captcha_url)
        
        payload = {
            "CL_court_no": CL_court_no,
            "causelist_date": causelist_date,
            "cause_list_captcha_code": captcha_code,
            "court_name_txt": court_name_txt,
            "state_code": str(state_code),
            "dist_code": str(dist_code),
            "court_complex_code": str(court_complex_code),
            "est_code": est_code,
            "cicri": cicri,
            "selprevdays": "0",
            "ajax_req": "true",
            "app_token": app_token,
        }

        submit_url = BASE_URL + "/ecourtindia_v6/?p=cause_list/submitCauseList"
        resp = session.post(submit_url, data=payload)
        resp.raise_for_status()

        try:
            data = resp.json()
        except ValueError:
            print("Response is not valid JSON. Here’s the raw text:")
            print(resp.text)
            return

        case_data_html = data.get("case_data", "")
        if not case_data_html.strip():
            print("No case data found in response.")
            return

        soup = BeautifulSoup(case_data_html, "html.parser")
        table = soup.find("table")
        if not table:
            print("No table found in the case data.")
            return

        rows = table.find_all("tr")

        header = "Cause List Results\n\n"
        header += "{:<6} {:<20} {:<50} {}\n".format("SrNo", "Case No", "Party Name", "Advocate")
        header += "-" * 120 + "\n"

        lines = [header]

        for row in rows:
            cols = [td.get_text(separator=" ", strip=True) for td in row.find_all("td")]
            if len(cols) == 4:
                sr_no, case_no, party_name, advocate = cols
                line = f"{sr_no:<6} {case_no:<20} {party_name:<50} {advocate}\n"
                lines.append(line)

        footer = "\n Finished printing all cases.\n"
        lines.append(footer)
        print("".join(lines))
 
        with open("cause_list_results.txt", "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(" Saved as cause_list_results.txt")

import json

with open("selections.json", "r") as f:
    selections = json.load(f)

state_code = selections["state_code"]
dist_code = selections["district_code"]
CL_court_no = selections["court_no"]
causelist_date = selections["causelist_date"]
court_name_txt = selections["cause_list_name"]
state_code = selections["state_code"]
court_complex_code = selections["court_complex_code"]
est_code = selections["est_code"]
cicri = selections["cicri"]

print(state_code,dist_code,CL_court_no,causelist_date,court_name_txt,court_complex_code,est_code)

submit_cause_list(CL_court_no, court_name_txt, state_code, dist_code, court_complex_code, est_code, causelist_date,cicri)
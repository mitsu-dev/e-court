import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import re
import json

BASE_URL = "https://services.ecourts.gov.in/ecourtindia_v6"

def get_fresh_token(session):
    url = f"{BASE_URL}/?p=casestatus/getCaptcha"
    resp = session.get(url, params={"ajax_req": "true"})
    resp.raise_for_status()
    data = resp.json()
    return data.get("app_token")

def fetch_captcha(session):
    url = f"{BASE_URL}/?p=casestatus/getCaptcha"
    resp = session.get(url, params={"ajax_req": "true"})
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

def get_districts_for_state(session, state_code):
    app_token = get_fresh_token(session)
    url = f"{BASE_URL}/?p=casestatus/fillDistrict"
    payload = {"state_code": str(state_code), "ajax_req": "true", "app_token": app_token}
    headers = {"X-Requested-With": "XMLHttpRequest"}

    resp = session.post(url, data=payload, headers=headers)
    resp.raise_for_status()

    data = resp.json()
    html_options = data.get("dist_list", "")
    soup = BeautifulSoup(html_options, "html.parser")

    options = [(opt.text.strip(), int(opt["value"]))
               for opt in soup.find_all("option")
               if opt.get("value") and "select" not in opt.text.lower()]

    print("\nAvailable Districts:")
    for i, (name, code) in enumerate(options, 1):
        print(f"{i}. {name} ({code})")

    choice = int(input("\nEnter district number: ")) - 1
    selected = options[choice]
    print(f"Selected District: {selected[0]}, Code: {selected[1]}")
    return selected

def get_court_complexes(session, state_code, dist_code):
    app_token = get_fresh_token(session)
    url = f"{BASE_URL}/?p=casestatus/fillcomplex"
    payload = {
        "state_code": str(state_code),
        "dist_code": str(dist_code),
        "ajax_req": "true",
        "app_token": app_token,
    }
    headers = {"X-Requested-With": "XMLHttpRequest"}

    resp = session.post(url, data=payload, headers=headers)
    resp.raise_for_status()

    data = resp.json()
    html_options = data.get("complex_list", "")
    soup = BeautifulSoup(html_options, "html.parser")

    complexes = []
    for opt in soup.find_all("option"):
        value = opt.get("value", "").strip()
        name = opt.text.strip()
        if not value or "select" in name.lower():
            continue
        parts = value.split("@")
        if len(parts) >= 2:
            complexes.append({
                "court_complex_code": parts[0],
                "est_code": parts[1],
                "name": name
            })

    if not complexes:
        print("\n No court complexes found — likely due to invalid district code or expired token.")
        return None

    print("\nAvailable Court Complexes:")
    for i, c in enumerate(complexes, 1):
        print(f"{i}. {c['name']} ({c['court_complex_code']})")

    choice = int(input("\nEnter complex number: ")) - 1
    selected = complexes[choice]
    print(f"Selected Court Complex: {selected['name']}, Court Code: {selected['court_complex_code']}, Est Code: {selected['est_code']}")
    return selected


def get_cause_list(session, state_code, dist_code, court_complex_code, est_code):
    app_token = get_fresh_token(session)
    url = f"{BASE_URL}/?p=cause_list/fillCauseList"
    payload = {
        "state_code": str(state_code),
        "dist_code": str(dist_code),
        "court_complex_code": str(court_complex_code),
        "est_code": str(est_code),
        "search_act": "undefined",
        "ajax_req": "true",
        "app_token": app_token,
    }
    headers = {"X-Requested-With": "XMLHttpRequest"}

    resp = session.post(url, data=payload, headers=headers)
    resp.raise_for_status()

    data = resp.json()
    html_options = data.get("cause_list", "")
    soup = BeautifulSoup(html_options, "html.parser")
    
    options = []
    for opt in soup.find_all("option"):
        value = opt.get("value", "").strip()
        text = opt.text.strip()
        if value and "select" not in text.lower():
            options.append({"CL_court_no": value, "court_name_txt": text})

    print("\nAvailable Cause Lists:")
    valid_options = []
    index = 1

    for c in options:
        if c["CL_court_no"] == "D":
            print(f"   {c['court_name_txt']} ({c['CL_court_no']})  ← Disabled")
        else:
            print(f"{index}. {c['court_name_txt']} ({c['CL_court_no']})")
            valid_options.append(c)
            index += 1

    choice = int(input("\nEnter cause list number: ")) - 1
    selected = valid_options[choice]

    print(f"Selected Cause List: {selected['court_name_txt']}, Court No: {selected['CL_court_no']}")
    return selected


def main():
    states = {
        28: "Andaman and Nicobar",
        2: "Andhra Pradesh",
        36: "Arunachal Pradesh",
        6: "Assam",
        8: "Bihar",
        27: "Chandigarh",
        18: "Chhattisgarh",
        26: "Delhi",
        30: "Goa",
        17: "Gujarat",
        14: "Haryana",
        5: "Himachal Pradesh",
        12: "Jammu and Kashmir",
        7: "Jharkhand",
        3: "Karnataka",
        4: "Kerala",
        33: "Ladakh",
        37: "Lakshadweep",
        23: "Madhya Pradesh",
        1: "Maharashtra",
        25: "Manipur",
        21: "Meghalaya",
        19: "Mizoram",
        34: "Nagaland",
        11: "Odisha",
        35: "Puducherry",
        22: "Punjab",
        9: "Rajasthan",
        24: "Sikkim",
        10: "Tamil Nadu",
        29: "Telangana",
        38: "The Dadra And Nagar Haveli And Daman And Diu",
        20: "Tripura",
        15: "Uttarakhand",
        13: "Uttar Pradesh",
        16: "West Bengal"
    }

    print("\nAvailable States:\n")
    for code, name in states.items():
        print(f"{code:>2} - {name}")
        
    print("\n-------------------------------------")
    user_input = input("Enter the state code: ").strip()

    if user_input.isdigit() and int(user_input) in states:
        code = int(user_input)
        print(f"\nSelected State: {states[code]} (Code: {code})")
        
    with requests.Session() as session:
        state_code = code

        dist_name, dist_code = get_districts_for_state(session, state_code)
        complex_info = get_court_complexes(session, state_code, dist_code)
        if not complex_info:
            return
        cause_info = get_cause_list(
            session, state_code, dist_code,
            complex_info["court_complex_code"],
            complex_info["est_code"]
        )

        causelist_date = input("\nEnter cause list date (e.g., 27-10-2025): ")
        cicri = input("Enter 'cri' or 'civ': ")

        print("\nFinal Selections:")
        print(f"State Code: {state_code}")
        print(f"District: {dist_name}, Code: {dist_code}")
        print(f"Court Complex: {complex_info['name']}, Court Code: {complex_info['court_complex_code']}, Est Code: {complex_info['est_code']}")
        print(f"Cause List: {cause_info['court_name_txt']}, Court No: {cause_info['CL_court_no']}")
        print(f"Cause List Date: {causelist_date}")
        print(f"CICRI: {cicri}")

        selections = {
            "state_code": state_code,
            "district_name": dist_name,
            "district_code": dist_code,
            "court_complex_name": complex_info['name'],
            "court_complex_code": complex_info['court_complex_code'],
            "est_code": complex_info['est_code'],
            "cause_list_name": cause_info['court_name_txt'],
            "court_no": cause_info['CL_court_no'],
            "causelist_date": causelist_date,
            "cicri": cicri
        }

        with open("selections.json", "w") as f:
            json.dump(selections, f, indent=4)
        print("\nSelections saved to selections.json")

if __name__ == "__main__":
    main()
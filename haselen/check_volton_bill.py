import json
import os
import re
import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def load_options():
    options_path = "/data/options.json"
    if not os.path.exists(options_path):
        raise FileNotFoundError(
            f"Options file '{options_path}' not found! This must be run as a Home Assistant add-on."
        )
    with open(options_path, "r") as f:
        opts = json.load(f)
    for key in ("vusername", "vpassword", "haip", "token"):
        if key not in opts:
            raise ValueError(f"Missing '{key}' in options!")
    return opts


def update_input_text(entity_id, value, token, haip):
    url = f"https://{haip}:8123/api/services/input_text/set_value"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "entity_id": entity_id,
        "value": value,
    }
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        if response.status_code == 200:
            print(f"Updated {entity_id} to: {value}")
        else:
            print(f"Failed to update {entity_id}: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")


opts = load_options()
username = opts["vusername"]
password = opts["vpassword"]
entity_id = "input_text.volton_b21"
haip = opts["haip"]
token = opts["token"]

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service("/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    driver.get("https://myon.volton.gr/s/login/")

    # Username (phone/email)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input.inputField[placeholder='Κινητό ή email']")
        )
    )
    user_elem = driver.find_element(
        By.CSS_SELECTOR, "input.inputField[placeholder='Κινητό ή email']"
    )
    user_elem.clear()
    user_elem.send_keys(username)

    # Continue
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class, 'my-custom-button') and not(@disabled)]")
        )
    )
    driver.find_element(
        By.XPATH, "//button[contains(@class, 'my-custom-button') and not(@disabled)]"
    ).click()

    # Password
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='password'][placeholder='Κωδικός πρόσβασης']")
        )
    )
    pw_elem = driver.find_element(
        By.CSS_SELECTOR, "input[type='password'][placeholder='Κωδικός πρόσβασης']"
    )
    pw_elem.clear()
    pw_elem.send_keys(password)
    pw_elem.submit()

    # ---- Amount extraction ----
    # The amount is under: <span part="formatted-rich-text"><div> 73.02€ </div></span>
    amount_xpath = (
        "//div[contains(@class,'headerText') and "
        "@data-test-id='Block-TextAmounts-Block-1-Block-1-Text-0']"
        "//span[@part='formatted-rich-text']"
    )

    amount_el = WebDriverWait(driver, 40).until(
        EC.visibility_of_element_located((By.XPATH, amount_xpath))
    )

    raw_text = (amount_el.text or "").strip()

    # LWC/Salesforce sometimes returns empty .text; use textContent for reliability
    if not raw_text:
        raw_text = (
            driver.execute_script("return arguments[0].textContent;", amount_el) or ""
        ).strip()

    print("Raw amount field:", repr(raw_text))

    m = re.search(r"([0-9]+[.,][0-9]{2})", raw_text)
    amount = m.group(1) if m else raw_text
    print("Outstanding Volton Amount:", amount)

    update_input_text(entity_id, amount, token, haip)

except (TimeoutException, NoSuchElementException) as e:
    with open("/tmp/page_debug_volton.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("Failed to find outstanding amount:", str(e))
    print("Check /tmp/page_debug_volton.html for page source")
finally:
    driver.quit()

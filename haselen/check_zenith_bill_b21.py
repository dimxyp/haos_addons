from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import json
import os
import warnings
from urllib3.exceptions import InsecureRequestWarning

# suppress "Unverified HTTPS request" spam
warnings.simplefilter("ignore", InsecureRequestWarning)

QUIET = True
def info(msg):
    if not QUIET:
        print(msg)

def critical(msg):
    print(msg)

def load_options():
    options_path = "/data/options.json"
    if not os.path.exists(options_path):
        raise FileNotFoundError(
            f"Options file '{options_path}' not found! This must be run as a Home Assistant add-on."
        )
    with open(options_path, "r") as f:
        opts = json.load(f)
    for key in ("zusername", "zpassword", "haip", "token"):
        if key not in opts:
            raise ValueError(f"Missing '{key}' in options!")
    return opts

opts = load_options()
username = opts["zusername"]
password = opts["zpassword"]
entity_id = "input_text.zenith_power"
haip = opts["haip"]
token = opts["token"]

# ---- target supply filter (only this supply) ----
TARGET_SUPPLY_TOKEN = "13061304"

def update_input_text(entity_id, value, token, haip):
    url = f"https://{haip}:8123/api/services/input_text/set_value"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"entity_id": entity_id, "value": value}

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        if response.status_code != 200:
            critical(f"Failed to update {entity_id}: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        critical(f"API request failed: {e}")

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service('/usr/bin/chromedriver', log_output="/dev/null")
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    driver.get("https://myzenith.zenith.gr/user/login")

    # Accept cookies (not critical)
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
        info("Accepted cookies.")
    except Exception:
        pass

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "login")))
    info("Login form loaded.")

    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)

    driver.find_element(
        By.XPATH,
        '//form[@id="login"]//button[@type="submit" and .//span[text()="Σύνδεση"]]'
    ).click()

    try:
        WebDriverWait(driver, 15).until_not(EC.url_contains("/user/login"))
        info(f"Logged in! Current URL: {driver.current_url}")
    except TimeoutException:
        critical("Login failed (still on login page).")
        driver.quit()
        raise SystemExit(1)

    driver.get("https://myzenith.zenith.gr/bills/Electricity")
    info("Navigated to bills.")

    # 1) Find the correct "bill card" (article) that contains your supply number token
    article = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((
            By.XPATH,
            (
                '//article[contains(@class,"card--bill")]'
                f'[.//span[normalize-space()="Αρ. Παροχής"]'
                f'/following-sibling::span[contains(normalize-space(.), "{TARGET_SUPPLY_TOKEN}")]]'
            )
        ))
    )

    # 2) From inside that article, grab "Συνολικό Ποσό Οφειλής"
    value_elem = article.find_element(
        By.XPATH,
        './/span[contains(normalize-space(.), "Συνολικό Ποσό Οφειλής")]/following-sibling::h4'
    )
    amount = value_elem.text.strip()

    critical(f"Outstanding Amount ({TARGET_SUPPLY_TOKEN}): {amount}")

    clean_amount = amount.replace("€", "").strip()
    update_input_text(entity_id, clean_amount, token, haip)

except (TimeoutException, NoSuchElementException) as e:
    with open("/tmp/page_debug.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    critical(f"Failed to find outstanding amount for supply token {TARGET_SUPPLY_TOKEN}: {e}")
    critical("Saved debug HTML to /tmp/page_debug.html")
finally:
    driver.quit()
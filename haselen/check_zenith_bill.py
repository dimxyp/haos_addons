from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import json
import os

# --- Load Home Assistant add-on options ---
def load_options():
    options_path = "/data/options.json"
    if not os.path.exists(options_path):
        raise FileNotFoundError(f"Options file '{options_path}' not found! This must be run as a Home Assistant add-on.")
    with open(options_path, "r") as f:
        opts = json.load(f)
    for key in ("username", "password", "haip", "token"):
        if key not in opts:
            raise ValueError(f"Missing '{key}' in options!")
    return opts

opts = load_options()
username = opts["username"]
password = opts["password"]
entity_id = opts.get("entity_id", "input_text.zenith_power")
haip = opts["haip"]
token = opts["token"]

def update_input_text(entity_id, value, token, haip):
    url = f"https://{haip}:8123/api/services/input_text/set_value"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "entity_id": entity_id,
        "value": value
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
        print(f"Updated {entity_id} to: {value}, HA response:", r.text)
        return True
    except Exception as e:
        print("Failed to update Home Assistant input_text:", e)
        return False

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service('/usr/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Start from the login page
    driver.get("https://myzenith.zenith.gr/user/login")

    # Accept cookies
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
        print("Accepted cookies.")
    except Exception as e:
        print("Cookie banner not found or already accepted.", str(e))

    # Wait for login form
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "login"))
    )
    print("Login form loaded.")

    # Fill login details
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)

    # Click submit button ("Σύνδεση")
    driver.find_element(By.XPATH, '//form[@id="login"]//button[@type="submit" and .//span[text()="Σύνδεση"]]').click()

    # Wait for login to finish (URL must change from /user/login)
    try:
        WebDriverWait(driver, 15).until_not(
            EC.url_contains("/user/login")
        )
        print("Logged in! Current URL:", driver.current_url)
    except TimeoutException:
        print("Login failed, still on login page.")
        driver.quit()
        exit(1)

    # Visit the bills page
    driver.get("https://myzenith.zenith.gr/bills/Electricity")
    print("Navigated to bills.")

    # Wait for the value block to appear
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.XPATH, '//span[contains(text(),"Συνολικό Ποσό Οφειλής")]/following-sibling::h4')
        )
    )

    # Extract the amount
    value_elem = driver.find_element(By.XPATH, '//span[contains(text(),"Συνολικό Ποσό Οφειλής")]/following-sibling::h4')
    amount = value_elem.text.strip()
    print("Outstanding Amount:", amount)

    clean_amount = amount.replace("€", "").strip()

    # Send to Home Assistant
    update_input_text(entity_id, clean_amount, token, haip)

except (TimeoutException, NoSuchElementException) as e:
    with open("/tmp/page_debug.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("Failed to find outstanding amount:", str(e))
    print("Check /tmp/page_debug.html for page source")
finally:
    driver.quit()
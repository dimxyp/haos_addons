import json
import os
import re
import time
import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


OPTIONS_PATH = "/data/options.json"
DEBUG_HTML_PATH = "/tmp/page_debug_volton.html"
DEBUG_SCREENSHOT_PATH = "/tmp/page_debug_volton.png"


def load_options():
    if not os.path.exists(OPTIONS_PATH):
        raise FileNotFoundError(
            f"Options file '{OPTIONS_PATH}' not found! This must be run as a Home Assistant add-on."
        )
    with open(OPTIONS_PATH, "r") as f:
        opts = json.load(f)
    for key in ("vusername", "vpassword", "haip", "token"):
        if key not in opts:
            raise ValueError(f"Missing '{key}' in options!")
    return opts


def update_input_text(entity_id, value, token, haip):
    url = f"https://{haip}:8123/api/services/input_text/set_value"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"entity_id": entity_id, "value": value}
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=20)
        if response.status_code == 200:
            print(f"Updated {entity_id} to: {value}")
        else:
            print(f"Failed to update {entity_id}: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")


def dump_debug(driver, reason):
    try:
        with open(DEBUG_HTML_PATH, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"[DEBUG] wrote HTML to {DEBUG_HTML_PATH} ({reason})")
    except Exception as e:
        print(f"[DEBUG] failed to write HTML: {e}")

    try:
        driver.save_screenshot(DEBUG_SCREENSHOT_PATH)
        print(f"[DEBUG] wrote screenshot to {DEBUG_SCREENSHOT_PATH} ({reason})")
    except Exception as e:
        print(f"[DEBUG] failed to write screenshot: {e}")

    try:
        print("[DEBUG] current_url:", driver.current_url)
    except Exception:
        pass
    try:
        print("[DEBUG] title:", driver.title)
    except Exception:
        pass


def normalize_amount(raw_text):
    if raw_text is None:
        return None
    raw_text = raw_text.replace("\u00a0", " ").strip()  # NBSP -> space
    m = re.search(r"([0-9]+[.,][0-9]{2})", raw_text)
    return m.group(1) if m else raw_text


def wait_for_amount_text(driver, timeout=70):
    """
    Wait until a <span part="formatted-rich-text"> appears with textContent containing '€'.
    This matches the exact HTML you pasted.
    Returns the raw text (e.g. '73.02€').
    """
    def _has_amount(d):
        spans = d.find_elements(By.CSS_SELECTOR, "span[part='formatted-rich-text']")
        for sp in spans:
            try:
                txt = d.execute_script("return arguments[0].textContent;", sp)
            except WebDriverException:
                txt = sp.text
            txt = (txt or "").replace("\u00a0", " ").strip()
            if "€" in txt:
                return txt
        return False

    return WebDriverWait(driver, timeout).until(_has_amount)


def main():
    opts = load_options()
    username = opts["vusername"]
    password = opts["vpassword"]
    haip = opts["haip"]
    token = opts["token"]

    entity_id = "input_text.volton_b21"

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://myon.volton.gr/s/login/?language=el")

        # Username
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input.inputField[placeholder='Κινητό ή email']")
            )
        )
        user_elem = driver.find_element(By.CSS_SELECTOR, "input.inputField[placeholder='Κινητό ή email']")
        user_elem.clear()
        user_elem.send_keys(username)

        # Continue button
        WebDriverWait(driver, 25).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@class, 'my-custom-button') and not(@disabled)]")
            )
        )
        driver.find_element(By.XPATH, "//button[contains(@class, 'my-custom-button') and not(@disabled)]").click()

        # Password
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='password'][placeholder='Κωδικός πρόσβασης']")
            )
        )
        pw_elem = driver.find_element(By.CSS_SELECTOR, "input[type='password'][placeholder='Κωδικός πρόσβασης']")
        pw_elem.clear()
        pw_elem.send_keys(password)

        # Prefer clicking a visible enabled button if there is one; fallback to Enter.
        buttons = driver.find_elements(By.XPATH, "//button[not(@disabled)]")
        clicked = False
        for b in buttons:
            t = (b.text or "").strip().lower()
            if t in ("είσοδος", "σύνδεση", "login", "sign in", "submit", "συνέχεια"):
                try:
                    b.click()
                    clicked = True
                    break
                except WebDriverException:
                    pass
        if not clicked:
            pw_elem.send_keys(Keys.ENTER)

        # Let SPA render
        time.sleep(2)
        print("[DEBUG] after submit current_url:", driver.current_url)
        print("[DEBUG] after submit title:", driver.title)

        raw_text = wait_for_amount_text(driver, timeout=80)
        print("Raw amount field:", repr(raw_text))

        amount = normalize_amount(raw_text)
        print("Outstanding Volton Amount:", amount)

        update_input_text(entity_id, amount, token, haip)

    except (TimeoutException, NoSuchElementException) as e:
        dump_debug(driver, f"selenium-error: {e.__class__.__name__}")
        print("Failed to find outstanding amount:", str(e))
        print(f"Check {DEBUG_HTML_PATH} for page source")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()

import json
import os
import re
import time
import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
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
        # NOTE: verify=False because many HA installs use self-signed certs.
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


def get_text_content(driver, el):
    """Return visible text; if empty, return textContent (more reliable for LWC)."""
    txt = (el.text or "").strip()
    if txt:
        return txt
    try:
        txt = (driver.execute_script("return arguments[0].textContent;", el) or "").strip()
    except WebDriverException:
        txt = ""
    return txt


def find_amount_text_in_current_context(driver):
    """
    Look for spans like:
      <span part="formatted-rich-text"><div> 73.02€ </div></span>
    Return the first text that contains '€'.
    """
    candidates = driver.find_elements(By.CSS_SELECTOR, "span[part='formatted-rich-text']")
    for el in candidates:
        t = get_text_content(driver, el)
        if "€" in t:
            return t
    return None


def find_amount_text(driver, timeout=60):
    """
    Robust amount extraction:
      1) Wait for any 'formatted-rich-text' spans to appear.
      2) Search in main document for one containing €.
      3) If not found, sweep iframes and search there.
    Returns raw text like '73.02€' (may contain spaces/non-breaking spaces).
    """
    wait = WebDriverWait(driver, timeout)

    # Wait until at least one candidate exists somewhere in the main document.
    # (Even if the real value appears later, this reduces flakiness.)
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "span[part='formatted-rich-text']")) > 0)

    # Try main document first
    txt = find_amount_text_in_current_context(driver)
    if txt:
        return txt

    # If not found, try iframes (common cause of element-not-found)
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    if iframes:
        print(f"[DEBUG] found {len(iframes)} iframe(s), scanning...")
    for idx, frame in enumerate(iframes):
        try:
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            txt = find_amount_text_in_current_context(driver)
            if txt:
                print(f"[DEBUG] amount found in iframe index {idx}")
                driver.switch_to.default_content()
                return txt
        except WebDriverException:
            continue

    driver.switch_to.default_content()
    return None


def normalize_amount(raw_text):
    """
    Extract number like 96.24 or 96,24 from raw text.
    """
    if raw_text is None:
        return None
    raw_text = raw_text.replace("\u00a0", " ").strip()  # convert NBSP to normal spaces
    m = re.search(r"([0-9]+[.,][0-9]{2})", raw_text)
    return m.group(1) if m else raw_text


def main():
    opts = load_options()
    username = opts["vusername"]
    password = opts["vpassword"]
    haip = opts["haip"]
    token = opts["token"]

    # If you want this to be configurable via options.json, tell me and I’ll adjust.
    entity_id = "input_text.volton_b21"

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://myon.volton.gr/s/login/")

        # Username
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input.inputField[placeholder='Κινητό ή email']")
            )
        )
        user_elem = driver.find_element(By.CSS_SELECTOR, "input.inputField[placeholder='Κινητό ή email']")
        user_elem.clear()
        user_elem.send_keys(username)

        # Continue
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
        pw_elem.submit()

        # Give the portal a moment to redirect/render after submit
        time.sleep(2)
        print("[DEBUG] after submit current_url:", driver.current_url)
        print("[DEBUG] after submit title:", driver.title)

        raw_text = find_amount_text(driver, timeout=70)
        if not raw_text:
            dump_debug(driver, "amount-not-found")
            raise TimeoutException("Amount element not found (no formatted-rich-text containing €).")

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

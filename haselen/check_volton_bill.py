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

DEBUG_DIR = "/share/volton_debug"
DEBUG_HTML_PATH = os.path.join(DEBUG_DIR, "page_debug_volton.html")
DEBUG_SCREENSHOT_PATH = os.path.join(DEBUG_DIR, "page_debug_volton.png")
DEBUG_PROBE_PATH = os.path.join(DEBUG_DIR, "_probe.txt")


def load_options():
    if not os.path.exists(OPTIONS_PATH):
        raise FileNotFoundError(f"Options file '{OPTIONS_PATH}' not found!")
    with open(OPTIONS_PATH, "r", encoding="utf-8") as f:
        opts = json.load(f)

    for key in ("vusername", "vpassword", "haip", "token"):
        if key not in opts:
            raise ValueError(f"Missing '{key}' in options!")

    opts.setdefault("debug_sleep_seconds", 0)
    return opts


def ensure_debug_dir():
    os.makedirs(DEBUG_DIR, exist_ok=True)


def debug_probe_share():
    print("[DEBUG] /share exists:", os.path.exists("/share"))
    try:
        print("[DEBUG] /share listing:", os.listdir("/share"))
    except Exception as e:
        print("[DEBUG] /share list failed:", repr(e))

    try:
        ensure_debug_dir()
        with open(DEBUG_PROBE_PATH, "w", encoding="utf-8") as f:
            f.write(f"probe ok @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print("[DEBUG] wrote probe:", DEBUG_PROBE_PATH)
        print("[DEBUG] DEBUG_DIR listing:", os.listdir(DEBUG_DIR))
    except Exception as e:
        print("[DEBUG] probe write failed:", repr(e))


def dump_debug(driver, reason):
    ensure_debug_dir()

    html = ""
    try:
        html = driver.page_source or ""
        with open(DEBUG_HTML_PATH, "w", encoding="utf-8") as f:
            f.write(html)
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
        print("[DEBUG] title:", driver.title)
    except Exception:
        pass

    if html:
        lowered = html.lower()
        for n in ("captcha", "recaptcha", "two-factor", "2fa", "otp", "verification", "access denied", "error"):
            if n in lowered:
                print(f"[DEBUG] page_source contains '{n}'")


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


def normalize_amount(raw_text):
    if raw_text is None:
        return None
    raw_text = raw_text.replace("\u00a0", " ").strip()
    m = re.search(r"([0-9]+[.,][0-9]{2})", raw_text)
    return m.group(1) if m else raw_text


def wait_for_amount_text(driver, timeout=80):
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


def type_like_human(elem, text, delay=0.05):
    elem.click()
    elem.clear()
    for ch in text:
        elem.send_keys(ch)
        time.sleep(delay)


def force_input_events(driver, elem):
    # Dispatch input/change events so reactive frameworks update button enabled state
    driver.execute_script(
        """
        const el = arguments[0];
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        """,
        elem,
    )


def click_continue(driver):
    # Your existing selector, but we try a couple of safe variants
    xpaths = [
        "//button[contains(@class, 'my-custom-button') and not(@disabled)]",
        "//button[contains(@class, 'my-custom-button')]",
    ]
    for xp in xpaths:
        btns = driver.find_elements(By.XPATH, xp)
        for b in btns:
            try:
                if b.is_enabled():
                    b.click()
                    return True
            except WebDriverException:
                continue
    return False


def main():
    opts = load_options()
    username = opts["vusername"]
    password = opts["vpassword"]
    haip = opts["haip"]
    token = opts["token"]
    debug_sleep_seconds = int(opts.get("debug_sleep_seconds", 0))

    entity_id = "input_text.volton_b21"

    debug_probe_share()

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://myon.volton.gr/s/login/?language=el")

        # USERNAME: wait clickable (not just present)
        user_css = "input.inputField[placeholder='Κινητό ή email']"
        user_elem = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, user_css))
        )

        # Type slowly + force events (important!)
        type_like_human(user_elem, username, delay=0.04)
        force_input_events(driver, user_elem)

        # Wait a bit for JS to enable the button
        time.sleep(0.5)

        # Continue button: wait clickable then click
        try:
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'my-custom-button') and not(@disabled)]")
                )
            )
        except TimeoutException:
            # dump debug if continue never enables
            dump_debug(driver, "continue-not-enabled")
            raise

        driver.find_element(
            By.XPATH, "//button[contains(@class, 'my-custom-button') and not(@disabled)]"
        ).click()

        # PASSWORD
        pw_css = "input[type='password'][placeholder='Κωδικός πρόσβασης']"
        pw_elem = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, pw_css))
        )
        type_like_human(pw_elem, password, delay=0.04)
        force_input_events(driver, pw_elem)

        # Submit via Enter (or you can add a button click if you find its text)
        pw_elem.send_keys(Keys.ENTER)

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
        print("Failed:", str(e))
        print(f"Debug files saved to: {DEBUG_DIR}")
        print(f" - {DEBUG_HTML_PATH}")
        print(f" - {DEBUG_SCREENSHOT_PATH}")
        print(f" - {DEBUG_PROBE_PATH}")

        if debug_sleep_seconds > 0:
            print(f"[DEBUG] sleeping for {debug_sleep_seconds}s ...")
            time.sleep(debug_sleep_seconds)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()

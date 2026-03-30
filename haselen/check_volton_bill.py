import json
import os
import re
import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

OPTIONS_PATH = "/data/options.json"

DEBUG_DIR = "/share/volton_debug"
DEBUG_HTML_LOGIN = os.path.join(DEBUG_DIR, "volton_login_page.html")
DEBUG_PNG_LOGIN = os.path.join(DEBUG_DIR, "volton_login_page.png")
DEBUG_HTML_AFTER = os.path.join(DEBUG_DIR, "volton_after_login.html")
DEBUG_PNG_AFTER = os.path.join(DEBUG_DIR, "volton_after_login.png")


def load_options():
    if not os.path.exists(OPTIONS_PATH):
        raise FileNotFoundError(f"Options file '{OPTIONS_PATH}' not found")

    with open(OPTIONS_PATH, "r", encoding="utf-8") as f:
        opts = json.load(f)

    for key in ("vusername", "vpassword", "haip", "token"):
        if key not in opts or not str(opts[key]).strip():
            raise ValueError(f"Missing '{key}' in options.json: {key}")

    # entity_id όπου θα γράψουμε το ποσό
    opts.setdefault("entity_id", "input_text.volton_b21")
    opts.setdefault("debug_sleep_seconds", 0)
    return opts


def ensure_debug_dir():
    os.makedirs(DEBUG_DIR, exist_ok=True)


def debug_dump(driver, html_path, png_path, label):
    try:
        ensure_debug_dir()
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"[DEBUG] Saved HTML ({label}) to {html_path}")
    except Exception as e:
        print(f"[DEBUG] Could not save HTML ({label}): {e}")

    try:
        driver.save_screenshot(png_path)
        print(f"[DEBUG] Saved screenshot ({label}) to {png_path}")
    except Exception as e:
        print(f"[DEBUG] Could not save screenshot ({label}): {e}")


def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver


def find_username_input(driver):
    wait = WebDriverWait(driver, 20)
    return wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='text']")))


def find_password_input(driver):
    wait = WebDriverWait(driver, 20)
    return wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//div[contains(@c-vdpasswordmainlogin_vdpasswordmainlogin,'')]//input[@type='password']",
            )
        )
    )


def do_login(driver, username, password):
    url = "https://myon.volton.gr/myOn/s/?language=el"
    print("Opening:", url)
    driver.get(url)

    # Login page debug
    time.sleep(5)
   # debug_dump(driver, DEBUG_HTML_LOGIN, DEBUG_PNG_LOGIN, "login_page")

    # 1. username
    user_input = find_username_input(driver)
    time.sleep(0.5)
    user_input.clear()
    user_input.send_keys(username)
    print("Typed username")

    wait = WebDriverWait(driver, 20)
    continue_btn = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(@class,'my-custom-button') "
                "and (text()='Συνέχεια' or normalize-space()='Συνέχεια')]",
            )
        )
    )
    continue_btn.click()
    print("Clicked first 'Συνέχεια'")

    # 2. password
    time.sleep(3)
    pw_input = find_password_input(driver)
    time.sleep(0.5)
    pw_input.clear()
    pw_input.send_keys(password)
    print("Typed password")

    login_btn = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(@class,'my-custom-button') "
                "and (text()='Σύνδεση' or normalize-space()='Σύνδεση')]",
            )
        )
    )
    login_btn.click()
    print("Clicked 'Σύνδεση'")

    # Μεγάλο delay + προσπάθεια να περιμένουμε να τελειώσει το loading
    # Πρώτα ένα σκληρό sleep για να φορτώσουν τα Aura scripts
    time.sleep(15)

    # Optionally: αν υπάρχει γνωστό loader, μπορούμε να περιμένουμε να εξαφανιστεί
    try:
        # Παράδειγμα: div με class "slds-spinner" ή κάτι παρόμοιο
        WebDriverWait(driver, 30).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".slds-spinner"))
        )
        print("[DEBUG] Spinner disappeared")
    except Exception:
        # Αν δεν βρούμε spinner, συνεχίζουμε κανονικά
        print("[DEBUG] Spinner not found or still visible, continuing anyway")

    print("After submit URL:", driver.current_url)
   # debug_dump(driver, DEBUG_HTML_AFTER, DEBUG_PNG_AFTER, "after_login")


def wait_for_amount_text(driver, timeout=120):
    """
    Παίρνει όλο το innerText της σελίδας μέσω JS και ψάχνει γύρω από
    το 'Ανεξόφλητος λογαριασμός' για ποσό τύπου 73.02€.
    Έτσι αποφεύγουμε το shadow DOM θέμα.
    """
    import textwrap

    def _has_amount(drv):
        # Παίρνουμε το ορατό κείμενο της σελίδας
        full_text = drv.execute_script("return document.body.innerText || ''")
        if not full_text:
            print("[DEBUG] innerText is empty")
            return False

        # Για debug – να μην γεμίσει τα logs:
        lines = full_text.splitlines()
        snippet = "\n".join(lines[:40])
        print("[DEBUG] innerText first lines:\n" + textwrap.indent(snippet, "    "))

        # Βρίσκουμε γραμμές που περιέχουν 'Ανεξόφλητος λογαριασμός'
        for i, line in enumerate(lines):
            if "Ανεξόφλητος λογαριασμός" in line:
                # Κοιτάμε αυτήν και τις επόμενες 3 γραμμές για pattern ποσού
                window = "\n".join(lines[i : i + 4])
                m = re.search(r"([0-9]+[.,][0-9]{2}\s*€)", window)
                if m:
                    txt = m.group(1)
                    txt = txt.replace("\u00a0", " ").strip()
                    print(f"[DEBUG] Candidate amount from innerText: {repr(txt)}")
                    return txt

        return False

    return WebDriverWait(driver, timeout).until(_has_amount)


def normalize_amount(raw_text):
    """
    Παίρνει κάτι σαν ' 73.02€ ' ή '73,02 €' και επιστρέφει '73.02'.
    """
    if raw_text is None:
        return None
    raw_text = raw_text.replace("\u00a0", " ").strip()
    m = re.search(r"([0-9]+[.,][0-9]{2})", raw_text)
    if not m:
        return raw_text
    val = m.group(1).replace(",", ".")
    return val


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


def main():
    opts = load_options()
    haip = opts["haip"]
    token = opts["token"]
    entity_id = opts["entity_id"]

    driver = create_driver()
    try:
        do_login(driver, opts["vusername"], opts["vpassword"])

        print("Waiting for amount text ...")
        raw = wait_for_amount_text(driver, timeout=120)
        print("Raw amount text:", repr(raw))

        amount = normalize_amount(raw)
        print("Normalized amount:", amount)

        update_input_text(entity_id, amount, token, haip)

        debug_sleep = int(opts.get("debug_sleep_seconds", 0))
        if debug_sleep > 0:
            print(f"[DEBUG] Sleeping for {debug_sleep}s for inspection...")
            time.sleep(debug_sleep)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()

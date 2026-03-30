import json
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

OPTIONS_PATH = "/data/options.json"


def load_options():
    if not os.path.exists(OPTIONS_PATH):
        raise FileNotFoundError(f"Options file '{OPTIONS_PATH}' not found")

    with open(OPTIONS_PATH, "r", encoding="utf-8") as f:
        opts = json.load(f)

    for key in ("vusername", "vpassword"):
        if key not in opts or not str(opts[key]).strip():
            raise ValueError(f"Missing '{key}' in options.json: {key}")

    return opts


def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver


def debug_dump(driver, label: str):
    """Αποθηκεύει HTML + screenshot για να δούμε τι βλέπει ο Selenium."""
    try:
        html_path = f"/share/volton_debug/volton_{label}.html"
        png_path = f"/share/volton_debug/volton_{label}.png"

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"[DEBUG] Saved page source to {html_path}")

        try:
            driver.save_screenshot(png_path)
            print(f"[DEBUG] Saved screenshot to {png_path}")
        except Exception as e:
            print(f"[DEBUG] Could not save screenshot: {e}")
    except Exception as e:
        print(f"[DEBUG] debug_dump failed: {e}")


def find_username_input(driver):
    """Δοκιμάζει διάφορους selectors για το πρώτο input."""
    wait = WebDriverWait(driver, 20)

    candidates = [
        (By.CSS_SELECTOR, "input.inputField"),
        (By.CSS_SELECTOR, "input[placeholder='Κινητό ή email']"),
        (By.XPATH, "//input[@type='text']"),
        (By.XPATH, "//div[contains(@class,'mainMobileLogin')]//input"),
    ]

    last_exc = None
    for by, sel in candidates:
        print(f"[DEBUG] Trying username selector: {by} = {sel}")
        try:
            el = wait.until(EC.presence_of_element_located((by, sel)))
            print(f"[DEBUG] Found username input with selector: {by} = {sel}")
            return el
        except Exception as e:
            print(f"[DEBUG] Selector failed: {by} = {sel} ({e})")
            last_exc = e

    raise last_exc or RuntimeError("Could not find username input")


def find_password_input(driver):
    """Δοκιμάζει διάφορους selectors για το password."""
    wait = WebDriverWait(driver, 20)

    candidates = [
        (
            By.CSS_SELECTOR,
            "div[c-vdpasswordmainlogin_vdpasswordmainlogin] input[type='password']",
        ),
        (By.CSS_SELECTOR, "input[type='password']"),
        (
            By.XPATH,
            "//div[contains(@c-vdpasswordmainlogin_vdpasswordmainlogin,'')]//input[@type='password']",
        ),
    ]

    last_exc = None
    for by, sel in candidates:
        print(f"[DEBUG] Trying password selector: {by} = {sel}")
        try:
            el = wait.until(EC.presence_of_element_located((by, sel)))
            print(f"[DEBUG] Found password input with selector: {by} = {sel}")
            return el
        except Exception as e:
            print(f"[DEBUG] Selector failed: {by} = {sel} ({e})")
            last_exc = e

    raise last_exc or RuntimeError("Could not find password input")


def do_login(driver, username, password):
    url = "https://myon.volton.gr/myOn/s/?language=el"
    print("Opening:", url)
    driver.get(url)

    # Δίνουμε λίγο χρόνο να φορτώσει και γράφουμε debug
    time.sleep(5)
    debug_dump(driver, "login_page")

    # --- 1. Πρώτη οθόνη: username ---
    username_input = find_username_input(driver)
    time.sleep(0.5)
    username_input.clear()
    username_input.send_keys(username)
    print("Typed username")

    # Βρίσκουμε το κουμπί "Συνέχεια" με χαλαρό selector
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

    # --- 2. Δεύτερη οθόνη: password ---
    time.sleep(3)
    debug_dump(driver, "password_page")

    password_input = find_password_input(driver)
    time.sleep(0.5)
    password_input.clear()
    password_input.send_keys(password)
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

    # --- 3. Περιμένουμε να αλλάξει η σελίδα ---
    def logged_in(drv):
        url_now = drv.current_url or ""
        return "/myOn/s/" in url_now and "login" not in url_now

    try:
        WebDriverWait(driver, 30).until(logged_in)
        print("Login appears successful. Current URL:", driver.current_url)
        debug_dump(driver, "after_login")
    except Exception as e:
        print("[DEBUG] Login did not complete as expected:", e)
        debug_dump(driver, "login_failed")
        raise


def main():
    opts = load_options()
    driver = create_driver()
    try:
        do_login(driver, opts["vusername"], opts["vpassword"])
        time.sleep(3)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()

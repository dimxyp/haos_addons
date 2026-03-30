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

    # Αν στο add-on ήδη χρησιμοποιείς διαφορετικό webdriver, προσαρμόσ’ το εδώ
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver


def do_login(driver, username, password):
    url = "https://myon.volton.gr/myOn/s/?language=el"
    print("Opening:", url)
    driver.get(url)

    wait = WebDriverWait(driver, 30)

    # --- 1. Πρώτη οθόνη: Κινητό ή email ---
    # Χρησιμοποιούμε απλό selector με την class "inputField"
    username_input = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input.inputField"))
    )
    time.sleep(0.5)
    username_input.clear()
    username_input.send_keys(username)
    print("Typed username")

    # Κουμπί "Συνέχεια" στην ίδια φόρμα (πρώτο button.my-custom-button)
    continue_btn = wait.until(
        EC.element_to_be_clickable(
            (
                By.CSS_SELECTOR,
                "div[c-vd_mainlogininputphoneoremail_vd_mainlogininputphoneoremail] button.my-custom-button",
            )
        )
    )
    continue_btn.click()
    print("Clicked first 'Συνέχεια'")

    # --- 2. Δεύτερη οθόνη: password ---
    password_input = wait.until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                "div[c-vdpasswordmainlogin_vdpasswordmainlogin] "
                "input[type='password']",
            )
        )
    )
    time.sleep(0.5)
    password_input.clear()
    password_input.send_keys(password)
    print("Typed password")

    login_btn = wait.until(
        EC.element_to_be_clickable(
            (
                By.CSS_SELECTOR,
                "div[c-vdpasswordmainlogin_vdpasswordmainlogin] button.my-custom-button",
            )
        )
    )
    login_btn.click()
    print("Clicked 'Σύνδεση'")

    # --- 3. Περιμένουμε να φορτώσει η κεντρική σελίδα μετά το login ---
    # Απλό wait: να αλλάξει το URL και να ΜΗΝ περιέχει "login"
    def logged_in(drv):
        url_now = drv.current_url or ""
        return "/myOn/s/" in url_now and "login" not in url_now

    wait.until(logged_in)
    print("Login appears successful. Current URL:", driver.current_url)

    # Debug: screenshot για να το δούμε αν χρειαστεί
    try:
        driver.save_screenshot("/tmp/volton_after_login.png")
        print("Saved screenshot to /tmp/volton_after_login.png")
    except Exception as e:
        print("Could not save screenshot:", e)


def main():
    opts = load_options()
    driver = create_driver()
    try:
        do_login(driver, opts["vusername"], opts["vpassword"])
        # Εδώ αργότερα θα βάλουμε κώδικα για να πάρουμε υπόλοιπο λογαριασμού
        time.sleep(3)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()

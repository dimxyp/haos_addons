import json
import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

OPTIONS_PATH = "/data/options.json"


def load_options():
    with open(OPTIONS_PATH, "r", encoding="utf-8") as f:
        opts = json.load(f)

    for key in ("vusername", "vpassword"):
        if key not in opts or not str(opts[key]).strip():
            raise ValueError(f"Missing '{key}' in options.json")

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


def do_login(driver, username, password):
    url = "https://myon.volton.gr/myOn/s/?language=el"
    driver.get(url)

    wait = WebDriverWait(driver, 30)

    # 1. Πρώτη οθόνη – κινητό / email
    username_input = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input.inputField[placeholder='Κινητό ή email']")
        )
    )
    username_input.clear()
    username_input.send_keys(username)

    # Περιμένουμε να ενεργοποιηθεί το κουμπί "Συνέχεια"
    continue_btn = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div[c-vd_mainlogininputphoneoremail_vd_mainlogininputphoneoremail] button.my-custom-button")
        )
    )
    continue_btn.click()

    # 2. Δεύτερη οθόνη – password
    password_input = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='password'][placeholder='Κωδικός πρόσβασης']")
        )
    )
    time.sleep(0.5)  # μικρό delay για σταθερότητα
    password_input.clear()
    password_input.send_keys(password)

    login_btn = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div[c-vdpasswordmainlogin_vdpasswordmainlogin] button.my-custom-button")
        )
    )
    login_btn.click()

    # 3. Περιμένουμε να ολοκληρωθεί το login (home σελίδα)
    # Εδώ κάνουμε ένα generic wait π.χ. για URL που ΔΕΝ είναι πλέον /s/?language=el
    wait.until(lambda d: "/myOn/s/" in d.current_url and "login" not in d.current_url)
    print("Login seems successful, current URL:", driver.current_url)


def main():
    opts = load_options()
    drv = create_driver()
    try:
        do_login(drv, opts["vusername"], opts["vpassword"])
        # Εδώ αργότερα θα βάλουμε: παίρνω cookies -> requests για Aura -> TotalBalance
        time.sleep(5)
    finally:
        drv.quit()


if __name__ == "__main__":
    main()

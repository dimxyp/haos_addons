from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json

CONFIG_PATH = '/data/options.json'  # Home Assistant Addon path for user config

def get_credentials():
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    return config.get('username'), config.get('password')

username, password = get_credentials()

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
service = Service('/usr/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    driver.get("https://myzenith.zenith.gr/")

    # Accept cookies
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
        print("Accepted cookies.")
    except Exception as e:
        print("Cookie banner not found or already accepted.", str(e))

    # Wait for login form and fill credentials
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "login"))
    )
    driver.find_element(By.ID, "username").clear()
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(password)

    # Click login button (greek: 'Σύνδεση')
    driver.find_element(By.XPATH, "//button[@type='submit' and span[text()='Σύνδεση']]").click()

    # Wait for login redirect
    try:
        WebDriverWait(driver, 20).until(
            EC.any_of(
                EC.url_contains("/bills"),
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'/bills')]"))
            )
        )
    except TimeoutException:
        print("Login failed: Timeout waiting for success redirect or 'bills' link.")
        driver.quit()
        exit(1)

    # Go to electricity bills page
    driver.get("https://myzenith.zenith.gr/bills/Electricity")

    # Wait for the value block to appear
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'is-flex') and .//span[contains(text(),'Συνολικό Ποσό Οφειλής')]]/h4")
        )
    )

    value_elem = driver.find_element(
        By.XPATH, "//div[contains(@class, 'is-flex') and .//span[contains(text(),'Συνολικό Ποσό Οφειλής')]]/h4"
    )
    amount = value_elem.text.strip()
    print("Outstanding Amount:", amount)

except (TimeoutException, NoSuchElementException) as e:
    print("Failed to find outstanding amount:", str(e))
finally:
    driver.quit()
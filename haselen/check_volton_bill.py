import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Function to extract the outstanding amount
def extract_outstanding_amount(driver):
    try:
        # Wait for the element to be visible
        element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "span[part='formatted-rich-text']"))
        )
        # Extract and return the text content
        return element.text
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

# Call the function with your driver instance
# outstanding_amount = extract_outstanding_amount(driver)
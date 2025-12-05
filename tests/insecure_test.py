import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoAlertPresentException

# ------------------------
# Setup ChromeDriver
# ------------------------
service = Service(r"C:\Users\35389\OneDrive - National College of Ireland\Desktop\ITSupportApp\chromedriver.exe")
driver = webdriver.Chrome(service=service)
driver.maximize_window()

def wait(seconds=2):
    time.sleep(seconds)

def handle_alert():
    """Dismiss alert if present"""
    try:
        alert = driver.switch_to.alert
        print(f"Alert detected: {alert.text}")
        alert.accept()
        wait(1)
    except NoAlertPresentException:
        pass

# ------------------------
# UC-1: Register User
# ------------------------
driver.get("http://127.0.0.1:5000/register")
driver.find_element(By.NAME, "username").send_keys("testuser")
driver.find_element(By.NAME, "password").send_keys("test123")
driver.find_element(By.TAG_NAME, "button").click()
wait(2)
# Check redirected to login page
assert "Login" in driver.page_source or "login" in driver.page_source.lower()
print("UC-1 passed: Register User")


import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import uuid


BASE_URL = "http://127.0.0.1:5000"

DRIVER_PATH = "../chromedriver.exe" 


TEST_USERNAME = f"testuser_{uuid.uuid4().hex[:8]}"
TEST_PASSWORD = "TestPass123!"
TEST_TICKET_TITLE = f"Urgent Issue {uuid.uuid4().hex[:4]}"
TEST_TICKET_DESC = "My computer is displaying a blue screen error after the update."

class SecureAppTests(unittest.TestCase):
    """Functional tests for the secure IT Support Application."""
    
    @classmethod
    def setUpClass(cls):
        """Setup code run once before all test methods."""
       
        service = ChromeService(executable_path=DRIVER_PATH)
        cls.driver = webdriver.Chrome(service=service)
        cls.driver.implicitly_wait(10) 

    @classmethod
    def tearDownClass(cls):
        """Teardown code run once after all test methods."""
        cls.driver.quit()

    def setUp(self):
        """Setup code run before each test method."""
        self.driver.get(BASE_URL)

    # --- TEST 1: Registration and Successful Login ---
    def test_01_register_and_login(self):
        driver = self.driver
        print(f"\n--- Running Test 1: Registering user {TEST_USERNAME} ---")

        # 1. Navigate to Registration
        driver.find_element(By.LINK_TEXT, "Register").click()
        self.assertIn("/register", driver.current_url)

        # 2. Fill and Submit Registration Form
        driver.find_element(By.NAME, "username").send_keys(TEST_USERNAME)
        driver.find_element(By.NAME, "password").send_keys(TEST_PASSWORD)
        driver.find_element(By.TAG_NAME, "button").click()

        # 3. Verify Redirect to Login and Perform Login
        WebDriverWait(driver, 10).until(EC.url_contains("/login"))
        print("Registration successful. Logging in...")

        driver.find_element(By.NAME, "username").send_keys(TEST_USERNAME)
        driver.find_element(By.NAME, "password").send_keys(TEST_PASSWORD)
        driver.find_element(By.TAG_NAME, "button").click()

        # 4. Verify successful redirection to Dashboard
        WebDriverWait(driver, 10).until(EC.url_contains("/dashboard"))
        welcome_text = driver.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Welcome", welcome_text)
        print("Login successful.")

    # --- TEST 2: Create a New Ticket ---
    # This test depends on test_01 creating the user and logging in.
    # It assumes the user created in T1 is still logged in or logs in again.
    def test_02_create_ticket(self):
        # Ensure we are logged in first (re-login for robustness)
        self.driver.get(f"{BASE_URL}/login")
        self.driver.find_element(By.NAME, "username").send_keys(TEST_USERNAME)
        self.driver.find_element(By.NAME, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.TAG_NAME, "button").click()

        driver = self.driver
        WebDriverWait(driver, 10).until(EC.url_contains("/dashboard"))
        print("\n--- Running Test 2: Creating a new ticket ---")

        # 1. Navigate to New Ticket page (using the link text from the dashboard)
        driver.find_element(By.LINK_TEXT, "Submit New Ticket").click() 
        self.assertIn("/ticket/new", driver.current_url)

        # 2. Fill and Submit Ticket Form
        driver.find_element(By.NAME, "title").send_keys(TEST_TICKET_TITLE)
        driver.find_element(By.NAME, "description").send_keys(TEST_TICKET_DESC)
        driver.find_element(By.TAG_NAME, "button").click()

        # 3. Verify Redirection to Tickets List
        WebDriverWait(driver, 10).until(EC.url_contains("/tickets"))
        self.assertIn("/tickets", driver.current_url)
        print("Ticket submission successful. Verifying ticket in list...")

        # 4. Verify the newly created ticket title is present in the list
        # We search for an element containing the specific ticket title text
        ticket_element = driver.find_element(By.XPATH, f"//h5[contains(text(), '{TEST_TICKET_TITLE}')]")
        self.assertIsNotNone(ticket_element, "The new ticket title was not found on the list page.")
        print("Ticket successfully verified on the list.")
        
    # --- TEST 3: Logout Functionality ---
    def test_03_logout(self):
        # Ensure we are logged in first (re-login for robustness)
        self.driver.get(f"{BASE_URL}/login")
        self.driver.find_element(By.NAME, "username").send_keys(TEST_USERNAME)
        self.driver.find_element(By.NAME, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.TAG_NAME, "button").click()
        WebDriverWait(self.driver, 10).until(EC.url_contains("/dashboard"))
        
        driver = self.driver
        print("\n--- Running Test 3: Logout and Access Control Check ---")

        # 1. Click the Logout button/link
        driver.find_element(By.LINK_TEXT, "Logout").click()

        # 2. Verify redirection to the Home page
        WebDriverWait(driver, 10).until(EC.url_to_be(f"{BASE_URL}/"))
        self.assertEqual(f"{BASE_URL}/", driver.current_url)
        print("Logout successful. User is on the index page.")

        # 3. Test access control (try to access dashboard while logged out)
        driver.get(f"{BASE_URL}/dashboard")
        WebDriverWait(driver, 10).until(EC.url_contains("/login")) # Should redirect to login
        self.assertIn("/login", driver.current_url, "Access Control Failed: Did not redirect to login after logout.")
        print("Access control check passed (redirected to login).")


if __name__ == "__main__":
    # Ensure the correct execution order (using unittest default loader)
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
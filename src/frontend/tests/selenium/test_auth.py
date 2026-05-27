# UC-01: Register account, UC-02: Login, UC-16: Logout.
import uuid

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import pytest

BASE_URL = "http://localhost:5173"

CITIZEN_EMAIL    = "citizen@example.com"
CITIZEN_PASSWORD = "Citizen123!"
CITIZEN_USERNAME = "citizen"

OPERATOR_EMAIL    = "operator@example.com"
OPERATOR_PASSWORD = "Operator123!"

ADMIN_EMAIL    = "admin@example.com"
ADMIN_PASSWORD = "Admin123!"

@pytest.fixture
def driver():
    d = webdriver.Chrome()  
    yield d
    d.quit()

@pytest.fixture
def wait(driver):
    return WebDriverWait(driver, 10)


class TestRegister:
    def test_register_account(self, driver, wait):
        unique_id = uuid.uuid4().hex[:8]
        username = f"testuser.{unique_id}"
        email = f"testuser.{unique_id}@example.com"

        
        driver.get(BASE_URL)
        wait.until(EC.element_to_be_clickable((By.ID, "register-link"))).click()
        
        # Enter registration details
        wait.until(EC.visibility_of_element_located((By.ID, "register-username")))
        driver.find_element(By.ID, "register-username").send_keys(username)
        driver.find_element(By.ID, "register-first-name").send_keys("Test")
        driver.find_element(By.ID, "register-last-name").send_keys("User")
        driver.find_element(By.ID, "register-email").send_keys(email)
        driver.find_element(By.ID, "register-password").send_keys(CITIZEN_PASSWORD)

        #submit registration
        driver.find_element(By.ID, "register-submit").click()

        # wait for success message or redirect
        success = wait.until(EC.presence_of_element_located((By.ID, "register-success")))

        assert "verify" in driver.current_url.lower() or "success" in driver.page_source.lower()
        assert ("Account created" in success.text or "Verify" in success.text)
        verification_box = wait.until(EC.presence_of_element_located((By.ID, "verification-box"))) 
        assert verification_box.is_displayed(), ( "Verification link box should be visible after successful registration.")


    def test_register_with_existing_email(self, driver, wait):
        unique_id = uuid.uuid4().hex[:8]

        username = f"testuser.{unique_id}"

        driver.get(BASE_URL)
        wait.until(EC.element_to_be_clickable((By.ID, "register-link"))).click()

        wait.until(EC.presence_of_element_located((By.ID, "register-page")))
        driver.find_element(By.ID, "register-username").send_keys(username)
        driver.find_element(By.ID, "register-first-name").send_keys("Maria")
        driver.find_element(By.ID, "register-last-name").send_keys("Rossi")
        driver.find_element(By.ID, "register-email").send_keys(CITIZEN_EMAIL)
        driver.find_element(By.ID, "register-password").send_keys("TestPass123!")
        driver.find_element(By.ID, "register-submit").click()
 
        error = wait.until(EC.presence_of_element_located((By.ID, "register-error")))
        assert error.text, "An error message should appear when the email is already taken."

    def test_register_with_existing_username(self, driver, wait):
        unique_id = uuid.uuid4().hex[:8]

        email = f"testuser.{unique_id}@example.com"

        driver.get(BASE_URL)
        wait.until(EC.element_to_be_clickable((By.ID, "register-link"))).click()

        wait.until(EC.presence_of_element_located((By.ID, "register-page")))
        driver.find_element(By.ID, "register-username").send_keys(CITIZEN_USERNAME)
        driver.find_element(By.ID, "register-first-name").send_keys("Maria")
        driver.find_element(By.ID, "register-last-name").send_keys("Rossi")
        driver.find_element(By.ID, "register-email").send_keys(email)
        driver.find_element(By.ID, "register-password").send_keys("TestPass123!")
        driver.find_element(By.ID, "register-submit").click()
 
        error = wait.until(EC.presence_of_element_located((By.ID, "register-error")))
        assert error.text, "An error message should appear when the username is already taken."

    def test_register_missing_field(self, driver, wait):
        uid = uuid.uuid4().hex[:8]
 
        driver.get(BASE_URL)
        wait.until(EC.element_to_be_clickable((By.ID, "register-link"))).click()
        
        wait.until(EC.visibility_of_element_located((By.ID, "register-username")))
 
        # leave username empty
        driver.find_element(By.ID, "register-first-name").send_keys("No")
        driver.find_element(By.ID, "register-last-name").send_keys("Name")
        driver.find_element(By.ID, "register-email").send_keys(f"noname_{uid}@example.com")
        driver.find_element(By.ID, "register-password").send_keys("TestPass123!")
        driver.find_element(By.ID, "register-submit").click()
 
        assert "register" in driver.current_url
        assert driver.find_element(By.ID, "register-page").is_displayed()

    def test_verification_link_invalid_shows_error(self, driver, wait):
        uid = uuid.uuid4().hex[:8]
 
        driver.get(BASE_URL)
        wait.until(EC.element_to_be_clickable((By.ID, "register-link"))).click()
        wait.until(EC.visibility_of_element_located((By.ID, "register-username")))
 

        driver.find_element(By.ID, "register-username").send_keys(f"user_{uid}")
        driver.find_element(By.ID, "register-first-name").send_keys("Test")
        driver.find_element(By.ID, "register-last-name").send_keys("User")
        driver.find_element(By.ID, "register-email").send_keys(f"user_{uid}@example.com")
        driver.find_element(By.ID, "register-password").send_keys("TestPass123!")
        driver.find_element(By.ID, "register-submit").click()

        wait.until(EC.presence_of_element_located((By.ID, "register-success")))

        verification_link = driver.find_element(By.ID, "verification-link").get_attribute("href")
        broken_link = verification_link[:-6] + "000000"

        driver.get(broken_link)

        assert "error" in driver.page_source.lower()
        assert "/dashboard" not in driver.current_url




class TestLogin:
#Login with valid credentials
    def test_login_with_valid_credentials(self, driver, wait):

        driver.get(BASE_URL)

        wait.until(EC.element_to_be_clickable((By.ID, "login-link"))).click()
        
        wait.until(EC.visibility_of_element_located((By.ID, "login-identifier")))

        driver.find_element(By.ID, "login-identifier").clear()
        driver.find_element(By.ID, "login-identifier").send_keys(CITIZEN_EMAIL)
        driver.find_element(By.ID, "login-password").clear()
        driver.find_element(By.ID, "login-password").send_keys(CITIZEN_PASSWORD)
        
        driver.find_element(By.ID, "login-submit").click()
        
        wait.until(EC.url_contains("/dashboard"))
        assert "/dashboard" in driver.current_url, ("Citizen should be redirected to /dashboard after successful login.")

    def test_login_with_invalid_credentials(self, driver, wait):
        driver.get(BASE_URL)
        
        wait.until(EC.element_to_be_clickable((By.ID, "login-link"))).click()
        wait.until(EC.visibility_of_element_located((By.ID, "login-identifier")))
        
        driver.find_element(By.ID, "login-identifier").clear()
        driver.find_element(By.ID, "login-identifier").send_keys("invalid@example.com")
        driver.find_element(By.ID, "login-password").clear()
        driver.find_element(By.ID, "login-password").send_keys("WrongPassword123!")
        driver.find_element(By.ID, "login-submit").click()
        
        wait.until(EC.presence_of_element_located((By.ID, "login-error")))
        error_element = driver.find_element(By.ID, "login-error")
        assert error_element.is_displayed()
    
    def test_login_with_unverified_account(self, driver, wait):
        uid = uuid.uuid4().hex[:8]
        username = f"testuser_{uid}"
        email = f"testuser_{uid}@example.com"

        driver.get(f"{BASE_URL}/register")
        wait.until(EC.presence_of_element_located((By.ID, "register-page")))

        driver.find_element(By.ID, "register-username").send_keys(username)
        driver.find_element(By.ID, "register-first-name").send_keys("Test")
        driver.find_element(By.ID, "register-last-name").send_keys("User")
        driver.find_element(By.ID, "register-email").send_keys(email)
        driver.find_element(By.ID, "register-password").send_keys("TestPass123!")
        driver.find_element(By.ID, "register-submit").click()

        # wait for registration to complete 
        wait.until(EC.presence_of_element_located((By.ID, "register-success")))

        driver.get(f"{BASE_URL}/login")
        wait.until(EC.presence_of_element_located((By.ID, "login-page")))

        driver.find_element(By.ID, "login-identifier").clear()
        driver.find_element(By.ID, "login-identifier").send_keys(username)
        driver.find_element(By.ID, "login-password").clear()
        driver.find_element(By.ID, "login-password").send_keys("TestPass123!")
        driver.find_element(By.ID, "login-submit").click()

        error = wait.until(EC.presence_of_element_located((By.ID, "login-error")))
        assert error.is_displayed()
        assert "login" in driver.current_url


class TestLogout:
    def test_logout(self,wait, driver):

        driver.get(BASE_URL)

        wait.until(EC.element_to_be_clickable((By.ID, "login-link"))).click()
        
        wait.until(EC.visibility_of_element_located((By.ID, "login-identifier")))

        driver.find_element(By.ID, "login-identifier").clear()
        driver.find_element(By.ID, "login-identifier").send_keys(CITIZEN_EMAIL)
        driver.find_element(By.ID, "login-password").clear()
        driver.find_element(By.ID, "login-password").send_keys(CITIZEN_PASSWORD)
        
        driver.find_element(By.ID, "login-submit").click()
        wait.until(EC.presence_of_element_located((By.ID, "logout-button")))
        driver.find_element(By.ID, "logout-button").click()
        nav_login = wait.until(EC.presence_of_element_located((By.ID, "nav-login")))
        assert nav_login.is_displayed()  

    def test_logout_blocks_protected_route(self, driver, wait):
        driver.get(BASE_URL)
        wait.until(EC.element_to_be_clickable((By.ID, "login-link"))).click()
        
        wait.until(EC.visibility_of_element_located((By.ID, "login-identifier")))        
        wait.until(EC.presence_of_element_located((By.ID, "login-page")))

        driver.find_element(By.ID, "login-identifier").clear()
        driver.find_element(By.ID, "login-identifier").send_keys(CITIZEN_EMAIL)
        driver.find_element(By.ID, "login-password").clear()
        driver.find_element(By.ID, "login-password").send_keys(CITIZEN_PASSWORD)
        driver.find_element(By.ID, "login-submit").click()
        wait.until(EC.presence_of_element_located((By.ID, "logout-button")))
 
        driver.find_element(By.ID, "logout-button").click()
        wait.until(EC.presence_of_element_located((By.ID, "nav-login")))
 
        driver.get(f"{BASE_URL}/dashboard")
        wait.until(lambda d: "/dashboard" not in d.current_url or "login" in d.current_url)
        assert "/dashboard" not in driver.current_url or "login" in driver.current_url
        
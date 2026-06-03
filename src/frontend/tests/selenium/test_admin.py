# UC-13 View private statistics

# UC-14 Manage categories and configuration

import time

from selenium import webdriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import pytest

BASE_URL = "http://localhost:5173"
SEED_TITLE = "Pothole on Via Roma"
SEED_CATEGORY = "Roads and Urban Furniture"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Admin123!"
CITIZEN_EMAIL = "citizen@example.com"
CITIZEN_PASSWORD = "Citizen123!"


@pytest.fixture
def driver():
    d = webdriver.Chrome()
    yield d
    d.quit()

@pytest.fixture
def wait(driver):
    return WebDriverWait(driver, 200)


def login(driver, wait, email: str, password: str) -> None:
    driver.get(BASE_URL)
    wait.until(EC.element_to_be_clickable((By.ID, "login-link"))).click()
    wait.until(EC.visibility_of_element_located((By.ID, "login-identifier")))
    wait.until(EC.visibility_of_element_located((By.ID, "login-password")))
    driver.find_element(By.ID, "login-identifier").clear()
    driver.find_element(By.ID, "login-identifier").send_keys(email)
    driver.find_element(By.ID, "login-password").clear()
    driver.find_element(By.ID, "login-password").send_keys(password)
    driver.find_element(By.ID, "login-submit").click()

# At times, despite being logged as Admin, the frontend still reports that authentication is required, which leads to a failure by assertion.
# Another problem could be -unable to load admin data -

# UC-13: View private statistics 

class TestViewPrivateStatistics:

    def test_admin_sees_private_statistics(self, driver, wait):
        login(driver, wait, ADMIN_EMAIL, ADMIN_PASSWORD)
        wait.until(EC.url_changes(f"{BASE_URL}/admin"))
        wait.until(lambda d: d.get_cookie("session") is not None)

        wait.until(lambda d: len(d.find_elements(By.XPATH, "//*[starts-with(@id,'admin-metric')]")) > 0)
        
        assert driver.find_element(By.XPATH, "//*[starts-with(@id, 'admin-metric')]").is_displayed()


    def test_citizen_cannot_access_private_statistics(self, driver, wait):
        login(driver, wait, CITIZEN_EMAIL, CITIZEN_PASSWORD)
        wait.until(EC.url_changes(f"{BASE_URL}/login"))

        assert "admin" not in driver.current_url


# UC-14: Manage categories and configuration 

class TestManageCategories:

    def test_admin_can_create_category(self, driver, wait):
        login(driver, wait, ADMIN_EMAIL, ADMIN_PASSWORD)
        wait.until(EC.url_changes(f"{BASE_URL}/admin"))
        wait.until(EC.url_contains("/admin"))

        wait.until(lambda d: d.get_cookie("session") is not None)

        wait.until(EC.presence_of_element_located((By.ID, "admin-create-category-card")))

        unique_name = f"Test Category {int(time.time())}"
        wait.until(EC.presence_of_element_located((By.ID, "admin-new-category-name")))
        driver.find_element(By.ID, "admin-new-category-name").send_keys(unique_name)
        driver.find_element(By.ID, "admin-new-category-submit").click()

        success = wait.until(EC.presence_of_element_located((By.ID, "admin-success")))
        assert success.is_displayed()
        assert "category created." in success.text.lower()


    #category name already exists 
    def test_admin_duplicate_category_shows_error(self, driver, wait):
        login(driver, wait, ADMIN_EMAIL, ADMIN_PASSWORD)
        wait.until(EC.url_changes(f"{BASE_URL}/admin"))
        wait.until(EC.url_contains("/admin"))

        wait.until(lambda d: d.get_cookie("session") is not None)


        wait.until(EC.presence_of_element_located((By.ID, "admin-create-category-card")))

        driver.find_element(By.ID, "admin-new-category-name").clear()
        driver.find_element(By.ID, "admin-new-category-name").send_keys(SEED_CATEGORY)
        driver.find_element(By.ID, "admin-new-category-submit").click()
        #twice because sometimes the error message disappears and the assertion fails
        driver.find_element(By.ID, "admin-new-category-submit").click()

        wait.until(EC.presence_of_element_located((By.ID, "admin-error")))
        error = driver.find_element(By.ID, "admin-error")

        assert error.is_displayed()
     


    def test_admin_can_toggle_category_and_change_persists(self, driver, wait):
        login(driver, wait, ADMIN_EMAIL, ADMIN_PASSWORD)
        wait.until(EC.url_changes(f"{BASE_URL}/admin"))
        wait.until(EC.url_contains("/admin"))

        wait.until(EC.presence_of_element_located((By.ID, "admin-categories-header-active")))


        wait.until(lambda d: len(d.find_elements(By.XPATH,"//*[starts-with(@id, 'admin-category-name-')]")) > 0)

        first_row = driver.find_elements(By.XPATH,"//*[starts-with(@id, 'admin-category-name-')]")[0]

        category_id = first_row.get_attribute("id").split("-")[-1]

        checkbox = driver.find_element(By.ID,f"admin-category-active-{category_id}")

        initial_state = checkbox.is_selected()

        checkbox.click()

        wait.until(lambda d: d.find_element(By.ID, f"admin-category-active-{category_id}").is_selected() != initial_state)

        driver.find_element(By.ID,f"admin-category-save-{category_id}").click()

        wait.until(EC.presence_of_element_located((By.ID, "admin-success")))

        driver.refresh()

        wait.until(EC.url_contains("/admin"))
        wait.until(EC.visibility_of_element_located((By.ID, "admin-create-category-card")))

        checkbox = wait.until(EC.presence_of_element_located((By.ID, f"admin-category-active-{category_id}")))

        assert checkbox.is_selected() != initial_state

        # cleanup
        checkbox.click()

        driver.find_element(By.ID,f"admin-category-save-{category_id}").click()

        wait.until(EC.presence_of_element_located((By.ID, "admin-success")))


    def test_saved_category_name_persists_after_reload(self, driver, wait):
        login(driver, wait, ADMIN_EMAIL, ADMIN_PASSWORD)
        wait.until(EC.url_changes(f"{BASE_URL}/admin"))
        wait.until(EC.url_contains("/admin"))
        wait.until(lambda d: d.get_cookie("session") is not None)

        wait.until(EC.presence_of_element_located((By.ID, "admin-categories-header-active")))

        wait.until(EC.presence_of_element_located((By.ID, "admin-create-category-card")))  
        wait.until(lambda d: len(d.find_elements(By.XPATH, "//*[starts-with(@id, 'admin-category-name-')]")) > 0)

        first_row = driver.find_elements(By.XPATH, "//*[starts-with(@id, 'admin-category-name-')]")[0]
        category_id = first_row.get_attribute("id").split("-")[-1]

        unique_name = f"Renamed {int(time.time())}"
        name_input = driver.find_element(By.ID, f"admin-category-name-{category_id}")  
        name_input.clear()
        name_input.send_keys(unique_name)

        save_btn = wait.until(EC.element_to_be_clickable((By.ID, f"admin-category-save-{category_id}")))
        save_btn.click()

        # wait for success notification
        success = wait.until(EC.presence_of_element_located((By.ID, "admin-success"))) 
        assert "updated" in success.text.lower()

        # reload and verify
        driver.refresh()
        wait.until(EC.presence_of_element_located((By.ID, "admin-create-category-card")))  
        wait.until(lambda d: len( d.find_elements(By.XPATH, "//*[starts-with(@id, 'admin-category-name-')]")) > 0)

        saved_input = driver.find_element(By.ID, f"admin-category-name-{category_id}")  
        assert saved_input.get_attribute("value") == unique_name


    def test_saved_user_role_persists_after_reload(self, driver, wait):
        login(driver, wait, ADMIN_EMAIL, ADMIN_PASSWORD)
        wait.until(EC.url_changes(f"{BASE_URL}/admin"))
        wait.until(EC.url_contains("/admin"))
        wait.until(lambda d: d.get_cookie("session") is not None)

        wait.until(EC.presence_of_element_located((By.ID, "admin-categories-header-active")))

        wait.until(EC.presence_of_element_located((By.ID, "admin-create-category-card")))  
        wait.until(lambda d: len(d.find_elements(By.XPATH, "//*[starts-with(@id, 'admin-user-save-')]")) > 0)

        first_save = driver.find_elements(By.XPATH, "//*[starts-with(@id, 'admin-user-save-')]")[0]

        user_id = first_save.get_attribute("id").split("-")[-1]

        # toggle active checkbox
        active_cb = driver.find_element(By.ID, f"admin-user-status-{user_id}")  
        initial_state = active_cb.is_selected()
        active_cb.click()

        save_btn = wait.until(EC.element_to_be_clickable((By.ID, f"admin-user-save-{user_id}")))
        save_btn.click()

        wait.until(EC.presence_of_element_located((By.ID, "admin-success")))  

        driver.refresh()
        wait.until(EC.presence_of_element_located((By.ID, "admin-create-category-card")))  
        wait.until(lambda d: len(d.find_elements(By.XPATH, "//*[starts-with(@id, 'admin-user-save-')]")) > 0)

        active_cb = driver.find_element(By.ID, f"admin-user-status-{user_id}")  
        assert active_cb.is_selected() != initial_state

        # restore
        active_cb.click()
        driver.find_element(By.ID, f"admin-user-save-{user_id}").click()  
        wait.until(EC.presence_of_element_located((By.ID, "admin-success")))  




    def test_admin_can_create_user(self, driver, wait):
        login(driver, wait, ADMIN_EMAIL, ADMIN_PASSWORD)
        wait.until(EC.url_changes(f"{BASE_URL}/admin"))
        wait.until(EC.url_contains("/admin"))
        wait.until(lambda d: d.get_cookie("session") is not None)

        wait.until(EC.presence_of_element_located((By.ID, "admin-categories-header-active")))
    
        unique = int(time.time())

        username = f"testuser{unique}"
        email = f"testuser{unique}@example.com"

        driver.find_element(By.ID,"admin-new-user-username").send_keys(username)
        driver.find_element(By.ID,"admin-new-user-email").send_keys(email)
        driver.find_element(By.ID,"admin-new-user-first-name").send_keys("Test")
        driver.find_element(By.ID,"admin-new-user-last-name").send_keys("User")

        driver.find_element(By.ID,"admin-new-user-password").send_keys("Password123!")
        Select(driver.find_element(By.ID,"admin-new-user-role")).select_by_visible_text("citizen")

        driver.find_element(By.ID,"admin-new-user-submit").click()

        success = wait.until(EC.presence_of_element_located((By.ID, "admin-success"))) 
        assert "created" in success.text.lower()


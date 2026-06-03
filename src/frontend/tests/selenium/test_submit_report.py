# UC-03 Submit report


import os
import time
import tempfile
import base64
import uuid

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

BASE_URL          = "http://localhost:5173"
SEED_CATEGORY     = "Roads and Urban Furniture"

# Demo accounts
CITIZEN_EMAIL     = "citizen@example.com"
CITIZEN_PASSWORD  = "Citizen123!"
OPERATOR_EMAIL    = "operator@example.com"
OPERATOR_PASSWORD = "Operator123!"
ADMIN_EMAIL       = "admin@example.com"
ADMIN_PASSWORD    = "Admin123!"


@pytest.fixture
def driver():
    d = webdriver.Chrome()
    yield d
    d.quit()

@pytest.fixture
def wait(driver):
    return WebDriverWait(driver, 10)


@pytest.fixture
def dummy_images():
    temp_files = []
    for i in range(4):
        fd, path = tempfile.mkstemp(suffix=".jpg")
        with os.fdopen(fd, 'wb') as f:
            f.write(b"\x00")
        temp_files.append(path)

    yield temp_files

    for path in temp_files:
        try:
            os.remove(path)
        except OSError:
            pass

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
    wait.until(EC.url_contains("/dashboard"))


def login_as_citizen(driver, wait) -> None:
    login(driver, wait, CITIZEN_EMAIL, CITIZEN_PASSWORD)
    wait.until(EC.url_contains("/dashboard"))

def make_temp_image(suffix=".png") -> str:
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(_ONE_PIXEL_PNG)
    tmp.flush()
    tmp.close()
    return tmp.name


# A tiny valid 1x1 PNG, decoded at runtime (avoids Pillow dependency)
_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Zr2QAAAAASUVORK5CYII="
)

class TestSubmitReport:

    def test_submit_report_success(self, driver, wait):
        unique_id = uuid.uuid4().hex[:8]

        login_as_citizen(driver, wait)
        wait.until(EC.presence_of_element_located((By.ID, "nav-new-report"))).click()
        wait.until(EC.presence_of_element_located((By.ID, "report-title")))

        title = f"Report title - {unique_id}"
        driver.find_element(By.ID, "report-title").send_keys(title)
        driver.find_element(By.ID, "report-description").send_keys(f"Report description. ")
        category = Select(driver.find_element(By.ID, "report-category")).select_by_visible_text("Public Lighting")
        driver.find_element(By.ID, "report-longitude").send_keys("45.12")

        latitude_field = driver.find_element(By.ID, "report-latitude")
        latitude_field.clear()
        latitude_field.send_keys("45.12")

        longitude_field = driver.find_element(By.ID, "report-longitude")
        longitude_field.clear()
        longitude_field.send_keys("9.34") 

        photo_input = driver.find_element(By.ID, "report-photos")
        photo_input.send_keys( make_temp_image() )
        
        driver.find_element(By.ID, "new-report-submit").click()


        status_element = wait.until(EC.visibility_of_element_located((By.ID, "report-detail-status")))
        assert "Status: Pending Approval" in status_element.text

        title_element = driver.find_element(By.ID, "report-detail-title")
        assert title_element.text == title

        reporter_element = driver.find_element(By.ID, "report-detail-reporter-value")
        assert reporter_element.text == "Marco Citizen"

        reporter_element = driver.find_element(By.ID, "report-detail-reporter-value")
        assert reporter_element.text == "Marco Citizen"


    def test_missing_data(self, driver, wait):
        unique_id = uuid.uuid4().hex[:8]

        login_as_citizen(driver, wait)
        wait.until(EC.presence_of_element_located((By.ID, "nav-new-report"))).click()
        wait.until(EC.presence_of_element_located((By.ID, "report-title")))

        driver.find_element(By.ID, "new-report-submit").click()

        assert driver.find_elements(By.ID, "new-report-title")

        title_input = driver.find_element(By.ID, "report-title")
        is_valid = driver.execute_script("return arguments[0].checkValidity();", title_input)
        assert is_valid is False
    

    def test_submit_more_than_three_photos(self, driver, wait):
        unique_id = uuid.uuid4().hex[:8]

        login_as_citizen(driver, wait)
        wait.until(EC.presence_of_element_located((By.ID, "nav-new-report"))).click()
        wait.until(EC.presence_of_element_located((By.ID, "report-title")))

        title = f"Report title - {unique_id}"
        driver.find_element(By.ID, "report-title").send_keys(title)
        driver.find_element(By.ID, "report-description").send_keys(f"Report description. ")
        category = Select(driver.find_element(By.ID, "report-category")).select_by_visible_text("Public Lighting")
        driver.find_element(By.ID, "report-longitude").send_keys("45.12")

        latitude_field = driver.find_element(By.ID, "report-latitude")
        latitude_field.clear()
        latitude_field.send_keys("45.12")

        longitude_field = driver.find_element(By.ID, "report-longitude")
        longitude_field.clear()
        longitude_field.send_keys("9.34") 

        photo_input = driver.find_element(By.ID, "report-photos")
        photo_input.send_keys( make_temp_image() )

        photo_input = driver.find_element(By.ID, "report-photos")
        photo_input.send_keys( make_temp_image() )

        photo_input = driver.find_element(By.ID, "report-photos")
        photo_input.send_keys( make_temp_image() )

        photo_input = driver.find_element(By.ID, "report-photos")
        photo_input.send_keys( make_temp_image() )
        
        photo_input = driver.find_element(By.ID, "report-photos")
        photo_input.send_keys( make_temp_image() )
        
        driver.find_element(By.ID, "new-report-submit").click()


        error_element = wait.until(EC.visibility_of_element_located((By.ID, "new-report-error")))

        expected_message = "A report can contain at most 3 photos. Only the first 3 have been selected."
        assert error_element.text == expected_message, f"Testo errore non corrispondente! Trovato: '{error_element.text}'"


    def test_submit_zero_photos(self, driver, wait):
        unique_id = uuid.uuid4().hex[:8]

        login_as_citizen(driver, wait)
        wait.until(EC.presence_of_element_located((By.ID, "nav-new-report"))).click()
        wait.until(EC.presence_of_element_located((By.ID, "report-title")))

        title = f"Report title - {unique_id}"
        driver.find_element(By.ID, "report-title").send_keys(title)
        driver.find_element(By.ID, "report-description").send_keys(f"Report description. ")
        category = Select(driver.find_element(By.ID, "report-category")).select_by_visible_text("Public Lighting")
        driver.find_element(By.ID, "report-longitude").send_keys("45.12")

        latitude_field = driver.find_element(By.ID, "report-latitude")
        latitude_field.clear()
        latitude_field.send_keys("45.12")

        longitude_field = driver.find_element(By.ID, "report-longitude")
        longitude_field.clear()
        longitude_field.send_keys("9.34") 


        driver.find_element(By.ID, "new-report-submit").click()
        assert len(driver.find_elements(By.ID, "new-report-title")) > 0

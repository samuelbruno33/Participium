# UC-11 Send Message to user
# UC-12 Reply to operator message


from __future__ import annotations

import tempfile
import time

import pytest
from requests import options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

BASE_URL = "http://localhost:5173"
SEED_TITLE = "Pothole on Via Roma"
SEED_CATEGORY = "Roads and Urban Furniture"



@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-save-password-bubble")
    options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
    })
    d = webdriver.Chrome(options=options)
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

    wait.until(EC.url_changes(f"{BASE_URL}/login"))


def logout(driver, wait) -> None:
    driver.get(f"{BASE_URL}/logout")
    wait.until(EC.presence_of_element_located((By.ID, "public-filter-form")))




# UC-11: Send message to citizen 
class TestSendMessageToCitizen:

    def test_operator_can_send_message(self, driver, wait):
        login(driver, wait, "operator@example.com", "Operator123!")
        
        driver.get(f"{BASE_URL}/operator")
        wait.until(EC.presence_of_element_located((By.ID, "operator-summary-section")))

        assigned_rows = wait.until(
            lambda d: d.find_elements(By.XPATH, "//*[contains(@id, 'assigned-report-row-')]")
        )
        if not assigned_rows:
            pytest.skip("No assigned reports available for operator")

        report_id = assigned_rows[0].get_attribute("id").split("-")[-1]
        link = wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//*[@id='assigned-report-row-{report_id}']//*[contains(@id,'-open-detail')]")
        ))
        link.click()
        wait.until(EC.presence_of_element_located((By.ID, "messages-card")))

        msg_input = wait.until(EC.presence_of_element_located((By.ID, "report-message-body")))
        msg_input.send_keys("Operator message UC-11")
        driver.find_element(By.ID, "report-message-submit").click()

        wait.until(lambda d: any("Operator message UC-11" in el.text
            for el in d.find_elements(By.XPATH, "//*[contains(@id, 'message-item')]")
        ))




        

# UC-12: Reply to operator message (citizen) 
class TestReplyToOperator:

    def test_citizen_reply_to_operator_message(self, driver, wait):
        login(driver, wait, "citizen@example.com", "Citizen123!")

        driver.get(f"{BASE_URL}/dashboard")
        wait.until(EC.presence_of_element_located((By.ID, "my-reports-card")))

        report_rows = wait.until(lambda d: d.find_elements(By.XPATH, "//*[starts-with(@id, 'my-report-row-')]"))

        if not report_rows:
            pytest.skip("No citizen reports available")

        report_id = report_rows[0].get_attribute("id").split("-")[-1]

        open_btn = wait.until(EC.element_to_be_clickable((By.XPATH, f"//*[@id='my-report-row-{report_id}']//*[contains(@id,'-open-')]")))
        
        driver.execute_script("arguments[0].click();", open_btn)

        wait.until(EC.presence_of_element_located((By.ID, "report-detail-page")))

        reply_input = wait.until(EC.presence_of_element_located((By.ID, "report-message-body")))

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reply_input)

        test_reply = "Citizen reply UC-12"
        reply_input.send_keys(test_reply)

        submit_btn = wait.until(EC.element_to_be_clickable((By.ID, "report-message-submit")))
        submit_btn.click()

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{test_reply}')]"))
    )







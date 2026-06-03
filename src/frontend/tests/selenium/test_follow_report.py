# UC-07 Follow report

from __future__ import annotations

import time
import requests
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.action_chains import ActionChains


BASE_URL = "http://localhost:5173"
API_URL = "http://localhost:5050/api/v1"

TEST_USER = {
    "identifier": "citizen@example.com",
    "password": "Citizen123!"
}

@pytest.fixture
def followable_report():
    session = requests.Session()

    resp = session.post(f"{API_URL}/auth/login", json=TEST_USER)
    assert resp.status_code == 200, f"API Login Failed: {resp.text}"

    resp = session.get(f"{API_URL}/reports")
    assert resp.status_code == 200, f"Report recovery failed: {resp.text}"
    data = resp.json()
    reports = data if isinstance(data, list) else data.get("reports") or data.get("items") or []
    assert len(reports) > 0, "No report was found in the DB."

    yield reports[0]["id"]

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    d = webdriver.Chrome(options=options)
    d.maximize_window()
    yield d
    d.quit()


def human_click(driver, element):
    """Two closeby clicks: the first one activates the component, the second one triggers the action."""
    ActionChains(driver).move_to_element(element).click().pause(0.1).click().perform()

@pytest.mark.implementation_bug(reason="Sometimes it asks for the login despite it having been just made.")
def helper_login_as_test_citizen(driver, wait):
    driver.get(f"{BASE_URL}/login")
    wait.until(EC.presence_of_element_located((By.ID, "login-page")))

    identifier_field = driver.find_element(By.ID, "login-identifier")
    password_field = driver.find_element(By.ID, "login-password")

    identifier_field.clear()
    identifier_field.send_keys(TEST_USER["identifier"])

    password_field.clear()
    password_field.send_keys(TEST_USER["password"])

    human_click(driver, driver.find_element(By.ID, "login-submit"))
    wait.until(EC.presence_of_element_located((By.ID, "dashboard-page")))

@pytest.mark.implementation_bug(reason="Sometimes the button to follow or stop following a report doesn't appear.")
def test_uc07_main_scenario_and_3a_follow_unfollow(driver, followable_report):
    wait = WebDriverWait(driver, 10)
    helper_login_as_test_citizen(driver, wait)

    driver.get(f"{BASE_URL}/reports/{followable_report}")
    wait.until(EC.presence_of_element_located((By.ID, "report-detail-page")))

    try:
        follow_button = wait.until(EC.element_to_be_clickable((By.ID, "follow-button")))
    except TimeoutException:
        pytest.fail("The 'Follow' button didn't appear in the report's page.")

    initial_text = follow_button.text.strip()

    human_click(driver, follow_button)

    try:
        wait.until(lambda d: d.find_element(By.ID, "follow-button").text.strip() != initial_text)
    except TimeoutException:
        errors = driver.find_elements(By.ID, "report-detail-error")
        err_msg = errors[0].text.strip() if errors and errors[0].is_displayed() else "The button didn't react."
        pytest.fail(f"Follow failed: {err_msg}")

    new_text = driver.find_element(By.ID, "follow-button").text.strip()
    assert new_text in ["Follow report", "Unfollow report"], f"Unexpected button test: '{new_text}'"

    # Extension 3a: Unfollow to restore the state
    follow_button = wait.until(EC.element_to_be_clickable((By.ID, "follow-button")))
    human_click(driver, follow_button)
    wait.until(lambda d: d.find_element(By.ID, "follow-button").text.strip() == initial_text)


def test_uc07_extension_3b_unauthenticated_cannot_follow(driver, followable_report):
    wait = WebDriverWait(driver, 10)

    driver.get(f"{BASE_URL}/reports/{followable_report}")
    wait.until(EC.presence_of_element_located((By.ID, "report-detail-page")))

    buttons = driver.find_elements(By.ID, "follow-button")
    assert len(buttons) == 0, "The Follow button mustn't be visibile to unauthenticated visitors."